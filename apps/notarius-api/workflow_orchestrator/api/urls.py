"""
URL configuration for workflow orchestrator API.
"""

from django.urls import path
from . import views

urlpatterns = [
    path("route/", views.route_workflow, name="workflow-route"),
    path("rulepacks/", views.get_rulepacks, name="workflow-rulepacks"),
]

