"""Expose only the existing local atendimento workflow and account access."""
from django.http import HttpResponse
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.processos.views import AtendimentoViewSet
from apps.authentication import views

router = DefaultRouter()
router.register('atendimentos', AtendimentoViewSet, basename='atendimento')
urlpatterns = [path('health/', lambda request: HttpResponse('OK')),
               path('api/v1/', include(router.urls))]
for route, view in [('login', views.login_view), ('logout', views.logout_view),
                    ('me', views.me_view), ('tenants', views.user_tenants_view),
                    ('set-default-tenant', views.set_default_tenant_view)]:
    urlpatterns.append(path(f'api/v1/auth/{route}/', view))
