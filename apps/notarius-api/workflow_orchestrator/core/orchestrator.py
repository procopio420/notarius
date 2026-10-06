"""
Core orchestration logic.

Determines complete workflow plan for documents based on type, specialty, UF, and metadata.
"""

import logging
from typing import List

from django.conf import settings

from workflow_orchestrator.models.contracts import (
    WorkflowInput,
    WorkflowPlan,
    Destino,
    Assinatura,
    DocumentoBasico,
)
from workflow_orchestrator.core.rulepack_loader import get_rulepack_for_document
from workflow_orchestrator.utils.pii import generate_cache_key, redact_pii_in_logs

logger = logging.getLogger(__name__)


def normalize_slug(value: str) -> str:
    """Normalize string to slug format."""
    return value.lower().strip().replace(" ", "_").replace("-", "_")


def _prefer_presencial(canais: List[str]) -> str:
    """Return presencial if available otherwise fallback to online."""
    if "presencial" in canais:
        return "presencial"
    if "online" in canais:
        return "online"
    return "presencial"


def _append_unique(items: List[str], value: str):
    """Append value to list if not already present."""
    if value and value not in items:
        items.append(value)


def determine_roteamento(
    especialidade: str,
    preferencia_online: bool,
    canais_disponiveis: List[str]
) -> Destino:
    """
    Determine routing destination based on specialty.
    
    Args:
        especialidade: Document specialty
        preferencia_online: User preference for online
        canais_disponiveis: Available channels
        
    Returns:
        Destino object
    """
    especialidade_norm = normalize_slug(especialidade)
    canais = [normalize_slug(c) for c in canais_disponiveis]
    has_online = "online" in canais
    has_presencial = "presencial" in canais
    
    # Default authority names
    autorities = {
        "tabelionato_notas": "Tabelionato de Notas",
        "rcpn": "Registro Civil de Pessoas Naturais",
        "registro_imoveis": "Registro de Imóveis competente",
        "rtd": "Registro de Títulos e Documentos",
        "rcpj": "Registro Civil de Pessoas Jurídicas",
        "protesto": "Tabelionato de Protesto",
    }
    
    # tabelionato_notas → e-notariado if enabled and online preferred/available
    if especialidade_norm == "tabelionato_notas":
        enot_enabled = getattr(settings, "ENABLE_ENOTARIADO", True)
        if enot_enabled and has_online and (preferencia_online or not has_presencial):
            modo = "hibrido" if has_presencial else "online"
            return Destino(
                autoridade=autorities["tabelionato_notas"],
                plataforma="e-notariado",
                modo=modo,
            )
        # fallback to presencial/manual flow
        fallback_modo = "presencial" if has_presencial else ("online" if has_online else "presencial")
        return Destino(
            autoridade=autorities["tabelionato_notas"],
            plataforma=None,
            modo=fallback_modo,
        )
    
    if especialidade_norm == "rcpn":
        return Destino(
            autoridade=autorities["rcpn"],
            plataforma=None,
            modo="presencial",
        )
    
    if especialidade_norm == "registro_imoveis":
        ri_enabled = getattr(settings, "ENABLE_RI_CENTRAL", True)
        if ri_enabled and has_online and (preferencia_online or not has_presencial):
            return Destino(
                autoridade=autorities["registro_imoveis"],
                plataforma="registrodeimoveis.org.br",
                modo="online",
            )
        return Destino(
            autoridade=autorities["registro_imoveis"],
            plataforma=None,
            modo=_prefer_presencial(canais),
        )
    
    if especialidade_norm in {"rtd", "rcpj"}:
        rtd_enabled = getattr(settings, "ENABLE_RTDPJ_CENTRAL", True)
        if rtd_enabled and has_online and (preferencia_online or not has_presencial):
            return Destino(
                autoridade=autorities[especialidade_norm],
                plataforma="rtdbrasil.org.br",
                modo="online",
            )
        return Destino(
            autoridade=autorities[especialidade_norm],
            plataforma=None,
            modo=_prefer_presencial(canais),
        )
    
    if especialidade_norm == "protesto":
        protesto_enabled = getattr(settings, "ENABLE_PROTESTO_CENTRAL", True)
        if protesto_enabled and has_online and (preferencia_online or not has_presencial):
            return Destino(
                autoridade=autorities["protesto"],
                plataforma="protesto.com.br",
                modo="online",
            )
        return Destino(
            autoridade=autorities["protesto"],
            plataforma=None,
            modo=_prefer_presencial(canais),
        )
    
    # Default fallback
    return Destino(
        autoridade="Cartório competente",
        plataforma=None,
        modo=_prefer_presencial(canais),
    )


