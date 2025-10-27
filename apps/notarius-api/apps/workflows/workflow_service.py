"""
Workflow automation service for Notarius.

This service manages task queues, workflow automation,
and clerk task dashboards for pending authentications, reviews, etc.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from apps.auditoria.models import AuditLog
from .models import WorkflowTask
from apps.documentos.models import Documento, Minuta
from .notification_service import NotificationService


class WorkflowService:
    """
    Service for managing workflow automation and task queues.
    
    Features:
    - Task creation and management
    - Queue system for different task types
    - Deadline monitoring
    - Automatic task assignment
    - Task dashboard data
    """

    def __init__(self):
        self.notification_service = NotificationService()

    def create_task(
        self,
        titulo: str,
        descricao: str,
        tipo: str,
        tenant_id: str,
        created_by: User,
        prioridade: str = "media",
        assigned_to: User = None,
        deadline: datetime = None,
        documento: Documento = None,
        minuta: Minuta = None,
        processo=None,
        metadata: Dict[str, Any] = None
    ) -> WorkflowTask:
        """
        Create a new workflow task.
        
        Args:
            titulo: Task title
            descricao: Task description
            tipo: Task type (autenticacao, assinatura, revisao, etc.)
            tenant_id: Tenant ID
            created_by: User who created the task
            prioridade: Task priority (baixa, media, alta, urgente)
            assigned_to: User assigned to the task
            deadline: Task deadline
            documento: Related documento
            minuta: Related minuta
            processo: Related processo
            metadata: Additional task metadata
            
        Returns:
            WorkflowTask instance
        """
        if metadata is None:
            metadata = {}

        task = WorkflowTask.objects.create(
            tenant_id=tenant_id,
            titulo=titulo,
            descricao=descricao,
            tipo=tipo,
            prioridade=prioridade,
            assigned_to=assigned_to,
            created_by=created_by,
            deadline=deadline,
            documento=documento,
            minuta=minuta,
            processo=processo,
            metadata=metadata
        )

        # Send notification if assigned
        if assigned_to and assigned_to.email:
            try:
                self.notification_service.send_task_assignment_notification(
                    task=task,
                    assigned_user_email=assigned_to.email,
                    assigned_user_name=assigned_to.get_full_name() or assigned_to.username
                )
            except Exception as e:
                print(f"Failed to send task assignment notification: {e}")

        # Log audit
        AuditLog.objects.create(
            tenant_id=tenant_id,
            actor=created_by,
            resource_type="workflow_task",
            resource_id=task.id,
            action="create",
            diff_json={
                "titulo": titulo,
                "tipo": tipo,
                "prioridade": prioridade,
                "assigned_to": assigned_to.get_full_name() if assigned_to else None,
            }
        )

        return task

    def assign_task(self, task_id: str, assigned_to: User, assigned_by: User) -> WorkflowTask:
        """Assign a task to a user."""
        task = WorkflowTask.objects.get(id=task_id)
        
        old_assigned = task.assigned_to
        task.assigned_to = assigned_to
        task.save()

        # Send notification
        if assigned_to.email:
            try:
                self.notification_service.send_task_assignment_notification(
                    task=task,
                    assigned_user_email=assigned_to.email,
                    assigned_user_name=assigned_to.get_full_name() or assigned_to.username
                )
            except Exception as e:
                print(f"Failed to send task assignment notification: {e}")

        # Log audit
        AuditLog.objects.create(
            tenant_id=task.tenant_id,
            actor=assigned_by,
            resource_type="workflow_task",
            resource_id=task.id,
            action="assign",
            diff_json={
                "old_assigned_to": old_assigned.get_full_name() if old_assigned else None,
                "new_assigned_to": assigned_to.get_full_name(),
            }
        )

        return task

    def complete_task(self, task_id: str, completed_by: User, notes: str = "") -> WorkflowTask:
        """Mark a task as completed."""
        task = WorkflowTask.objects.get(id=task_id)
        
        task.status = "concluida"
        task.completed_at = timezone.now()
        if notes:
            task.metadata["completion_notes"] = notes
        task.save()

        # Log audit
        AuditLog.objects.create(
            tenant_id=task.tenant_id,
            actor=completed_by,
            resource_type="workflow_task",
            resource_id=task.id,
            action="complete",
            diff_json={
                "completion_notes": notes,
                "completed_at": task.completed_at.isoformat(),
            }
        )

        return task

    def get_task_dashboard(self, tenant_id: str, user: User = None) -> Dict[str, Any]:
        """
        Get task dashboard data for a tenant or specific user.
        
        Args:
            tenant_id: Tenant ID
            user: Specific user (if None, returns all tasks for tenant)
            
        Returns:
            Dashboard data dictionary
        """
        base_query = WorkflowTask.objects.filter(tenant_id=tenant_id)
        
        if user:
            # User-specific dashboard
            base_query = base_query.filter(
                models.Q(assigned_to=user) | models.Q(created_by=user)
            )

        # Pending tasks
        pending_tasks = base_query.filter(status="pendente").order_by("-prioridade", "deadline")
        
        # In progress tasks
        in_progress_tasks = base_query.filter(status="em_andamento").order_by("-prioridade", "deadline")
        
        # Overdue tasks
        overdue_tasks = base_query.filter(
            status__in=["pendente", "em_andamento"],
            deadline__lt=timezone.now()
        ).order_by("deadline")
        
        # Upcoming deadlines (next 3 days)
        upcoming_deadline = timezone.now() + timedelta(days=3)
        upcoming_tasks = base_query.filter(
            status__in=["pendente", "em_andamento"],
            deadline__lte=upcoming_deadline,
            deadline__gt=timezone.now()
        ).order_by("deadline")

        # Task counts by type
        task_counts = base_query.values('tipo').annotate(
            total=models.Count('id'),
            pending=models.Count('id', filter=models.Q(status='pendente')),
            in_progress=models.Count('id', filter=models.Q(status='em_andamento')),
            completed=models.Count('id', filter=models.Q(status='concluida'))
        ).order_by('-total')

        # Task counts by priority
        priority_counts = base_query.values('prioridade').annotate(
            count=models.Count('id')
        ).order_by('-count')

        # Recent completed tasks
        recent_completed = base_query.filter(
            status="concluida",
            completed_at__gte=timezone.now() - timedelta(days=7)
        ).order_by("-completed_at")[:10]

        return {
            "pending_tasks": list(pending_tasks.values(
                'id', 'titulo', 'tipo', 'prioridade', 'deadline', 'assigned_to__username',
                'created_by__username', 'created_at'
            )),
            "in_progress_tasks": list(in_progress_tasks.values(
                'id', 'titulo', 'tipo', 'prioridade', 'deadline', 'assigned_to__username',
                'created_by__username', 'created_at'
            )),
            "overdue_tasks": list(overdue_tasks.values(
                'id', 'titulo', 'tipo', 'prioridade', 'deadline', 'assigned_to__username',
                'created_by__username', 'created_at'
            )),
            "upcoming_tasks": list(upcoming_tasks.values(
                'id', 'titulo', 'tipo', 'prioridade', 'deadline', 'assigned_to__username',
                'created_by__username', 'created_at'
            )),
            "task_counts_by_type": list(task_counts),
            "task_counts_by_priority": list(priority_counts),
            "recent_completed": list(recent_completed.values(
                'id', 'titulo', 'tipo', 'completed_at', 'assigned_to__username'
            )),
            "summary": {
                "total_pending": pending_tasks.count(),
                "total_in_progress": in_progress_tasks.count(),
                "total_overdue": overdue_tasks.count(),
                "total_upcoming": upcoming_tasks.count(),
                "total_recent_completed": recent_completed.count(),
            }
        }

    def get_authentication_queue(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get pending authentication tasks."""
        auth_tasks = WorkflowTask.objects.filter(
            tenant_id=tenant_id,
            tipo="autenticacao",
            status__in=["pendente", "em_andamento"]
        ).order_by("-prioridade", "deadline")

        return list(auth_tasks.values(
            'id', 'titulo', 'descricao', 'prioridade', 'deadline', 
            'assigned_to__username', 'created_at', 'metadata'
        ))

    def get_signature_queue(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get pending signature tasks."""
        signature_tasks = WorkflowTask.objects.filter(
            tenant_id=tenant_id,
            tipo="assinatura",
            status__in=["pendente", "em_andamento"]
        ).order_by("-prioridade", "deadline")

        return list(signature_tasks.values(
            'id', 'titulo', 'descricao', 'prioridade', 'deadline',
            'assigned_to__username', 'created_at', 'metadata'
        ))

    def get_review_queue(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get pending review tasks."""
        review_tasks = WorkflowTask.objects.filter(
            tenant_id=tenant_id,
            tipo="revisao",
            status__in=["pendente", "em_andamento"]
        ).order_by("-prioridade", "deadline")

        return list(review_tasks.values(
            'id', 'titulo', 'descricao', 'prioridade', 'deadline',
            'assigned_to__username', 'created_at', 'metadata'
        ))

    def create_authentication_task(
        self,
        documento: Documento,
        tenant_id: str,
        created_by: User,
        assigned_to: User = None,
        deadline: datetime = None
    ) -> WorkflowTask:
        """Create an authentication task for a document."""
        return self.create_task(
            titulo=f"Autenticar {documento.tipo}",
            descricao=f"Autenticar documento {documento.tipo} - ID: {documento.id}",
            tipo="autenticacao",
            tenant_id=tenant_id,
            created_by=created_by,
            prioridade="media",
            assigned_to=assigned_to,
            deadline=deadline,
            documento=documento,
            metadata={"documento_id": str(documento.id)}
        )

    def create_signature_task(
        self,
        minuta: Minuta,
        tenant_id: str,
        created_by: User,
        assigned_to: User = None,
        deadline: datetime = None
    ) -> WorkflowTask:
        """Create a signature task for a minuta."""
        return self.create_task(
            titulo=f"Assinar {minuta.processo.tipo_ato if minuta.processo else 'Documento'}",
            descricao=f"Assinar minuta versão {minuta.versao} - ID: {minuta.id}",
            tipo="assinatura",
            tenant_id=tenant_id,
            created_by=created_by,
            prioridade="alta",
            assigned_to=assigned_to,
            deadline=deadline,
            minuta=minuta,
            metadata={"minuta_id": str(minuta.id), "versao": minuta.versao}
        )

    def create_review_task(
        self,
        minuta: Minuta,
        tenant_id: str,
        created_by: User,
        assigned_to: User = None,
        deadline: datetime = None
    ) -> WorkflowTask:
        """Create a review task for a minuta."""
        return self.create_task(
            titulo=f"Revisar {minuta.processo.tipo_ato if minuta.processo else 'Documento'}",
            descricao=f"Revisar minuta versão {minuta.versao} - ID: {minuta.id}",
            tipo="revisao",
            tenant_id=tenant_id,
            created_by=created_by,
            prioridade="media",
            assigned_to=assigned_to,
            deadline=deadline,
            minuta=minuta,
            metadata={"minuta_id": str(minuta.id), "versao": minuta.versao}
        )

    def check_deadlines(self, tenant_id: str) -> List[WorkflowTask]:
        """Check for approaching deadlines and send notifications."""
        # Tasks with deadlines in the next 24 hours
        upcoming_deadline = timezone.now() + timedelta(hours=24)
        
        approaching_tasks = WorkflowTask.objects.filter(
            tenant_id=tenant_id,
            status__in=["pendente", "em_andamento"],
            deadline__lte=upcoming_deadline,
            deadline__gt=timezone.now()
        )

        for task in approaching_tasks:
            if task.assigned_to and task.assigned_to.email:
                try:
                    self.notification_service.send_deadline_reminder_notification(
                        task=task,
                        recipient_email=task.assigned_to.email,
                        recipient_name=task.assigned_to.get_full_name() or task.assigned_to.username
                    )
                except Exception as e:
                    print(f"Failed to send deadline reminder: {e}")

        return list(approaching_tasks)
