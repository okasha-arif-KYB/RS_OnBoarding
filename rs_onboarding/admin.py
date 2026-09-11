from django.contrib import admin

from .models import Client, ClientRuleConfig, Rule


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("name", "key", "category", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("name", "key")


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "clinical_system", "is_active", "created_at")
    search_fields = ("id", "name")


@admin.register(ClientRuleConfig)
class ClientRuleConfigAdmin(admin.ModelAdmin):
    list_display = ("client", "rule", "is_enabled", "updated_at")
    list_filter = ("is_enabled", "rule__category")
    search_fields = ("client__name", "rule__name")