from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('me/', views.me_view, name='me'),
    path('tenants/', views.user_tenants_view, name='user-tenants'),
    path('set-default-tenant/', views.set_default_tenant_view, name='set-default-tenant'),
    path('manage-user-tenants/', views.manage_user_tenants_view, name='manage-user-tenants'),
]
