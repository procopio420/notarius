# apps/base/admin_mixins.py
from django.contrib import admin
from django.forms.widgets import HiddenInput

from apps.tenancy.tenancy import get_current_tenant


class BaseTenantAdmin(admin.ModelAdmin):
    list_filter = ("tenant",)
    autocomplete_fields = ("tenant",)
    tenant_field_name = "tenant"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        tenant = getattr(request, "tenant", None) or get_current_tenant()
        if tenant and not request.user.is_superuser:
            return qs.filter(**{self.tenant_field_name: tenant})
        return qs

    def get_form(
        self,
        request,
        obj=None,
        change=False,
        **kwargs,
    ):
        form = super().get_form(request, obj, change=change, **kwargs)
        if not request.user.is_superuser and self.tenant_field_name in form.base_fields:
            form.base_fields[self.tenant_field_name].widget = HiddenInput()
        return form

    def save_model(self, request, obj, form, change) -> None:
        tenant = getattr(request, "tenant", None) or get_current_tenant()

        if tenant and (
            not request.user.is_superuser or getattr(obj, self.tenant_field_name, None) is None
        ):
            setattr(obj, self.tenant_field_name, tenant)

        super().save_model(request, obj, form, change)
