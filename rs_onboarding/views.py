from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Client, ClientRuleConfig, Rule
from .serializers import (
    ClientRuleConfigHistorySerializer,
    ClientRuleConfigSerializer,
    ClientSerializer,
    RuleSerializer,
)


class RuleViewSet(viewsets.ModelViewSet):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer


class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def _get_default_values_for_rule(self, rule, client):
        schema = rule.field_schema or {}
        fields = schema.get("fields", [])
        values = {}

        for fld in fields:
            field_key = fld.get("fieldKey")
            default_val = fld.get("defaultValue")
            if field_key and default_val is not None:
                values[field_key] = default_val

        # Specific client-aware defaults
        if rule.key == "dispensingPharmacy":
            values["source"] = "patientDetails"
            values["pharmacyName"] = f"{client.name} Pharmacy"
        elif rule.key == "proactiveTaskForIssueAuthorization":
            values["route"] = "Team"
            values["assignment"] = f"{client.name} Team"
            values["taskType"] = "Medication Review"
        elif rule.key == "proactiveTaskMedicationReview":
            values["route"] = "Team"
            values["assignment"] = f"{client.name} Clinical Team"
            values["taskType"] = "Medication Review"
        elif rule.key == "doctorOrGroup":
            values["mode"] = "combined"
            values["singleDateEntries"] = [
                {"id": "sd_1", "date": "2026-10-05", "doctor": "Dr. Ali Khan"}
            ]
            values["dateRangeEntries"] = [
                {
                    "id": "dr_1",
                    "startDate": "2026-10-01",
                    "endDate": "2026-10-07",
                    "doctor": "Dr. Faisal Ahmed",
                }
            ]

        return values

    def perform_create(self, serializer):
        client = serializer.save()
        active_rules = Rule.objects.filter(is_active=True).order_by("display_order")
        configs = []
        for rule in active_rules:
            is_enabled = rule.key != "sendRepeatDispensingAsLogicAction"
            default_vals = self._get_default_values_for_rule(rule, client)
            configs.append(
                ClientRuleConfig(
                    client=client,
                    rule=rule,
                    is_enabled=is_enabled,
                    values=default_vals,
                )
            )
        ClientRuleConfig.objects.bulk_create(configs)

    @action(detail=True, methods=["get"], url_path="config")
    def config(self, request, pk=None):
        client = self.get_object()
        existing = {
            rc.rule_id: rc
            for rc in ClientRuleConfig.objects.filter(client=client).select_related("rule")
        }

        # If this client has no configs in DB (e.g. created before seeder/perform_create), auto-populate them
        if not existing:
            active_rules = Rule.objects.filter(is_active=True).order_by("display_order")
            new_configs = []
            for rule in active_rules:
                is_enabled = rule.key != "sendRepeatDispensingAsLogicAction"
                default_vals = self._get_default_values_for_rule(rule, client)
                new_configs.append(
                    ClientRuleConfig(
                        client=client,
                        rule=rule,
                        is_enabled=is_enabled,
                        values=default_vals,
                    )
                )
            ClientRuleConfig.objects.bulk_create(new_configs)
            existing = {
                rc.rule_id: rc
                for rc in ClientRuleConfig.objects.filter(client=client).select_related("rule")
            }

        rules_payload = []
        for rule in Rule.objects.filter(is_active=True).order_by("display_order"):
            config = existing.get(rule.key)
            rules_payload.append(
                {
                    "key": rule.key,
                    "name": rule.name,
                    "description": rule.description,
                    "category": rule.category,
                    "field_schema": rule.field_schema,
                    "config": {
                        "id": config.id if config else None,
                        "is_enabled": config.is_enabled if config else False,
                        "values": config.values if config else {},
                    },
                }
            )

        return Response({"client": ClientSerializer(client).data, "rules": rules_payload})

    @action(detail=True, methods=["post"], url_path="bulk-config")
    def bulk_config(self, request, pk=None):
        client = self.get_object()
        items = request.data.get("configs")
        if not isinstance(items, list) or not items:
            return Response(
                {"configs": "Provide a non-empty list of config items."}, status=400
            )

        results = []
        errors = []
        with transaction.atomic():
            for idx, item in enumerate(items):
                payload = {
                    "client": client.id,
                    "rule": item.get("rule"),
                    "is_enabled": item.get("is_enabled", False),
                    "values": item.get("values", {}),
                }
                instance = ClientRuleConfig.objects.filter(
                    client=client, rule_id=payload["rule"]
                ).first()
                serializer = ClientRuleConfigSerializer(instance=instance, data=payload)
                if not serializer.is_valid():
                    errors.append(
                        {"index": idx, "rule": payload["rule"], "errors": serializer.errors}
                    )
                    continue
                saved = serializer.save()
                results.append(ClientRuleConfigSerializer(saved).data)

            if errors:
                transaction.set_rollback(True)
                return Response({"errors": errors}, status=400)

        return Response({"updated": results}, status=200)


class ClientRuleConfigViewSet(viewsets.ModelViewSet):
    queryset = ClientRuleConfig.objects.select_related("client", "rule").all()
    serializer_class = ClientRuleConfigSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        client_id = self.request.query_params.get("client")
        rule_key = self.request.query_params.get("rule")
        if client_id:
            qs = qs.filter(client_id=client_id)
        if rule_key:
            qs = qs.filter(rule_id=rule_key)
        return qs

    @action(detail=True, methods=["get"], url_path="history")
    def history(self, request, pk=None):
        config = get_object_or_404(ClientRuleConfig, pk=pk)
        records = config.history.all().order_by("-history_date")
        return Response(ClientRuleConfigHistorySerializer(records, many=True).data)
