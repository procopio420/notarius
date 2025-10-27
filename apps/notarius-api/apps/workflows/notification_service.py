"""
Notification service for sending various types of notifications.
"""

from typing import Any, Dict, List, Optional
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from .models import NotificationTemplate, NotificationLog


class NotificationService:
    """Service for managing notifications and templates."""

    def __init__(self):
        pass

    def send_notification(
        self,
        template_name: str,
        recipient_email: str,
        recipient_name: str = "",
        context_data: Dict[str, Any] = None,
        tenant=None
    ) -> bool:
        """
        Send a notification using a template.
        
        Args:
            template_name: Name of the notification template
            recipient_email: Email address of the recipient
            recipient_name: Name of the recipient
            context_data: Context data for template rendering
            tenant: Tenant instance
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Get the template
            template = NotificationTemplate.objects.get(
                nome=template_name,
                tenant=tenant,
                is_active=True
            )
            
            # Render the message
            rendered_subject = self._render_template(template.assunto, context_data or {})
            rendered_body = self._render_template(template.corpo, context_data or {})
            
            # Send the notification
            success = self._send_email(
                subject=rendered_subject,
                message=rendered_body,
                recipient_email=recipient_email,
                recipient_name=recipient_name
            )
            
            # Log the notification
            NotificationLog.objects.create(
                tenant=tenant,
                template=template,
                recipient_name=recipient_name,
                recipient_email=recipient_email,
                rendered_subject=rendered_subject,
                rendered_body=rendered_body,
                status='sent' if success else 'failed',
                sent_at=timezone.now() if success else None,
                context_data=context_data or {}
            )
            
            return success
            
        except NotificationTemplate.DoesNotExist:
            return False
        except Exception as e:
            # Log error
            if 'template' in locals():
                NotificationLog.objects.create(
                    tenant=tenant,
                    template=template,
                    recipient_name=recipient_name,
                    recipient_email=recipient_email,
                    rendered_subject="",
                    rendered_body="",
                    status='failed',
                    error_message=str(e),
                    context_data=context_data or {}
                )
            return False

    def _render_template(self, template_content: str, context: Dict[str, Any]) -> str:
        """Render template content with context data."""
        try:
            from django.template import Template, Context
            template = Template(template_content)
            return template.render(Context(context))
        except Exception:
            # Fallback to simple string replacement
            rendered = template_content
            for key, value in context.items():
                rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
            return rendered

    def _send_email(
        self,
        subject: str,
        message: str,
        recipient_email: str,
        recipient_name: str = ""
    ) -> bool:
        """Send email notification."""
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient_email],
                fail_silently=False
            )
            return True
        except Exception:
            return False

    def get_notification_stats(self, tenant_id: str, days: int = 30) -> Dict[str, Any]:
        """Get notification statistics for a tenant."""
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        
        logs = NotificationLog.objects.filter(
            tenant_id=tenant_id,
            created_at__gte=start_date
        )
        
        total_sent = logs.filter(status='sent').count()
        total_failed = logs.filter(status='failed').count()
        total_pending = logs.filter(status='pending').count()
        
        return {
            'total_notifications': logs.count(),
            'sent': total_sent,
            'failed': total_failed,
            'pending': total_pending,
            'success_rate': (total_sent / logs.count() * 100) if logs.count() > 0 else 0,
            'period_days': days
        }
