from rest_framework.routers import DefaultRouter

from .views import GPInstConfigViewSet, InstanceRuleConfigViewSet, RuleViewSet

router = DefaultRouter()
router.register("rules", RuleViewSet, basename="rule")
router.register("gp-insts", GPInstConfigViewSet, basename="gp-inst-config")
router.register("instance-rule-configs", InstanceRuleConfigViewSet, basename="instance-rule-config")

urlpatterns = router.urls