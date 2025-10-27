from django_filters import rest_framework as df_filters
from rest_framework import filters

from apps.base.views import BaseTenantViewSet

from .models import Parte
from .serializers import ParteSerializer


class ParteFilter(df_filters.FilterSet):
    tipo = df_filters.CharFilter(field_name="tipo", lookup_expr="iexact")
    nome = df_filters.CharFilter(field_name="nome_normalizado", lookup_expr="icontains")

    class Meta:
        model = Parte
        fields = ["tipo", "nome"]


class ParteViewSet(BaseTenantViewSet):
    queryset = Parte.objects.all().order_by("-created_at")
    serializer_class = ParteSerializer
    filter_backends = [df_filters.DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ParteFilter
    search_fields = ["nome", "nome_normalizado"]
    ordering_fields = ["created_at", "updated_at", "nome_normalizado"]
