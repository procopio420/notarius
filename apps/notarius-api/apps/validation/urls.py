"""
Validation URLs.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('validate-document/', views.validate_document, name='validate-document'),
]

