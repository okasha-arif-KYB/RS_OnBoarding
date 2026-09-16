from django.core.management.base import BaseCommand
from django.db import transaction

from rs_onboarding.models import GPEntity, GPInst, InstanceRuleConfig, Rule

ENTITIES = [
    {"name": "Willowbrook Health Group"},
    {"name": "Riverside Primary Care Network"},
]

INSTANCES = [
    {
        "entity": "Willowbrook Health Group",
        "name": "Willowbrook Surgery - Main Branch",
        "inst_id": "GP00001",
        "address": "12 Willow Lane, Manchester, M1 4AB",
        "recepient_address": "12 Willow Lane Recipient Dept, Manchester, M1 4AB",
        "is_active_for_ltc": True,
        "is_active_outlook_notifications": True,
        "inst_order": 1,
    },
    {
        "entity": "Willowbrook Health Group",
        "name": "Willowbrook Surgery - North Branch",
        "inst_id": "GP00002",
        "address": "45 Oak Street, Manchester, M2 5CD",
        "recepient_address": "45 Oak Street Recipient Dept, Manchester, M2 5CD",
        "is_active_for_ltc": False,
        "is_active_outlook_notifications": True,
        "inst_order": 2,
    },
    {
        "entity": "Riverside Primary Care Network",
        "name": "Riverside Medical Centre",
        "inst_id": "GP00003",
        "address": "8 River Road, Leeds, LS1 2EF",
        "recepient_address": "8 River Road Recipient Dept, Leeds, LS1 2EF",
        "is_active_for_ltc": True,
        "is_active_outlook_notifications": False,
        "inst_order": 1,
    },
]


class Command(BaseCommand):
    help = "Seed dummy GPEntity/GPInst rows and backfill InstanceRuleConfig defaults for every active rule."

    def handle(self, *args, **options):
        with transaction.atomic():
            entity_map = {}
            for row in ENTITIES:
                entity, created = GPEntity.objects.get_or_create(name=row["name"])
                entity_map[row["name"]] = entity
                self.stdout.write(f"{'Created' if created else 'Exists '} entity: {entity.name}")

            insts = []
            for row in INSTANCES:
                inst, created = GPInst.objects.get_or_create(
                    inst_id=row["inst_id"],
                    defaults={
                        "entity": entity_map[row["entity"]],
                        "name": row["name"],
                        "address": row["address"],
                        "recepient_address": row["recepient_address"],
                        "is_active_for_ltc": row["is_active_for_ltc"],
                        "is_active_outlook_notifications": row["is_active_outlook_notifications"],
                        "inst_order": row["inst_order"],
                        "is_active": True,
                    },
                )
                insts.append(inst)
                self.stdout.write(f"{'Created' if created else 'Exists '} instance: {inst.name} ({inst.inst_id})")

            self._backfill_rule_configs(insts)

    def _backfill_rule_configs(self, insts):
        """
        Give every seeded GPInst an InstanceRuleConfig for every active Rule, at the
        rule's schema-driven default values, skipping any (instance, rule) pair that
        already exists. Does the same job your post_save signal would do, so it works
        even if you haven't wired that up yet in this standalone app.
        """
        active_rules = list(Rule.objects.filter(is_active=True))
        existing_pairs = set(
            InstanceRuleConfig.objects.filter(instance__in=insts).values_list("instance_id", "rule_id")
        )

        new_configs = [
            InstanceRuleConfig(instance=inst, rule=rule, is_enabled=True, values=rule.default_values())
            for inst in insts
            for rule in active_rules
            if (inst.pk, rule.pk) not in existing_pairs
        ]

        InstanceRuleConfig.objects.bulk_create(new_configs)
        self.stdout.write(
            self.style.SUCCESS(
                f"Backfilled {len(new_configs)} InstanceRuleConfig rows "
                f"({len(insts)} instances x {len(active_rules)} rules, minus existing)."
            )
        )