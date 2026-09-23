from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GPInst, InstanceRuleConfig, Rule
from .serializers import (
    GPInstSerializer,
    InstanceRuleConfigSerializer,
    RuleSerializer,
)

from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
# ===========================================================
# Rules (global catalog, not user-scoped)
# ===========================================================

class RuleListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        rules = Rule.objects.all()
        serializer = RuleSerializer(rules, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = RuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RuleDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Rule, pk=pk)

    def get(self, request, pk):
        rule = self.get_object(pk)
        return Response(RuleSerializer(rule).data)

    def put(self, request, pk):
        rule = self.get_object(pk)
        serializer = RuleSerializer(rule, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        rule = self.get_object(pk)
        serializer = RuleSerializer(rule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        rule = self.get_object(pk)
        rule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ===========================================================
# Instances (scoped to request.user.instances)
# ===========================================================

class InstanceListAPIView(APIView):
    """
    GET /instances/

    Only instances linked to the authenticated user are returned.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = request.user.instances.all()

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


class InstanceConfigAPIView(APIView):
    """
    GET /instances/<inst_id>/config/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, inst_id=None):
        instance = get_object_or_404(request.user.instances, inst_id=inst_id)

        existing = {
            rc.rule_id: rc
            for rc in InstanceRuleConfig.objects.filter(
                instance=instance
            ).select_related("rule")
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
            {
                "instance": {
                    "inst_id": instance.inst_id,
                    "name": instance.name,
                },
                "rules": rules_payload,
            }
        )


class InstanceBulkConfigAPIView(APIView):
    """
    POST /instances/<inst_id>/bulk_config/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, inst_id=None):
        instance = get_object_or_404(request.user.instances, inst_id=inst_id)

        items = request.data.get("configs")

        if not isinstance(items, list) or not items:
            return Response(
                {"configs": "Provide a non-empty list of config items."},
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
                    "is_enabled": item.get("is_enabled", True),
                    "system_type": item.get("system_type"),
                    "values": item.get("values", {}),
                }

                existing_config = InstanceRuleConfig.objects.filter(
                    instance=instance,
                    rule_id=payload["rule"],
                ).first()

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
                results.append(InstanceRuleConfigSerializer(saved).data)

            if errors:
                transaction.set_rollback(True)
                return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"updated": results}, status=status.HTTP_200_OK)


# ===========================================================
# InstanceRuleConfig, nested under a user-owned instance
# ===========================================================

class InstanceRuleConfigListCreateAPIView(APIView):
    """
    GET  /instances/<inst_id>/rule_configs/
    POST /instances/<inst_id>/rule_configs/
    """
    permission_classes = [IsAuthenticated]

    def get_instance(self, request, inst_id):
        return get_object_or_404(request.user.instances, inst_id=inst_id)

    def get(self, request, inst_id):
        instance = self.get_instance(request, inst_id)

        qs = InstanceRuleConfig.objects.select_related("instance", "rule").filter(
            instance=instance
        )

        rule_key = request.query_params.get("rule")
        if rule_key:
            qs = qs.filter(rule_id=rule_key)

        system_type = request.query_params.get("system_type")
        if system_type:
            qs = qs.filter(system_type=system_type)

        serializer = InstanceRuleConfigSerializer(qs, many=True)
        return Response(serializer.data)

    def post(self, request, inst_id):
        instance = self.get_instance(request, inst_id)

        serializer = InstanceRuleConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(instance=instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class InstanceRuleConfigDetailAPIView(APIView):
    """
    GET/PUT/PATCH/DELETE /instances/<inst_id>/rule_configs/<pk>/
    """
    permission_classes = [IsAuthenticated]

    def get_instance(self, request, inst_id):
        return get_object_or_404(request.user.instances, inst_id=inst_id)

    def get_object(self, request, inst_id, pk):
        instance = self.get_instance(request, inst_id)
        return get_object_or_404(
            InstanceRuleConfig.objects.select_related("instance", "rule"),
            pk=pk,
            instance=instance,
        )

    def get(self, request, inst_id, pk):
        obj = self.get_object(request, inst_id, pk)
        return Response(InstanceRuleConfigSerializer(obj).data)

    def put(self, request, inst_id, pk):
        obj = self.get_object(request, inst_id, pk)
        instance = self.get_instance(request, inst_id)
        serializer = InstanceRuleConfigSerializer(obj, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(instance=instance)
        return Response(serializer.data)

    def patch(self, request, inst_id, pk):
        obj = self.get_object(request, inst_id, pk)
        instance = self.get_instance(request, inst_id)
        serializer = InstanceRuleConfigSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(instance=instance)
        return Response(serializer.data)

    def delete(self, request, inst_id, pk):
        obj = self.get_object(request, inst_id, pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class LoginAPIView(APIView):
    """
    POST /api/login/
    Body: {"email": "...", "password": "..."}
    Returns: {"token": "..."}
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"detail": "email and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(request, username=email, password=password)

        if user is None:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "email": user.email})