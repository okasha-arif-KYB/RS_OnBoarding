from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import GPInst

from .models import InstanceRuleConfig, Rule
from .serializers import (
    InstanceRuleConfigSerializer,
    RuleSerializer,
)


class RuleViewSet(viewsets.ModelViewSet):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer


class GPInstConfigViewSet(viewsets.GenericViewSet):
    """
    Read-only access to GPInst, purely to hang the config/bulk-config actions off
    /gp-insts/<inst_id>/... . GPInst itself is owned/created by automation_app.
    """
    queryset = GPInst.objects.all()
    lookup_field = "inst_id"
    lookup_url_kwarg = "inst_id"

    @action(detail=True, methods=["get"], url_path="config")
    def config(self, request, inst_id=None):
        gp_inst = self.get_object()
        existing = {
            rc.rule_id: rc
            for rc in InstanceRuleConfig.objects.filter(instance=gp_inst).select_related("rule")
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
                        "is_enabled": config.is_enabled if config else True,
                        "values": config.values if config else rule.default_values(),
                    },
                }
            )

        return Response(
            {"instance": {"inst_id": gp_inst.inst_id, "name": gp_inst.name}, "rules": rules_payload}
        )

    @action(detail=True, methods=["post"], url_path="bulk-config")
    def bulk_config(self, request, inst_id=None):
        gp_inst = self.get_object()
        items = request.data.get("configs")
        if not isinstance(items, list) or not items:
            return Response({"configs": "Provide a non-empty list of config items."}, status=400)

        results = []
        errors = []
        with transaction.atomic():
            for idx, item in enumerate(items):
                payload = {
                    "instance": gp_inst.pk,
                    "rule": item.get("rule"),
                    "is_enabled": item.get("is_enabled", True),
                    "values": item.get("values", {}),
                }
                existing_config = InstanceRuleConfig.objects.filter(
                    instance=gp_inst, rule_id=payload["rule"]
                ).first()
                serializer = InstanceRuleConfigSerializer(instance=existing_config, data=payload)
                if not serializer.is_valid():
                    errors.append({"index": idx, "rule": payload["rule"], "errors": serializer.errors})
                    continue
                saved = serializer.save()
                results.append(InstanceRuleConfigSerializer(saved).data)

            if errors:
                transaction.set_rollback(True)
                return Response({"errors": errors}, status=400)

        return Response({"updated": results}, status=200)


class InstanceRuleConfigViewSet(viewsets.ModelViewSet):
    queryset = InstanceRuleConfig.objects.select_related("instance", "rule").all()
    serializer_class = InstanceRuleConfigSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        inst_id = self.request.query_params.get("instance")
        rule_key = self.request.query_params.get("rule")
        if inst_id:
            qs = qs.filter(instance__inst_id=inst_id)
        if rule_key:
            qs = qs.filter(rule_id=rule_key)
        return qs

