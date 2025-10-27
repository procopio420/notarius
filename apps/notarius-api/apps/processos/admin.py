from django.contrib import admin

from apps.base.admin_mixins import BaseTenantAdmin

from .models import Processo, ProcessoParte, Protocolo
from .services import ProtocoloService


@admin.register(Processo)
class ProcessoAdmin(BaseTenantAdmin):
    list_display = ("id", "tipo_ato", "status", "responsavel", "tenant", "created_at")
    list_filter = ("tipo_ato", "status")
    search_fields = ("id", "tipo_ato")
    autocomplete_fields = ("responsavel",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(ProcessoParte)
class ProcessoParteAdmin(BaseTenantAdmin):
    list_display = ("processo", "parte", "papel", "tenant", "created_at")
    list_filter = ("papel",)
    search_fields = ("processo__id", "parte__nome")
    autocomplete_fields = ("processo", "parte")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Protocolo)
class ProtocoloAdmin(BaseTenantAdmin):
    list_display = ['numero_formatado', 'processo', 'tipo', 'ano', 'created_at']
    list_filter = ['tipo', 'ano', 'created_at']
    search_fields = ['numero', 'processo__id', 'observacoes']
    readonly_fields = ['numero', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações do Protocolo', {
            'fields': ('tenant', 'numero', 'ano', 'processo', 'tipo')
        }),
        ('Observações', {
            'fields': ('observacoes',)
        }),
        ('Metadados', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['generate_protocols_for_processos']
    
    def generate_protocols_for_processos(self, request, queryset):
        """Generate protocols for selected processos."""
        service = ProtocoloService()
        generated = 0
        
        for protocolo in queryset:
            try:
                # Generate entry protocol if doesn't exist
                existing_entry = Protocolo.objects.filter(
                    tenant=protocolo.tenant,
                    processo=protocolo.processo,
                    tipo='entrada'
                ).first()
                
                if not existing_entry:
                    service.criar_protocolo(
                        tenant_id=str(protocolo.tenant.id),
                        processo_id=str(protocolo.processo.id),
                        tipo='entrada',
                        observacoes='Gerado via admin'
                    )
                    generated += 1
                    
            except Exception as e:
                self.message_user(request, f'Erro ao gerar protocolo para {protocolo.processo.id}: {e}', level='ERROR')
        
        self.message_user(request, f'{generated} protocolos de entrada gerados.')
    generate_protocols_for_processos.short_description = "Gerar protocolos de entrada para processos"
