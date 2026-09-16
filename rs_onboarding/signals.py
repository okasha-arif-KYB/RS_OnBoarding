from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import GPInst

from .models import InstanceRuleConfig, Rule


@receiver(post_save, sender=GPInst)
def provision_new_instance(sender, instance, created, **kwargs):
    """New GPInst -> get every active rule at its default values."""
    if not created:
        return
    InstanceRuleConfig.objects.bulk_create(
        InstanceRuleConfig(instance=instance, rule=rule, is_enabled=True, values=rule.default_values())
        for rule in Rule.objects.filter(is_active=True)
    )


@receiver(post_save, sender=Rule)
def provision_new_rule(sender, instance, created, **kwargs):
    """New Rule -> backfill it onto every existing GPInst."""
    if not created:
        return
    InstanceRuleConfig.objects.bulk_create(
        InstanceRuleConfig(instance=gp_inst, rule=instance, is_enabled=True, values=instance.default_values())
        for gp_inst in GPInst.objects.all()
    )