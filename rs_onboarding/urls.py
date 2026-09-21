from django.urls import path

from .views import (
    InstanceConfigViewSet,
    InstanceRuleConfigViewSet,
    RuleViewSet,
)


# ---------------------------------------------------------
# ViewSet instances
# ---------------------------------------------------------

instance_bulk_config = InstanceConfigViewSet.as_view(
    {
        "post": "bulk_config",
    }
)


instance_config = InstanceConfigViewSet.as_view(
    {
        "get": "config",
    }
)


instance_list = InstanceConfigViewSet.as_view(
    {
        "get": "list",
    }
)


instance_rule_config_detail = (
    InstanceRuleConfigViewSet.as_view(
        {
            "get": "retrieve",
            "put": "update",
            "patch": "partial_update",
            "delete": "destroy",
        }
    )
)


instance_rule_config_list = (
    InstanceRuleConfigViewSet.as_view(
        {
            "get": "list",
            "post": "create",
        }
    )
)


rule_detail = RuleViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }
)


rule_list = RuleViewSet.as_view(
    {
        "get": "list",
        "post": "create",
    }
)


urlpatterns = [

    # -----------------------------------------------------
    # Instances
    # -----------------------------------------------------

    path(
        "instances/",
        instance_list,
        name="instance_list",
    ),

    # Example:
    # POST /instances/ABC001/bulk_config/

    path(
        "instances/<str:inst_id>/bulk_config/",
        instance_bulk_config,
        name="instance_bulk_config",
    ),

    # Example:
    # GET /instances/ABC001/config/

    path(
        "instances/<str:inst_id>/config/",
        instance_config,
        name="instance_config",
    ),

    # Rule configs nested under their instance.
    # Example:
    # GET  /instances/ABC001/rule_configs/
    # POST /instances/ABC001/rule_configs/

    path(
        "instances/<str:inst_id>/rule_configs/",
        instance_rule_config_list,
        name="instance_rule_config_list",
    ),

    # Example:
    # GET/PUT/PATCH/DELETE /instances/ABC001/rule_configs/7/

    path(
        "instances/<str:inst_id>/rule_configs/<int:pk>/",
        instance_rule_config_detail,
        name="instance_rule_config_detail",
    ),

    # -----------------------------------------------------
    # Rules
    # -----------------------------------------------------

    path(
        "rules/",
        rule_list,
        name="rule_list",
    ),

    path(
        "rules/<str:pk>/",
        rule_detail,
        name="rule_detail",
    ),
]