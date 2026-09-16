from rest_framework import serializers

from .models import InstanceRuleConfig, Rule


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule
        fields = ["key", "name", "description", "category", "display_order", "is_active", "field_schema"]


class InstanceRuleConfigSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(source="rule.name", read_only=True)

    class Meta:
        model = InstanceRuleConfig
        fields = ["id", "instance", "rule", "rule_name", "is_enabled", "values", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, attrs):
        """
        Unchanged from before — this is the doctorOrGroup mode-normalization and the
        hasType/hasValue schema checks. Left in place since it's real validation logic,
        not the hardcoded default-value stuff you asked to remove. Say the word if you
        want this stripped too.
        """
        rule = attrs.get("rule") or getattr(self.instance, "rule", None)
        values = attrs.get("values")
        if rule and values is not None:
            rule_key = getattr(rule, "key", str(rule))
            if rule_key == "doctorOrGroup":
                mode = values.get("mode")
                is_schedule = (
                    mode in ["schedule", "combined", "single_date", "date_range"]
                    or (bool(values.get("singleDateEntries")) and mode != "fixed")
                    or (bool(values.get("dateRangeEntries")) and mode != "fixed")
                    or (
                        bool(values.get("date") or values.get("startDate"))
                        and mode != "fixed"
                        and not values.get("defaultDoctor")
                    )
                )
                if is_schedule:
                    values.pop("defaultDoctor", None)
                    values.pop("name", None)
                    has_single = bool(values.get("singleDateEntries")) or bool(values.get("date"))
                    has_range = bool(values.get("dateRangeEntries")) or bool(values.get("startDate"))
                    if has_single and has_range:
                        values["mode"] = "combined"
                    elif has_single:
                        values["mode"] = "single_date"
                    elif has_range:
                        values["mode"] = "date_range"
                    else:
                        values["mode"] = "schedule"
                else:
                    values["mode"] = "fixed"
                    values.pop("singleDateEntries", None)
                    values.pop("dateRangeEntries", None)
                    values.pop("date", None)
                    values.pop("startDate", None)
                    values.pop("endDate", None)

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

