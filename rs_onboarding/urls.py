from rest_framework.routers import DefaultRouter

from .views import ClientRuleConfigViewSet, ClientViewSet, RuleViewSet

router = DefaultRouter()
router.register("rules", RuleViewSet, basename="rule")
router.register("clients", ClientViewSet, basename="client")
router.register("client-rule-configs", ClientRuleConfigViewSet, basename="client-rule-config")

urlpatterns = router.urls