from rest_framework import serializers

from .models import Client, ClientRuleConfig, Rule


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = [
            "key", "name", "description", "category",
            "display_order", "is_active", "field_schema",
        ]


class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ["id", "name", "clinical_system", "is_active", "created_at", "updated_at"]


class ClientRuleConfigSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source="rule.name", read_only=True)

    class Meta:
        model = ClientRuleConfig
        fields = [
            "id", "client", "rule", "rule_name", "is_enabled", "values",
            "created_at", "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        """
        Validates `values` against the rule's field_schema, using the
        standard key convention:
          hasValue -> "value" (must be numeric)
          hasType  -> "type"  (must be one of typeOptions)
        """
        rule = attrs.get("rule") or getattr(self.instance, "rule", None)
        values = attrs.get("values")
        if rule and values is not None:
            schema = rule.field_schema or {}

            if schema.get("hasType") and "type" in values:
                allowed = schema.get("typeOptions", [])
                if allowed and values["type"] not in allowed:
                    raise serializers.ValidationError(
                        {"values": f"'type' must be one of {allowed} for rule '{rule.key}'."}
                    )

            if schema.get("hasValue") and "value" in values:
                if not isinstance(values["value"], (int, float)):
                    raise serializers.ValidationError(
                        {"values": f"'value' must be numeric for rule '{rule.key}'."}
                    )
        return attrs


class BulkClientRuleConfigItemSerializer(serializers.Serializer):
    """One item inside a bulk-config request body."""
    rule = serializers.PrimaryKeyRelatedField(queryset=Rule.objects.all())
    is_enabled = serializers.BooleanField(default=False)
    values = serializers.JSONField(default=dict)


class ClientRuleConfigHistorySerializer(serializers.Serializer):
    history_id = serializers.IntegerField()
    history_date = serializers.DateTimeField()
    history_type = serializers.CharField()
    is_enabled = serializers.BooleanField()
    values = serializers.JSONField()