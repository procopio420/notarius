"""
AI-powered document generation service for Notarius.

This service delegates AI operations to the appropriate microservices
instead of making direct OpenAI calls, ensuring proper routing and cost management.
"""

import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.auditoria.models import AuditLog
from .models import AIGeneratedMinuta
from apps.documentos.models import Minuta
from apps.templates.models import DocumentTemplate, Template
from apps.analytics.models import AIUsageAnalytics


class AIDocumentService:
    """
    Core AI service for natural language document generation.
    
    This service:
    1. Parses natural language commands into structured data
    2. Selects appropriate templates and clauses
    3. Generates documents without hallucination
    4. Tracks all generations for audit and learning
    """

    def __init__(self):
        self.intent_client = IntentEngineClient()
        self.lexnode_client = LexNodeClient()
        
        # OpenAI client will be created per request with API key
        
    async def parse_command(self, command: str, tenant_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse natural language command into structured data using intent-engine microservice.
        
        Args:
            command: Natural language input like "Fazer procuração pública de João Silva para Maria Oliveira"
            tenant_context: Tenant-specific context (notary info, etc.)
            
        Returns:
            Dict with parsed intent, confidence, and extracted entities
        """
        start_time = time.time()
        
        try:
            # Use intent-engine microservice for AI-powered parsing
            tenant_id = tenant_context.get('tenant_id')
            user_id = tenant_context.get('user_id')
            
            if not tenant_id:
                raise ValueError("tenant_id is required in tenant_context")
            
            # Call intent-engine microservice
            result = await self.intent_client.parse_intent(
                intent=command,
                processo_id=None,  # Not available at parsing stage
                tenant_id=UUID(tenant_id),
                user_id=UUID(user_id) if user_id else None
            )
            
            generation_time = int((time.time() - start_time) * 1000)
            
            return {
                "parsed_intent": result.get("parsed_intent", {}),
                "confidence": result.get("confidence", 0.0),
                "generation_time_ms": generation_time,
                "model_version": "intent-engine",
                "timestamp": timezone.now().isoformat(),
                "intent_id": result.get("intent_id"),
                "suggestions": result.get("suggestions", [])
            }
            
        except Exception as e:
            # Fall back to rule-based parsing if microservice fails
            print(f"Intent-engine parsing failed, falling back to rule-based: {e}")
            parsed_data = self._rule_based_parsing(command)
            confidence = self._calculate_confidence(command, parsed_data)
            
            generation_time = int((time.time() - start_time) * 1000)
            
            return {
                "parsed_intent": parsed_data,
                "confidence": confidence,
                "generation_time_ms": generation_time,
                "model_version": "rule-based-fallback",
                "timestamp": timezone.now().isoformat()
            }
    
    def _rule_based_parsing(self, command: str) -> Dict[str, Any]:
        """Rule-based parsing for common notary document patterns."""
        command_lower = command.lower()
        
        # Document type detection
        doc_type = self._detect_document_type(command_lower)
        
        # Extract entities based on document type
        entities = self._extract_entities(command, doc_type)
        
        # Transform entities into structured parties array
        parties = self._build_parties_array(entities, doc_type)
        
        # Build metadata from remaining entities
        metadata = self._build_metadata(entities, doc_type, command)
        
        return {
            "document_type": doc_type,
            "parties": parties,
            "metadata": metadata,
            "original_command": command
        }
    
    def _detect_document_type(self, command: str) -> str:
        """Detect the type of notary document from the command."""
        patterns = {
            "procuração pública": [
                r"procura[çc][ãa]o",
                r"procurador",
                r"poderes",
                r"outorgar"
            ],
            "escritura": [
                r"escritura",
                r"compra.*venda",
                r"doa[çc][ãa]o",
                r"permuta"
            ],
            "autenticacao": [
                r"autentica[çc][ãa]o",
                r"c[óo]pia.*autenticada",
                r"fiel.*c[óo]pia"
            ],
            "reconhecimento": [
                r"reconhecimento.*firma",
                r"assinatura",
                r"firma.*reconhecida"
            ],
            "testamento": [
                r"testamento",
                r"heran[çc]a",
                r"sucess[ãa]o"
            ]
        }
        
        for doc_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                if re.search(pattern, command):
                    return doc_type
        
        return "geral"  # Default fallback
    
    def _extract_entities(self, command: str, doc_type: str) -> Dict[str, Any]:
        """Extract entities like names, CPFs, values from the command."""
        entities = {}
        
        # Extract CPF patterns
        cpf_pattern = r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b'
        cpfs = re.findall(cpf_pattern, command)
        if cpfs:
            entities["cpfs"] = cpfs
        
        # Extract names (improved pattern - avoid common words)
        # First, remove common words that shouldn't be names
        common_words = {
            'fazer', 'criar', 'gerar', 'elaborar', 'preparar', 'fazer', 'de', 'para', 'com', 'poderes',
            'poder', 'venda', 'compra', 'gerais', 'especiais', 'administracao', 'reconhecimento',
            'autenticacao', 'escritura', 'testamento', 'procuracao', 'procuração', 'cpf', 'rg',
            'documento', 'ato', 'notarial', 'cartorio', 'cartório', 'tabeliao', 'tabelião'
        }
        
        name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        all_names = re.findall(name_pattern, command)
        
        # Filter out common words and very short names
        names = [name for name in all_names 
                if name.lower() not in common_words 
                and len(name.split()) >= 2  # At least first and last name
                and len(name) > 5]  # Reasonable length
        
        
        if names:
            entities["nomes"] = names
        
        # Extract monetary values
        value_pattern = r'R\$\s*[\d.,]+|\b[\d.,]+\s*reais?\b'
        values = re.findall(value_pattern, command, re.IGNORECASE)
        if values:
            entities["valores"] = values
        
        # Document-specific entity extraction
        if doc_type in ["procuracao", "procuração pública", "procuração"]:
            entities.update(self._extract_procuracao_entities(command))
        elif doc_type == "escritura":
            entities.update(self._extract_escritura_entities(command))
        
        return entities
    
    def _extract_procuracao_entities(self, command: str) -> Dict[str, Any]:
        """Extract specific entities for procuração documents."""
        entities = {}
        
        # Look for "Outorgante: X" and "Outorgado: Y" pattern
        # Capture until comma or semicolon to get full names
        outorgante_pattern = r'outorgante:\s*([^,;]+?)(?:\s*,\s*CPF|$)'
        outorgado_pattern = r'outorgado:\s*([^,;]+?)(?:\s*,\s*CPF|$)'
        
        outorgante_match = re.search(outorgante_pattern, command, re.IGNORECASE)
        outorgado_match = re.search(outorgado_pattern, command, re.IGNORECASE)
        
        if outorgante_match:
            entities["outorgante"] = outorgante_match.group(1).strip()
        if outorgado_match:
            entities["outorgado"] = outorgado_match.group(1).strip()
        
        # Fallback to "de X para Y" pattern if the above doesn't work
        if not entities.get("outorgante") or not entities.get("outorgado"):
            de_para_pattern = r'de\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+para\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            match = re.search(de_para_pattern, command, re.IGNORECASE)
            if match:
                entities["outorgante"] = match.group(1).strip()
                entities["outorgado"] = match.group(2).strip()
        
        # Look for power types
        power_patterns = {
            "gerais": r"poderes?\s+gerais?",
            "especiais": r"poderes?\s+especiais?",
            "administracao": r"administra[çc][ãa]o",
            "venda": r"venda|vender",
            "compra": r"compra|comprar"
        }
        
        for power_type, pattern in power_patterns.items():
            if re.search(pattern, command, re.IGNORECASE):
                entities["tipo_poderes"] = power_type
                break
        
        return entities
    
    def _extract_escritura_entities(self, command: str) -> Dict[str, Any]:
        """Extract specific entities for escritura documents."""
        entities = {}
        
        # Look for property description
        property_pattern = r'im[óo]vel\s+([^,\n]+?)(?:\s|,|$)'
        match = re.search(property_pattern, command, re.IGNORECASE)
        if match:
            entities["descricao_imovel"] = match.group(1).strip()
        
        return entities
    
    def _build_parties_array(self, entities: Dict[str, Any], doc_type: str) -> List[Dict[str, Any]]:
        """Build structured parties array from extracted entities."""
        parties = []
        
        # Get names and CPFs
        nomes = entities.get("nomes", [])
        cpfs = entities.get("cpfs", [])
        
        if doc_type in ["procuracao", "procuração pública", "procuração"]:
            # For procuração, try to identify outorgante and outorgado
            outorgante = entities.get("outorgante")
            outorgado = entities.get("outorgado")
            
            # Track which names we've already used
            used_names = set()
            
            if outorgante:
                # Find CPF for outorgante
                outorgante_cpf = None
                if cpfs and len(cpfs) > 0:
                    outorgante_cpf = cpfs[0]
                
                parties.append({
                    "name": outorgante,
                    "role": "outorgante",
                    "cpf": outorgante_cpf
                })
                used_names.add(outorgante)
            
            if outorgado:
                # Find CPF for outorgado
                outorgado_cpf = None
                if cpfs and len(cpfs) > 1:
                    outorgado_cpf = cpfs[1]
                elif cpfs and len(cpfs) == 1 and not outorgante:
                    outorgado_cpf = cpfs[0]
                
                parties.append({
                    "name": outorgado,
                    "role": "outorgado",
                    "cpf": outorgado_cpf
                })
                used_names.add(outorgado)
            
            # If we don't have specific outorgante/outorgado, use the general names
            if not outorgante and not outorgado:
                for i, nome in enumerate(nomes):
                    cpf = cpfs[i] if i < len(cpfs) else None
                    role = "outorgante" if i == 0 else "outorgado" if i == 1 else "parte"
                    
                    parties.append({
                        "name": nome,
                        "role": role,
                        "cpf": cpf
                    })
            else:
                # Add any remaining names as general parties (avoid duplicates)
                for nome in nomes:
                    if nome not in used_names:
                        parties.append({
                            "name": nome,
                            "role": "parte"
                        })
                        used_names.add(nome)
        
        elif doc_type == "escritura":
            # For escritura, identify comprador and vendedor
            for i, nome in enumerate(nomes):
                cpf = cpfs[i] if i < len(cpfs) else None
                role = "comprador" if i == 0 else "vendedor" if i == 1 else "parte"
                
                parties.append({
                    "name": nome,
                    "role": role,
                    "cpf": cpf
                })
        
        else:
            # For other document types, add all names as general parties
            for i, nome in enumerate(nomes):
                cpf = cpfs[i] if i < len(cpfs) else None
                
                parties.append({
                    "name": nome,
                    "role": "parte",
                    "cpf": cpf
                })
        
        return parties
    
    def _build_metadata(self, entities: Dict[str, Any], doc_type: str, original_command: str = "") -> Dict[str, Any]:
        """Build metadata object from remaining entities."""
        metadata = {}
        
        # Extract validity days
        validity_pattern = r'v[áa]lid[ao]?\s+por\s+(\d+)\s+dias?'
        validity_match = re.search(validity_pattern, original_command, re.IGNORECASE)
        if validity_match:
            metadata["validity_days"] = int(validity_match.group(1))
        
        # Extract location
        location_pattern = r'(?:em|localizado em|situado em)\s+([^,\n]+?)(?:\s|,|$)'
        location_match = re.search(location_pattern, original_command, re.IGNORECASE)
        if location_match:
            metadata["location"] = location_match.group(1).strip()
        
        # Document-specific metadata
        if doc_type in ["procuracao", "procuração pública", "procuração"]:
            tipo_poderes = entities.get("tipo_poderes")
            if tipo_poderes:
                metadata["tipo_poderes"] = tipo_poderes
            
            # Add special conditions based on power type
            if tipo_poderes == "venda":
                metadata["special_conditions"] = ["Poder para venda de imóveis", "Poder para receber valores"]
            elif tipo_poderes == "gerais":
                metadata["special_conditions"] = ["Poderes gerais de representação"]
        
        elif doc_type == "escritura":
            descricao_imovel = entities.get("descricao_imovel")
            if descricao_imovel:
                metadata["descricao_imovel"] = descricao_imovel
            
            # Extract property value
            valores = entities.get("valores", [])
            if valores:
                metadata["valor_imovel"] = valores[0]
        
        return metadata
    
    def _calculate_confidence(self, command: str, parsed_data: Dict[str, Any]) -> float:
        """Calculate confidence score for the parsing result."""
        confidence = 0.5  # Base confidence
        
        # Boost confidence if we found a clear document type
        if parsed_data.get("document_type") != "geral":
            confidence += 0.3
        
        # Boost confidence if we found entities
        entities = parsed_data.get("entities", {})
        if entities.get("nomes"):
            confidence += 0.1
        if entities.get("cpfs"):
            confidence += 0.1
        
        # Boost confidence for specific document types with required entities
        doc_type = parsed_data.get("document_type")
        if doc_type in ["procuracao", "procuração pública", "procuração"] and entities.get("outorgante") and entities.get("outorgado"):
            confidence += 0.2
        elif doc_type == "escritura" and entities.get("descricao_imovel"):
            confidence += 0.2
        
        return min(confidence, 1.0)  # Cap at 1.0
    
    async def generate_document(
        self, 
        parsed_command: Dict[str, Any], 
        tenant_id: str,
        processo_id: str,
        created_by,
        original_command: str
    ) -> Tuple[Minuta, AIGeneratedMinuta]:
        """
        Generate complete document from parsed command.
        
        Args:
            parsed_command: Output from parse_command()
            tenant_id: Tenant ID for multi-tenancy
            processo_id: Process ID to attach the minuta to
            created_by: User who initiated the generation
            original_command: Original command from the user
        Returns:
            Tuple of (Minuta, AIGeneratedMinuta) objects
        """
        start_time = time.time()
        
        # Extract jurisdiction from tenant context (default to SP)
        jurisdiction = "SP"  # TODO: Extract from tenant context
        
        # Get appropriate template using hybrid approach
        template, template_source = await self._select_template_hybrid(
            parsed_command['parsed_intent'], 
            tenant_id, 
            jurisdiction
        )
        
        # Handle different template sources
        if template_source == "ai_generated":
            # Use Intent Engine for AI generation
            try:
                intent_result = await self.intent_client.generate_draft(
                    parsed_intent=parsed_command['parsed_intent'],
                    tenant_id=UUID(tenant_id),
                    user_id=None
                )
                document_content = intent_result.get('content', '')
            except Exception as e:
                logger.error(f"AI generation failed: {e}")
                raise ValueError(f"Failed to generate document: {e}")
        else:
            # Use template-based generation
            if not template:
                raise ValueError(f"No template found for document type: {parsed_command['parsed_intent']['document_type']}")
            
            # Get relevant clauses
            clauses = self._select_clauses(parsed_command, tenant_id)
            
            # Generate document content
            document_content = self._generate_content(template, clauses, parsed_command)
            
            # Update template usage count
            template.usage_count += 1
            template.save(update_fields=['usage_count'])
        
        # Create minuta
        last_minuta = Minuta.objects.filter(processo_id=processo_id).order_by('-versao').first()
        next_version = (last_minuta.versao + 1) if last_minuta else 1
        
        minuta = Minuta.objects.create(
            tenant_id=tenant_id,
            processo_id=processo_id,
            versao=next_version,
            gerada_por="ia",
            template_id=template.id if template else None,
            corpo_md=document_content,
            variaveis_json=parsed_command['parsed_intent'],
            created_by=created_by,
        )
        
        # Create AI generation tracking record
        generation_time = int((time.time() - start_time) * 1000)
        
        # Prepare clauses used (only for template-based generation)
        clauses_used = []
        if template_source != "ai_generated" and template:
            clauses = self._select_clauses(parsed_command, tenant_id)
            clauses_used = [str(clause.id) for clause in clauses]
        
        ai_generation = AIGeneratedMinuta.objects.create(
            tenant_id=tenant_id,
            minuta=minuta,
            original_command=original_command,
            parsed_intent=parsed_command['parsed_intent'],
            ai_model_version=parsed_command.get('model_version', 'gpt-4o-mini'),
            confidence_score=parsed_command['confidence'],
            generation_time_ms=generation_time,
            clauses_used=clauses_used,
            template_source=template_source
        )
        
        # Create audit log
        AuditLog.objects.create(
            tenant_id=tenant_id,
            actor=created_by,
            resource_type="minuta",
            resource_id=minuta.id,
            action="ai_generate",
            diff_json={
                "ai_generation_id": str(ai_generation.id),
                "original_command": original_command,
                "confidence": parsed_command['confidence'],
                "document_type": parsed_command['parsed_intent']['document_type'],
                "clauses_used": len(clauses)
            },
            extra={
                "ai_model_version": parsed_command.get('model_version', 'gpt-4o-mini'),
                "generation_time_ms": generation_time
            }
        )
        
        # Create analytics record
        AIUsageAnalytics.objects.create(
            tenant_id=tenant_id,
            command_length=len(original_command),
            generation_time_ms=generation_time,
            confidence_score=parsed_command['confidence'],
            approved=False,  # Will be updated when reviewed
            edited_after_generation=False,  # Will be updated if edited
            document_type=parsed_command['parsed_intent']['document_type'],
            clauses_count=len(clauses),
            ai_model_version=parsed_command.get('model_version', 'gpt-4o-mini')
        )
        
        return minuta, ai_generation
    
    async def _select_template_hybrid(
        self, 
        parsed_intent: Dict[str, Any], 
        tenant_id: str,
        jurisdiction: str = "SP"
    ) -> Tuple[Optional[Template], str]:
        """
        Select template using hybrid approach.
        Returns: (template, source) where source is "tenant"|"lexnode"|"ai_generated"
        """
        document_type = parsed_intent['document_type']
        
        # Step 1: Try tenant-specific template
        tenant_template = self._get_tenant_template(tenant_id, document_type)
        if tenant_template:
            return tenant_template, "tenant"
        
        # Step 2: Query LexNode for jurisdiction template
        lexnode_template = await self._get_lexnode_template(document_type, jurisdiction)
        if lexnode_template:
            # Save to tenant library for future use
            saved_template = self._save_template_to_tenant(
                tenant_id, document_type, lexnode_template
            )
            return saved_template, "lexnode"
        
        # Step 3: Use AI to generate template structure
        # (fallback - should be rare)
        return None, "ai_generated"
    
    def _get_tenant_template(self, tenant_id: str, document_type: str) -> Optional[Template]:
        """Get tenant-specific template for document type."""
        # Map document types to template categories
        category_mapping = {
            "procuracao": "procuracao",
            "procuração pública": "procuracao",
            "procuração": "procuracao",
            "escritura": "escritura",
            "escritura de compra e venda": "escritura",
            "autenticacao": "autenticacao",
            "autenticação de cópia": "autenticacao",
            "reconhecimento": "reconhecimento",
            "reconhecimento de firma": "reconhecimento",
            "testamento": "testamento"
        }
        
        category = category_mapping.get(document_type, "outro")
        
        return Template.objects.filter(
            tenant_id=tenant_id,
            document_type=category,
            is_active=True
        ).order_by('-version').first()
    
    async def _get_lexnode_template(self, document_type: str, jurisdiction: str) -> Optional[Dict[str, Any]]:
        """Get template from LexNode service."""
        try:
            return await self.lexnode_client.retrieve_template(
                document_type=document_type,
                jurisdiction=jurisdiction
            )
        except Exception as e:
            logger.error(f"Failed to retrieve template from LexNode: {e}")
            return None
    
    def _save_template_to_tenant(
        self, 
        tenant_id: str, 
        document_type: str, 
        lexnode_template: Dict[str, Any]
    ) -> Template:
        """Save LexNode template to tenant library."""
        # Map document types to template categories
        category_mapping = {
            "procuracao": "procuracao",
            "procuração pública": "procuracao",
            "procuração": "procuracao",
            "escritura": "escritura",
            "escritura de compra e venda": "escritura",
            "autenticacao": "autenticacao",
            "autenticação de cópia": "autenticacao",
            "reconhecimento": "reconhecimento",
            "reconhecimento de firma": "reconhecimento",
            "testamento": "testamento"
        }
        
        category = category_mapping.get(document_type, "outro")
        
        # Create new template from LexNode data
        template = Template.objects.create(
            tenant_id=tenant_id,
            name=f"{category}_lexnode_{lexnode_template.get('id', 'unknown')}",
            document_type=category,
            corpo_template=lexnode_template.get('template_content', ''),
            schema=lexnode_template.get('schema', {}),
            source="lexnode",
            jurisdiction=lexnode_template.get('jurisdiction', ''),
            description=f"Template from LexNode for {document_type}",
            is_active=True,
            version="1.0"
        )
        
        logger.info(f"Saved LexNode template to tenant {tenant_id}: {template.name}")
        return template
    
    def _select_clauses(self, parsed_command: Dict[str, Any], tenant_id: str) -> List:
        """Select relevant clauses based on parsed command."""
        # Note: ClauseLibrary model has been removed as per refactoring plan
        # Return empty list for now
        return []
    
    def _clause_matches_conditions(self, clause, entities: Dict[str, Any]) -> bool:
        """Check if a clause matches the current conditions."""
        # Note: ClauseLibrary model has been removed as per refactoring plan
        return False
        
        if not conditions:
            return True  # No conditions means always use
        
        # Check if required entities are present
        required_entities = conditions.get('required_entities', [])
        for entity in required_entities:
            if entity not in entities:
                return False
        
        # Check if power type matches (for procuração)
        if 'tipo_poderes' in conditions:
            if entities.get('tipo_poderes') != conditions['tipo_poderes']:
                return False
        
        return True
    
    def _generate_content(self, template: DocumentTemplate, clauses: List, parsed_command: Dict[str, Any]) -> str:
        """Generate document content using template and clauses."""
        # Start with template content
        content = template.corpo_template
        
        # Get parties and metadata from the new structure
        parties = parsed_command['parsed_intent'].get('parties', [])
        metadata = parsed_command['parsed_intent'].get('metadata', {})
        
        # Create a mapping of template variables to values
        template_vars = {}
        
        # Map parties to template variables
        for party in parties:
            if party['role'] == 'outorgante':
                template_vars['OUTORGANTE'] = party['name']
                template_vars['outorgante_nome'] = party['name']
                template_vars['outorgante_cpf'] = party.get('cpf', '')
                template_vars['outorgante_rg'] = party.get('rg', '')
                template_vars['outorgante_endereco'] = party.get('endereco', '')
                template_vars['outorgante_cidade'] = party.get('cidade', '')
                template_vars['outorgante_estado'] = party.get('estado', '')
                template_vars['ESTADO_CIVIL_OUTORGANTE'] = party.get('estado_civil', 'solteiro(a)')
            elif party['role'] == 'outorgado':
                template_vars['OUTORGADO'] = party['name']
                template_vars['outorgado_nome'] = party['name']
                template_vars['outorgado_cpf'] = party.get('cpf', '')
                template_vars['outorgado_rg'] = party.get('rg', '')
                template_vars['outorgado_endereco'] = party.get('endereco', '')
                template_vars['outorgado_cidade'] = party.get('cidade', '')
                template_vars['outorgado_estado'] = party.get('estado', '')
                template_vars['ESTADO_CIVIL_OUTORGADO'] = party.get('estado_civil', 'solteiro(a)')
        
        # Map metadata to template variables
        template_vars.update({
            'tipo_poderes': metadata.get('tipo_poderes', 'gerais'),
            'validade_dias': metadata.get('validity_days', 90),
            'cidade': metadata.get('location', 'São Paulo'),
            'CIDADE': metadata.get('location', 'São Paulo'),
            'OBJETO_PROCURACAO': metadata.get('objeto', 'Venda de imóvel'),
            'VIGENCIA': metadata.get('vigencia', '1 (um) ano'),
            'FORO': metadata.get('foro', 'São Paulo'),
            'DATA_ATUAL': '{{ data_atual }}',  # Will be filled by template engine
            'data_atual': '{{ data_atual }}',  # Will be filled by template engine
            'protocolo_numero': '{{ protocolo_numero }}',  # Will be filled by template engine
            'cartorio_nome': '{{ cartorio_nome }}',  # Will be filled by template engine
            'cartorio_endereco': '{{ cartorio_endereco }}',  # Will be filled by template engine
            'cartorio_telefone': '{{ cartorio_telefone }}',  # Will be filled by template engine
        })
        
        # Replace template variables
        for key, value in template_vars.items():
            placeholder = f"{{{{{key}}}}}"
            if isinstance(value, list):
                value = ", ".join(value)
            content = content.replace(placeholder, str(value))
        
        # Replace common placeholders with actual values
        placeholder_mappings = {
            '{{PLACEHOLDER_RG}}': template_vars.get('outorgante_rg', ''),
            '{{PLACEHOLDER_CPF}}': template_vars.get('outorgante_cpf', ''),
            '{{PLACEHOLDER_ENDERECO}}': template_vars.get('outorgante_endereco', ''),
            '{{PLACEHOLDER_CIDADE}}': template_vars.get('outorgante_cidade', ''),
            '{{PLACEHOLDER_ESTADO}}': template_vars.get('outorgante_estado', ''),
        }
        
        for placeholder, value in placeholder_mappings.items():
            content = content.replace(placeholder, str(value))
        
        # Add selected clauses
        clause_texts = []
        for clause in clauses:
            clause_texts.append(clause.texto)
            # Increment usage counter
            clause.frequencia_uso += 1
            clause.save(update_fields=['frequencia_uso'])
        
        if clause_texts:
            content += "\n\n" + "\n\n".join(clause_texts)
        
        return content
    
    def suggest_clauses(self, partial_text: str, context: Dict[str, Any], tenant_id: str) -> List[Dict[str, Any]]:
        """
        Suggest legal clauses as user types.
        
        Args:
            partial_text: The text the user is currently typing
            context: Context about the document being created
            tenant_id: Tenant ID for multi-tenancy
            
        Returns:
            List of suggested clauses with confidence scores
        """
        suggestions = []
        
        # Note: ClauseLibrary model has been removed as per refactoring plan
        clauses = []
        
        for clause in clauses:
            # Calculate relevance score
            relevance = self._calculate_clause_relevance(clause, partial_text, context)
            
            suggestions.append({
                "clause_id": str(clause.id),
                "nome": clause.nome,
                "texto": clause.texto,
                "categoria": clause.categoria,
                "relevance_score": relevance,
                "usage_count": clause.frequencia_uso
            })
        
        # Sort by relevance score
        suggestions.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return suggestions
    
    def _calculate_clause_relevance(self, clause, partial_text: str, context: Dict[str, Any]) -> float:
        """Calculate how relevant a clause is to the current context."""
        relevance = 0.0
        
        # Boost if partial text appears in clause
        if partial_text.lower() in clause.texto.lower():
            relevance += 0.5
        
        # Boost if clause category matches document type
        if context.get('document_type') == clause.categoria:
            relevance += 0.3
        
        # Note: ClauseLibrary model has been removed as per refactoring plan
        # Skip usage frequency boost
        
        return min(relevance, 1.0)
    
    # _openai_parsing method removed - now using intent-engine microservice

    # _transform_openai_result method removed - no longer needed

    def generate_document_from_intent(
        self, 
        parsed_intent: Dict[str, Any], 
        selected_clauses: List[str],
        tenant_id: str,
        processo_id: str,
        created_by,
        original_command: str
    ) -> Tuple[Minuta, AIGeneratedMinuta]:
        """
        Generate document from parsed intent and selected clauses.
        
        This is a wrapper around generate_document() that takes the parsed intent
        directly instead of a full parsed command.
        
        Args:
            parsed_intent: Parsed intent from analyze_command
            selected_clauses: List of clause IDs to include
            tenant_id: Tenant ID for multi-tenancy
            processo_id: Process ID to attach the minuta to
            created_by: User who initiated the generation
            original_command: Original command from the user
        Returns:
            Tuple of (Minuta, AIGeneratedMinuta) objects
        """
        # Create a parsed command structure that matches what generate_document expects
        parsed_command = {
            "parsed_intent": parsed_intent,
            "confidence": parsed_intent.get("confidence_score", 0.8),
            "generation_time_ms": 0,  # Will be calculated in generate_document
            "selected_clauses": selected_clauses
        }
      
        return self.generate_document(parsed_command, tenant_id, processo_id, created_by, original_command)
    
    async def rewrite_document_content(
        self, 
        content: str, 
        improvement_prompt: str, 
        is_partial: bool = False
    ) -> str:
        """
        Rewrite document content using intent-engine microservice based on user improvement prompt.
        
        Args:
            content: The content to rewrite (full document or selected text)
            improvement_prompt: User's prompt for improvements/edits
            is_partial: Whether this is a partial rewrite (selected text only)
            
        Returns:
            Rewritten content as string
        """
        try:
            # Use intent-engine microservice for document rewriting
            result = await self.intent_client.rewrite_content(
                content=content,
                improvement_prompt=improvement_prompt,
                document_type="geral",  # Default document type
                preserve_variables=True,
                tenant_id=None,  # Will be set by the calling view
                user_id=None
            )
            
            return result.get("rewritten_content", content)
            
        except Exception as e:
            # Fallback: return original content with a note
            print(f"Intent-engine rewrite failed: {e}")
            return f"{content}\n\n[Nota: IA não disponível - {improvement_prompt}]"