from django.db import models
from django.conf import settings

from apps.base.models import BaseTenantModel


class WorkflowTask(BaseTenantModel):
    """
    Model for workflow tasks and task management.
    """
    TIPO_CHOICES = [
        ('autenticacao', 'Autenticação'),
        ('assinatura', 'Assinatura'),
        ('revisao', 'Revisão'),
        ('aprovacao', 'Aprovação'),
        ('finalizacao', 'Finalização'),
        ('outro', 'Outro'),
    ]
    
    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('media', 'Média'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]
    
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('concluida', 'Concluída'),
        ('cancelada', 'Cancelada'),
        ('pausada', 'Pausada'),
    ]
    
    titulo = models.CharField(max_length=200, help_text="Task title")
    descricao = models.TextField(blank=True, help_text="Task description")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, help_text="Task type")
    prioridade = models.CharField(max_length=10, choices=PRIORIDADE_CHOICES, default='media')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pendente')
    
    # Assignment
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='created_tasks'
    )
    
    # Timing
    deadline = models.DateTimeField(null=True, blank=True, help_text="Task deadline")
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Related objects
    documento = models.ForeignKey(
        'documentos.Documento', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='workflow_tasks'
    )
    minuta = models.ForeignKey(
        'documentos.Minuta', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='workflow_tasks'
    )
    processo = models.ForeignKey(
        'processos.Processo', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='workflow_tasks'
    )
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional task metadata")
    notes = models.TextField(blank=True, help_text="Task notes and comments")
    
    class Meta:
        db_table = 'workflow_tasks'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status'], name='ix_workflow_task_status'),
            models.Index(fields=['tenant', 'tipo'], name='ix_workflow_task_tipo'),
            models.Index(fields=['tenant', 'assigned_to'], name='ix_workflow_task_assigned'),
            models.Index(fields=['deadline'], name='ix_workflow_task_deadline'),
        ]
    
    def __str__(self):
        return f"{self.titulo} ({self.get_status_display()})"


class DocumentoNota(BaseTenantModel):
    """
    Model for internal notes on documents.
    """
    documento = models.ForeignKey(
        'documentos.Documento', 
        on_delete=models.CASCADE,
        related_name='notas'
    )
    titulo = models.CharField(max_length=200, help_text="Note title")
    conteudo = models.TextField(help_text="Note content")
    is_private = models.BooleanField(default=False, help_text="Is this a private note?")
    is_resolved = models.BooleanField(default=False, help_text="Is this note resolved?")
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='created_documento_notas'
    )
    
    class Meta:
        db_table = 'documento_notas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'documento'], name='ix_documento_nota_doc'),
            models.Index(fields=['tenant', 'is_private'], name='ix_documento_nota_private'),
            models.Index(fields=['tenant', 'is_resolved'], name='ix_documento_nota_resolved'),
        ]
    
    def __str__(self):
        return f"{self.titulo} - {self.documento}"


class NotificationTemplate(BaseTenantModel):
    """
    Model for notification templates.
    """
    TIPO_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
    ]
    
    TRIGGER_CHOICES = [
        ('task_assigned', 'Task Assigned'),
        ('task_completed', 'Task Completed'),
        ('deadline_approaching', 'Deadline Approaching'),
        ('document_ready', 'Document Ready'),
        ('signature_required', 'Signature Required'),
        ('custom', 'Custom'),
    ]
    
    nome = models.CharField(max_length=100, help_text="Template name")
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, help_text="Notification type")
    trigger = models.CharField(max_length=30, choices=TRIGGER_CHOICES, help_text="Trigger event")
    assunto = models.CharField(max_length=200, help_text="Subject line")
    corpo = models.TextField(help_text="Message body")
    is_active = models.BooleanField(default=True, help_text="Is this template active?")
    
    # Template variables
    variables = models.JSONField(default=list, help_text="Available template variables")
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT,
        related_name='created_notification_templates'
    )
    
    class Meta:
        db_table = 'notification_templates'
        ordering = ['nome']
        indexes = [
            models.Index(fields=['tenant', 'tipo'], name='ix_notification_template_tipo'),
            models.Index(fields=['tenant', 'trigger'], name='ix_notification_trigger'),
            models.Index(fields=['tenant', 'is_active'], name='ix_notification_active'),
        ]
    
    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"


class NotificationLog(BaseTenantModel):
    """
    Model for logging sent notifications.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
        ('bounced', 'Bounced'),
    ]
    
    template = models.ForeignKey(
        NotificationTemplate, 
        on_delete=models.PROTECT,
        related_name='logs'
    )
    
    # Recipient info
    recipient_name = models.CharField(max_length=200, help_text="Recipient name")
    recipient_email = models.EmailField(help_text="Recipient email")
    recipient_phone = models.CharField(max_length=20, blank=True, help_text="Recipient phone")
    
    # Message content
    rendered_subject = models.CharField(max_length=200, help_text="Rendered subject")
    rendered_body = models.TextField(help_text="Rendered message body")
    
    # Status and timing
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    # Error handling
    error_message = models.TextField(blank=True, help_text="Error message if failed")
    retry_count = models.PositiveIntegerField(default=0)
    
    # Context
    context_data = models.JSONField(default=dict, help_text="Context data used for rendering")
    
    class Meta:
        db_table = 'notification_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tenant', 'status'], name='ix_notification_log_status'),
            models.Index(fields=['tenant', 'recipient_email'], name='ix_notification_log_email'),
            models.Index(fields=['tenant', 'sent_at'], name='ix_notification_log_sent'),
        ]
    
    def __str__(self):
        return f"{self.template.nome} -> {self.recipient_email} ({self.get_status_display()})"
