from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response

from .models import GPInst, InstanceRuleConfig, Rule
from .serializers import (
    GPInstSerializer,
    InstanceRuleConfigSerializer,
    RuleSerializer,
)


class RuleViewSet(viewsets.ModelViewSet):
    queryset = Rule.objects.all()
    serializer_class = RuleSerializer


class InstanceConfigViewSet(viewsets.GenericViewSet):
    """
    GPInst endpoints.

    GPInst itself is owned/created by automation_app.
    This viewset provides:
        - GP instance listing/filtering
        - config endpoint
        - bulk-config endpoint
    """

    queryset = GPInst.objects.all()
    lookup_field = "inst_id"
    lookup_url_kwarg = "inst_id"

    def list(self, request):

        queryset = self.get_queryset()

        # Filter by GPEntity ID
        entity_id = request.query_params.get("entity")

        if entity_id is not None:
            try:
                entity_id = int(entity_id)
            except (TypeError, ValueError):
                return Response(
                    {"entity": "entity must be a valid integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if entity_id <= 0:
                return Response(
                    {"entity": "entity must be a positive integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            queryset = queryset.filter(entity_id=entity_id)

        # Filter by GPInst primary key
        instance_id = request.query_params.get("instance")

        if instance_id is not None:
            try:
                instance_id = int(instance_id)
            except (TypeError, ValueError):
                return Response(
                    {"instance": "instance must be a valid integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if instance_id <= 0:
                return Response(
                    {"instance": "instance must be a positive integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            queryset = queryset.filter(pk=instance_id)

        # Limit returned entries
        entries = request.query_params.get("entries")

        if entries is not None:
            try:
                entries = int(entries)
            except (TypeError, ValueError):
                return Response(
                    {"entries": "entries must be a valid integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if entries <= 0:
                return Response(
                    {"entries": "entries must be greater than 0."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            queryset = queryset[:entries]

        serializer = GPInstSerializer(queryset, many=True)

        return Response(serializer.data)

    def config(self, request, inst_id=None):
        """
        GET /gp-insts/<inst_id>/config/
        """

        instance = self.get_object()

        existing = {
            rc.rule_id: rc
            for rc in InstanceRuleConfig.objects.filter(
                instance=instance
            ).select_related("rule")
        }

        rules_payload = []

        for rule in Rule.objects.filter(
            is_active=True
        ).order_by("display_order"):

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
                        "is_enabled": (
                            config.is_enabled
                            if config
                            else True
                        ),
                        "values": (
                            config.values
                            if config
                            else rule.default_values()
                        ),
                    },
                }
            )

        return Response(
            {
                "instance": {
                    "inst_id": instance.inst_id,
                    "name": instance.name,
                },
                "rules": rules_payload,
            }
        )

    def bulk_config(self, request, inst_id=None):
        """
        POST /instances/<inst_id>/bulk_config/
        """

        instance = self.get_object()

        items = request.data.get("configs")

        if not isinstance(items, list) or not items:
            return Response(
                {
                    "configs": (
                        "Provide a non-empty list of config items."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        results = []
        errors = []

        with transaction.atomic():

            for idx, item in enumerate(items):

                if not isinstance(item, dict):
                    errors.append(
                        {
                            "index": idx,
                            "errors": "Each config item must be an object.",
                        }
                    )
                    continue

                payload = {
                    "rule": item.get("rule"),
                    "is_enabled": item.get(
                        "is_enabled",
                        True,
                    ),
                    "system_type": item.get("system_type"),
                    "values": item.get(
                        "values",
                        {},
                    ),
                }

                existing_config = (
                    InstanceRuleConfig.objects.filter(
                        instance=instance,
                        rule_id=payload["rule"],
                    ).first()
                )

                serializer = InstanceRuleConfigSerializer(
                    instance=existing_config,
                    data=payload,
                )

                if not serializer.is_valid():

                    errors.append(
                        {
                            "index": idx,
                            "rule": payload["rule"],
                            "errors": serializer.errors,
                        }
                    )

                    continue

                saved = serializer.save(instance=instance)

                results.append(
                    InstanceRuleConfigSerializer(saved).data
                )

            if errors:
                transaction.set_rollback(True)

                return Response(
                    {"errors": errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {"updated": results},
            status=status.HTTP_200_OK,
        )


class InstanceRuleConfigViewSet(viewsets.ModelViewSet):
    queryset = (
        InstanceRuleConfig.objects
        .select_related("instance", "rule")
        .all()
    )

    serializer_class = InstanceRuleConfigSerializer

    def get_queryset(self):
        qs = super().get_queryset()

        inst_id = self.kwargs.get("inst_id")
        rule_key = self.request.query_params.get("rule")

        if inst_id:
            qs = qs.filter(instance__inst_id=inst_id)

        if rule_key:
            qs = qs.filter(rule_id=rule_key)

        return qs

    def _get_instance(self):
        return get_object_or_404(
            GPInst,
            inst_id=self.kwargs.get("inst_id"),
        )

    def perform_create(self, serializer):
        serializer.save(instance=self._get_instance())

    def perform_update(self, serializer):
        serializer.save(instance=self._get_instance())