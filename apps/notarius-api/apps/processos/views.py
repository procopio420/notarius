from django_filters import rest_framework as df_filters
from rest_framework import filters

from apps.base.views import BaseTenantViewSet

from .models import Processo, ProcessoParte, Protocolo
from .serializers import ProcessoParteSerializer, ProcessoSerializer, ProtocoloSerializer


class ProcessoFilter(df_filters.FilterSet):
    tipo_ato = df_filters.CharFilter(field_name="tipo_ato", lookup_expr="icontains")
    status = df_filters.CharFilter(field_name="status", lookup_expr="iexact")

    class Meta:
        model = Processo
        fields = ["tipo_ato", "status", "responsavel"]


class ProcessoViewSet(BaseTenantViewSet):
    queryset = Processo.objects.all().order_by("-created_at")
    serializer_class = ProcessoSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProcessoFilter
    search_fields = ["tipo_ato", "id"]
    ordering_fields = ["created_at", "updated_at", "sla_at"]


class ProcessoParteViewSet(BaseTenantViewSet):
    queryset = ProcessoParte.objects.all().order_by("-created_at")
    serializer_class = ProcessoParteSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["processo", "papel", "parte"]
    search_fields = ["processo__id", "parte__nome"]
    ordering_fields = ["created_at", "updated_at"]


class ProtocoloViewSet(BaseTenantViewSet):
    queryset = Protocolo.objects.all().order_by("-ano", "-numero")
    serializer_class = ProtocoloSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["ano", "tipo", "processo"]
    search_fields = ["numero", "processo__id"]
    ordering_fields = ["ano", "numero", "created_at"]
