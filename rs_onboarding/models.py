from django.db import models
from simple_history.models import HistoricalRecords


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


class Client(models.Model):
    

    id = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=255)
    clinical_system = models.CharField(max_length=64, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ClientRuleConfig(models.Model):

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="rule_configs")
    rule = models.ForeignKey(Rule, on_delete=models.PROTECT, related_name="client_configs")
    is_enabled = models.BooleanField(default=False)
    values = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["client", "rule"], name="unique_client_rule")
        ]

    def __str__(self):
        return f"{self.client} · {self.rule} ({'on' if self.is_enabled else 'off'})"