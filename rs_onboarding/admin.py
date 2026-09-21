from django.contrib import admin

from .models import GPEntity, GPInst, InstanceRuleConfig, Rule


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "category", "rule_type", "display_order", "is_active")
    list_filter = ("category", "rule_type", "is_active")
    search_fields = ("key", "name")


@admin.register(InstanceRuleConfig)
class InstanceRuleConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "instance", "rule", "system_type", "is_enabled")
    list_filter = ("is_enabled", "system_type", "rule")
    search_fields = ("instance__name", "instance__inst_id", "rule__key")