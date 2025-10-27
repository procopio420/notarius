from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Processo
from .services import ProtocoloService


@receiver(post_save, sender=Processo)
def auto_gerar_protocolo_processo(sender, instance, created, **kwargs):
    """
    Automatically generate protocols when processo status changes.
    """
    if created:
        # New processo - no protocol needed yet
        return
    
    # Check if status changed to trigger protocol generation
    if instance.status in ["analise", "assinatura"]:
        # Generate entry protocol
        protocolo_service = ProtocoloService()
        protocolo_service.auto_gerar_protocolo_entrada(instance)
    
    elif instance.status == "arquivado":
        # Generate exit protocol
        protocolo_service = ProtocoloService()
        protocolo_service.auto_gerar_protocolo_saida(instance)