def determine_assinatura(
    doc: DocumentoBasico,
    rule: dict,
    assinatura_disponivel: List[str],
    preferencia_online: bool
) -> Assinatura:
    """
    Determine signature requirements.
    
    Args:
        doc: Document information
        rule: Rulepack rule for this document
        assinatura_disponivel: Available signature types
        preferencia_online: User preference for online
        
    Returns:
        Assinatura object
    """
    # Get quem_assina from rulepack
    quem_assina = rule.get("quem_assina", [])
    
    # If rule doesn't specify quem_assina, try to derive from partes
    if not quem_assina:
        # Preserve original order while ensuring uniqueness
        partes_roles: List[str] = []
        for parte in doc.partes:
            if parte.papel not in partes_roles:
                partes_roles.append(parte.papel)
        quem_assina = partes_roles
        
        # Add tabeliao for tabelionato_notas if not already present
        especialidade_norm_local = normalize_slug(doc.especialidade)
        if especialidade_norm_local == "tabelionato_notas" and "tabeliao" not in quem_assina:
            quem_assina.append("tabeliao")
    
    # Determine signature type
    especialidade_norm = normalize_slug(doc.especialidade)
    enot_enabled = getattr(settings, "ENABLE_ENOTARIADO", True)
    
    preferred_types: List[str] = []
    preferred_from_rule = rule.get("assinatura_tipo")
    if preferred_from_rule in assinatura_disponivel:
        _append_unique(preferred_types, preferred_from_rule)
    
    if especialidade_norm == "tabelionato_notas":
        if enot_enabled and "e-notariado" in assinatura_disponivel:
            _append_unique(preferred_types, "e-notariado")
        if "icp_brasil" in assinatura_disponivel:
            _append_unique(preferred_types, "icp_brasil")
        if "manual" in assinatura_disponivel:
            _append_unique(preferred_types, "manual")
    else:
        if "icp_brasil" in assinatura_disponivel:
            _append_unique(preferred_types, "icp_brasil")
        if enot_enabled and "e-notariado" in assinatura_disponivel:
            _append_unique(preferred_types, "e-notariado")
        if "manual" in assinatura_disponivel:
            _append_unique(preferred_types, "manual")
    
    if not preferred_types:
        tipo = assinatura_disponivel[0] if assinatura_disponivel else "manual"
    else:
        tipo = preferred_types[0]
    
    # Determine videoconferencia
    videoconferencia = (
        preferencia_online and
        tipo in ["e-notariado", "icp_brasil"] and
        especialidade_norm == "tabelionato_notas"
    )
    
    return Assinatura(
        quem_assina=quem_assina,
        tipo=tipo,
        videoconferencia=videoconferencia
    )


def build_checklist(rule: dict, anexos: List[str]) -> List[str]:
    """
    Build checklist from rulepack and anexos.
    
    Args:
        rule: Rulepack rule
        anexos: Attachments provided
        
    Returns:
        List of checklist items
    """
    checklist = rule.get("checklist", []).copy()
    
    # Add anexo-specific items
    anexo_map = {
        "itbi": "ITBI",
        "habite_se": "Habite-se/ART-RRT",
        "art_rrt": "ART-RRT",
        "dnv": "DNV",
    }
    
    for anexo in anexos:
        anexo_norm = normalize_slug(anexo)
        if anexo_norm in anexo_map and anexo_map[anexo_norm] not in checklist:
            checklist.append(anexo_map[anexo_norm])
    
    return checklist


def plan_from_input(input_data: WorkflowInput) -> WorkflowPlan:
    """
    Generate workflow plan from input.
    
    Args:
        input_data: WorkflowInput with document and preferences
        
    Returns:
        WorkflowPlan with complete workflow information
    """
    doc = input_data.doc
    
    # Normalize slugs
    especialidade_norm = normalize_slug(doc.especialidade)
    tipo_documento_norm = normalize_slug(doc.tipo_documento)
    
    # Load rulepack
    rule = get_rulepack_for_document(especialidade_norm, tipo_documento_norm, doc.uf)
    
    # Log (with PII redaction)
    log_data = {
        "especialidade": especialidade_norm,
        "tipo_documento": tipo_documento_norm,
        "uf": doc.uf,
    }
    logger.info(f"Generating workflow plan: {redact_pii_in_logs(log_data)}")
    
    # Determine roteamento
    roteamento = determine_roteamento(
        especialidade_norm,
        input_data.preferencia_online,
        input_data.canais_disponiveis
    )
    
    # Determine assinatura
    assinatura = determine_assinatura(
        doc,
        rule,
        input_data.assinatura_disponivel,
        input_data.preferencia_online
    )
    
    # Build checklist
    checklist = build_checklist(rule, input_data.anexos)
    
    # Extract citacoes
    citacoes = rule.get("citacoes", [])
    
    # Extract bloqueantes and alerta
    bloqueantes = rule.get("bloqueantes", [])
    alerta = rule.get("alerta", [])
    
    # Extract fees_hint
    fees_hint = rule.get("fees_hint", [])
    
    # Generate cache key
    cache_key = generate_cache_key(doc, input_data.anexos)
    
    # Build protocolo instructions
    protocolo = {
        "canal_principal": roteamento.modo,
        "plataforma": roteamento.plataforma,
        "instrucoes": f"Enviar para {roteamento.autoridade}" + (
            f" via {roteamento.plataforma}" if roteamento.plataforma else ""
        )
    }
    
    return WorkflowPlan(
        roteamento=roteamento,
        assinatura=assinatura,
        protocolo=protocolo,
        checklist=checklist,
        citacoes=citacoes,
        bloqueantes=bloqueantes,
        alerta=alerta,
        fees_hint=fees_hint,
        cache_key=cache_key
    )

