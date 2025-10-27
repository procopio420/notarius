from datetime import datetime
from typing import Optional

from django.db import transaction
from django.utils import timezone

from .models import Processo, Protocolo


class ProtocoloService:
    """Service for managing protocol numbering and generation."""

    def gerar_proximo_numero(self, tenant_id: str, ano: Optional[int] = None) -> int:
        """
        Generate the next sequential protocol number for a tenant and year.
        
        Args:
            tenant_id: UUID of the tenant
            ano: Year (defaults to current year)
            
        Returns:
            Next protocol number
        """
        if ano is None:
            ano = timezone.now().year
        
        with transaction.atomic():
            # Use select_for_update to prevent race conditions
            last_protocol = Protocolo.objects.filter(
                tenant_id=tenant_id,
                ano=ano
            ).select_for_update().order_by('-numero').first()
            
            if last_protocol:
                next_numero = last_protocol.numero + 1
            else:
                next_numero = 1
            
            return next_numero

    def criar_protocolo(
        self,
        tenant_id: str,
        processo_id: str,
        tipo: str = "entrada",
        observacoes: str = "",
        ano: Optional[int] = None
    ) -> Protocolo:
        """
        Create a new protocol for a processo.
        
        Args:
            tenant_id: UUID of the tenant
            processo_id: UUID of the processo
            tipo: Protocol type (entrada, saida, interno)
            observacoes: Optional notes
            ano: Year (defaults to current year)
            
        Returns:
            Created Protocolo instance
        """
        if ano is None:
            ano = timezone.now().year
        
        # Get next number
        numero = self.gerar_proximo_numero(tenant_id, ano)
        
        # Create protocol
        protocolo = Protocolo.objects.create(
            tenant_id=tenant_id,
            numero=numero,
            ano=ano,
            processo_id=processo_id,
            tipo=tipo,
            observacoes=observacoes,
        )
        
        return protocolo

    def buscar_por_numero(
        self, 
        tenant_id: str, 
        numero: int, 
        ano: Optional[int] = None
    ) -> Optional[Protocolo]:
        """
        Search for a protocol by number.
        
        Args:
            tenant_id: UUID of the tenant
            numero: Protocol number
            ano: Year (defaults to current year)
            
        Returns:
            Protocolo instance if found, None otherwise
        """
        if ano is None:
            ano = timezone.now().year
        
        try:
            return Protocolo.objects.get(
                tenant_id=tenant_id,
                numero=numero,
                ano=ano
            )
        except Protocolo.DoesNotExist:
            return None

    def buscar_por_processo(self, tenant_id: str, processo_id: str) -> list[Protocolo]:
        """
        Get all protocols for a processo.
        
        Args:
            tenant_id: UUID of the tenant
            processo_id: UUID of the processo
            
        Returns:
            List of Protocolo instances
        """
        return list(Protocolo.objects.filter(
            tenant_id=tenant_id,
            processo_id=processo_id
        ).order_by('ano', 'numero'))

    def get_protocolo_formatado(
        self, 
        tenant_id: str, 
        numero: int, 
        ano: Optional[int] = None
    ) -> Optional[str]:
        """
        Get formatted protocol number.
        
        Args:
            tenant_id: UUID of the tenant
            numero: Protocol number
            ano: Year (defaults to current year)
            
        Returns:
            Formatted protocol string (e.g., "PROT-2025-000123") or None
        """
        protocolo = self.buscar_por_numero(tenant_id, numero, ano)
        if protocolo:
            return protocolo.numero_formatado
        return None

    def get_estatisticas_ano(self, tenant_id: str, ano: Optional[int] = None) -> dict:
        """
        Get protocol statistics for a year.
        
        Args:
            tenant_id: UUID of the tenant
            ano: Year (defaults to current year)
            
        Returns:
            Dictionary with statistics
        """
        if ano is None:
            ano = timezone.now().year
        
        protocols = Protocolo.objects.filter(tenant_id=tenant_id, ano=ano)
        
        total = protocols.count()
        por_tipo = {}
        
        for tipo, _ in Protocolo.TIPO:
            count = protocols.filter(tipo=tipo).count()
            por_tipo[tipo] = count
        
        return {
            'ano': ano,
            'total': total,
            'por_tipo': por_tipo,
            'primeiro_numero': protocols.order_by('numero').first().numero if total > 0 else None,
            'ultimo_numero': protocols.order_by('-numero').first().numero if total > 0 else None,
        }

    def auto_gerar_protocolo_entrada(self, processo: Processo) -> Optional[Protocolo]:
        """
        Automatically generate an entry protocol for a processo when it reaches certain status.
        
        Args:
            processo: Processo instance
            
        Returns:
            Created Protocolo instance or None
        """
        # Only generate protocol for certain statuses
        if processo.status not in ["analise", "assinatura"]:
            return None
        
        # Check if entry protocol already exists
        existing = Protocolo.objects.filter(
            tenant=processo.tenant,
            processo=processo,
            tipo="entrada"
        ).first()
        
        if existing:
            return existing
        
        # Create entry protocol
        return self.criar_protocolo(
            tenant_id=processo.tenant_id,
            processo_id=processo.id,
            tipo="entrada",
            observacoes="Protocolo gerado automaticamente"
        )

    def auto_gerar_protocolo_saida(self, processo: Processo) -> Optional[Protocolo]:
        """
        Automatically generate an exit protocol for a processo when it's completed.
        
        Args:
            processo: Processo instance
            
        Returns:
            Created Protocolo instance or None
        """
        # Only generate protocol for completed status
        if processo.status != "arquivado":
            return None
        
        # Check if exit protocol already exists
        existing = Protocolo.objects.filter(
            tenant=processo.tenant,
            processo=processo,
            tipo="saida"
        ).first()
        
        if existing:
            return existing
        
        # Create exit protocol
        return self.criar_protocolo(
            tenant_id=processo.tenant_id,
            processo_id=processo.id,
            tipo="saida",
            observacoes="Protocolo de saída gerado automaticamente"
        )

