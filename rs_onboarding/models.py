from django.db import models
from simple_history.models import HistoricalRecords
class GPEntity(models.Model):
    name = models.CharField(max_length=250, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f'{self.name}'
    
class GPInst(models.Model):
    entity = models.ForeignKey(GPEntity, on_delete=models.SET_NULL, null=True, related_name='instances')    
    name = models.CharField(max_length=255, null=True, unique=True)
    inst_id = models.CharField(max_length=35, null=True, blank=True, unique=True)
    address = models.CharField(max_length=255, null=True, blank=True, unique=True)
    recepient_address = models.CharField(max_length=255, null=True, blank=True, unique=True)
    is_active_for_ltc = models.BooleanField(default=False)
    is_active_outlook_notifications = models.BooleanField(default=False)
    inst_order = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name}'

class Rule(models.Model):
    key = models.CharField(max_length=64, primary_key=True)  # e.g. "etpCheck"
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=64)  # "timing", "safety", "comments"...
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)  # soft-disable in the catalog
    field_schema = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "display_order"]

    def __str__(self):
        return self.name

    def default_values(self):
        """Build {fieldKey: defaultValue} straight from field_schema. No per-rule special cases."""
        fields = (self.field_schema or {}).get("fields", [])
        values = {}
        for fld in fields:
            field_key = fld.get("fieldKey")
            default_val = fld.get("defaultValue")
            if field_key and default_val is not None:
                values[field_key] = default_val
        return values


class InstanceRuleConfig(models.Model):
    instance = models.ForeignKey(
        GPInst,
        on_delete=models.CASCADE,
        related_name="rule_configs",
    )
    rule = models.ForeignKey(
        Rule,
        on_delete=models.PROTECT,
        related_name="instance_configs",
    )
    is_enabled = models.BooleanField(default=True)
    values = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["instance", "rule"],
                name="unique_instance_rule",
            )
        ]