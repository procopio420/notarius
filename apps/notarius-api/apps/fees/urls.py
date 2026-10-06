"""
Fee URLs.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('calculate-fees/', views.calculate_fees, name='calculate-fees'),
]

