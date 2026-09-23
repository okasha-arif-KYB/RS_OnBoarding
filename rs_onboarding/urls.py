from django.urls import path

from .views import (
    InstanceBulkConfigAPIView,
    InstanceConfigAPIView,
    InstanceListAPIView,
    InstanceRuleConfigDetailAPIView,
    InstanceRuleConfigListCreateAPIView,
    RuleDetailAPIView,
    RuleListCreateAPIView,
    LoginAPIView,
)

urlpatterns = [

    path("instances/", InstanceListAPIView.as_view(), name="instance_list"),
    path("instances/<str:inst_id>/bulk_config/", InstanceBulkConfigAPIView.as_view(), name="instance_bulk_config"),
    path("instances/<str:inst_id>/config/", InstanceConfigAPIView.as_view(), name="instance_config"),
    path("instances/<str:inst_id>/rule_configs/", InstanceRuleConfigListCreateAPIView.as_view(), name="instance_rule_config_list"),
    path("instances/<str:inst_id>/rule_configs/<int:pk>/", InstanceRuleConfigDetailAPIView.as_view(), name="instance_rule_config_detail"),

    # Rules
    path("rules/", RuleListCreateAPIView.as_view(), name="rule_list"),
    path("rules/<str:pk>/", RuleDetailAPIView.as_view(), name="rule_detail"),

    # Auth
    path("login/", LoginAPIView.as_view(), name="login"),
]