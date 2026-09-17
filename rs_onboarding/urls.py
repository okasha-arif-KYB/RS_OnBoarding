from django.urls import path

from .views import (
    GPInstConfigViewSet,
    InstanceRuleConfigViewSet,
    RuleViewSet,
)


# ---------------------------------------------------------
# ViewSet instances
# ---------------------------------------------------------

rule_list = RuleViewSet.as_view(
    {
        "get": "list",
        "post": "create",
    }
)

rule_detail = RuleViewSet.as_view(
    {
        "get": "retrieve",
        "put": "update",
        "patch": "partial_update",
        "delete": "destroy",
    }
)


gp_inst_list = GPInstConfigViewSet.as_view(
    {
        "get": "list",
    }
)


gp_inst_config = GPInstConfigViewSet.as_view(
    {
        "get": "config",
    }
)


gp_inst_bulk_config = GPInstConfigViewSet.as_view(
    {
        "post": "bulk_config",
    }
)


instance_rule_config_list = (
    InstanceRuleConfigViewSet.as_view(
        {
            "get": "list",
            "post": "create",
        }
    )
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


urlpatterns = [

    # -----------------------------------------------------
    # Rules
    # -----------------------------------------------------

    path(
        "rules/",
        rule_list,
        name="rule-list",
    ),

    path(
        "rules/<str:pk>/",
        rule_detail,
        name="rule-detail",
    ),

    # -----------------------------------------------------
    # GP Instances
    # -----------------------------------------------------

    path(
        "gp-insts/",
        gp_inst_list,
        name="gp-inst-list",
    ),

    # Example:
    # GET /gp-insts/ABC001/config/

    path(
        "gp-insts/<str:inst_id>/config/",
        gp_inst_config,
        name="gp-inst-config",
    ),

    # Example:
    # POST /gp-insts/ABC001/bulk-config/

    path(
        "gp-insts/<str:inst_id>/bulk-config/",
        gp_inst_bulk_config,
        name="gp-inst-bulk-config",
    ),

    # -----------------------------------------------------
    # Individual Instance Rule Configs
    # -----------------------------------------------------

    path(
        "instance-rule-configs/",
        instance_rule_config_list,
        name="instance-rule-config-list",
    ),

    path(
        "instance-rule-configs/<int:pk>/",
        instance_rule_config_detail,
        name="instance-rule-config-detail",
    ),
]