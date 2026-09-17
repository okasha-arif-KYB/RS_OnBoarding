from django.core.management.base import BaseCommand
from django.db import transaction

from rs_onboarding.models import GPEntity, GPInst, InstanceRuleConfig, Rule

# Parsed from your provided JSON payload
INSTANCE_DATA = [
    {
        "entity_id": 1,
        "entity_name": "Haxby",
        "name": "HAXBY - York (0101)",
        "inst_id": "haxby_0001",
    },
    {
        "entity_id": 1,
        "entity_name": "Haxby",
        "name": "HAXBY - Kingswood - Hull (0303)",
        "inst_id": "haxby_0002",
    },
    {
        "entity_id": 1,
        "entity_name": "Haxby",
        "name": "HAXBY - Scarborough (0202)",
        "inst_id": "haxby_0005",
    },
    {
        "entity_id": 1,
        "entity_name": "Haxby",
        "name": "HAXBY - Calvert & Newington - Hull - (0505)",
        "inst_id": "haxby_0004",
    },
    {
        "entity_id": 1,
        "entity_name": "Haxby",
        "name": "HAXBY - Burnbrae - Hull (0404)",
        "inst_id": "haxby_0003",
    },
    {
        "entity_id": 2,
        "entity_name": "The Roxton Practice",
        "name": "The Roxton Practice",
        "inst_id": "rox_0001",
    },
    {
        "entity_id": 3,
        "entity_name": "York Medical Group",
        "name": "York Medical Group",
        "inst_id": "ymg_0001",
    },
    {
        "entity_id": 15,
        "entity_name": "Unsworth Group",
        "name": "UGP",
        "inst_id": "ugp_0001",
    },
    {
        "entity_id": 14,
        "entity_name": "Spring House Surgery",
        "name": "Spring House Surgery",
        "inst_id": "shs_0001",
    },
    {
        "entity_id": 12,
        "entity_name": "MyHealth",
        "name": "MyHealth",
        "inst_id": "mh_0001",
    },
    {
        "entity_id": 10,
        "entity_name": "Tollerton Surgery",
        "name": "Tollerton Surgery",
        "inst_id": "tol_0001",
    },
    {
        "entity_id": 9,
        "entity_name": "Dr O Z Qureshi's Surgery",
        "name": "Dr O Z Qureshi Surgery",
        "inst_id": "ozq_0001",
    },
    {
        "entity_id": 8,
        "entity_name": "Beacon Medical Centre",
        "name": "Beacon Medical Centre",
        "inst_id": "bmc_0001",
    },
    {
        "entity_id": 7,
        "entity_name": "Clee Medical Centre",
        "name": "Clee Medical Centre",
        "inst_id": "cmc_0001",
    },
    {
        "entity_id": 6,
        "entity_name": "Greenlands Surgery",
        "name": "Greenlands Surgery",
        "inst_id": "grn_0001",
    },
    {
        "entity_id": 5,
        "entity_name": "Raj Medical Centre",
        "name": "Raj Medical Centre",
        "inst_id": "raj_0001",
    },
    {
        "entity_id": 4,
        "entity_name": "James Wigg",
        "name": "James Wigg",
        "inst_id": "JW_0001",
    },
    {
        "entity_id": 20,
        "entity_name": "Stowhealth",
        "name": "StowHealth",
        "inst_id": "Stow_0001",
    },
    {
        "entity_id": 16,
        "entity_name": "Wickham Market Medical Centre (DHG)",
        "name": "Wickham Market Medical Centre (DHG)",
        "inst_id": "WMM_001",
    },
    {
        "entity_id": 17,
        "entity_name": "Framfield (DHG)",
        "name": "Framfield (DHG)",
        "inst_id": "Framfield_001",
    },
    {
        "entity_id": 18,
        "entity_name": "EastField",
        "name": "EastField Medical Centre",
        "inst_id": "EastField_001",
    },
    {
        "entity_id": 19,
        "entity_name": "Dr.A.Sinha",
        "name": "Dr A Sinha",
        "inst_id": "DrAS_001",
    },
    {
        "entity_id": 22,
        "entity_name": "Little St Johns (DHG)",
        "name": "Little St Johns (DHG)",
        "inst_id": "LSJ_001",
    },
    {
        "entity_id": 23,
        "entity_name": "DHG",
        "name": "DHG",
        "inst_id": "DHG_001",
    },
    {
        "entity_id": 24,
        "entity_name": "Bolton Medical Centre",
        "name": "Bolton Medical Centre",
        "inst_id": "BMC_001",
    },
    {
        "entity_id": 25,
        "entity_name": "Ashbourne Medical",
        "name": "Ashbourne Medical",
        "inst_id": "Ash_0001",
    },
    {
        "entity_id": 26,
        "entity_name": "Two Rivers",
        "name": "Two Rivers",
        "inst_id": "TR_001",
    },
    {
        "entity_id": 21,
        "entity_name": "Unity Suffolk",
        "name": "Unity",
        "inst_id": "Uni_0001",
    },
    {
        "entity_id": 27,
        "entity_name": "KYNOBY INSTANCE",
        "name": "KYNOBY TEST",
        "inst_id": "ka_0001",
    },
    {
        "entity_id": 28,
        "entity_name": "Conisbrough",
        "name": "Conisbrough",
        "inst_id": "cgp_0001",
    },
    {
        "entity_id": 29,
        "entity_name": "Lakeside",
        "name": "Lakeside - Corby",
        "inst_id": "lcorby_0001",
    },
    {
        "entity_id": 30,
        "entity_name": "Lakeside - Queen Street Surgery",
        "name": "Lakeside - Queen Street Surgery",
        "inst_id": "lqss_0001",
    },
    {
        "entity_id": 31,
        "entity_name": "Guildhall & Barrow Surgery",
        "name": "Guildhall & Barrow Surgery",
        "inst_id": "gbs_0001",
    },
    {
        "entity_id": 32,
        "entity_name": "Dr R K Mathews",
        "name": "Dr R K Mathews",
        "inst_id": "rkm_0001",
    },
    {
        "entity_id": 23,
        "entity_name": "DHG",
        "name": "Peninsula",
        "inst_id": "ppd_0001",
    },
    {
        "entity_id": 33,
        "entity_name": "The Garth Surgery",
        "name": "The Garth Surgery",
        "inst_id": "tgs_0001",
    },
    {
        "entity_id": 34,
        "entity_name": "Lakeside - Stamford",
        "name": "Lakeside - Stamford",
        "inst_id": "stamf_0001",
    },
    {
        "entity_id": 35,
        "entity_name": "Lakeside - St Neots",
        "name": "Lakeside - St Neots",
        "inst_id": "LKNEOTS_0001",
    },
    {
        "entity_id": 36,
        "entity_name": "Cherry Tree Medical",
        "name": "Cherry Tree Medical",
        "inst_id": "CTM_0001",
    },
    {
        "entity_id": 38,
        "entity_name": "Wish Park Surgery",
        "name": "Wish Park Surgery",
        "inst_id": "wps_0001",
    },
    {
        "entity_id": 29,
        "entity_name": "Lakeside",
        "name": "Lakeside Hereward",
        "inst_id": "LHWRD_0005",
    },
    {
        "entity_id": 39,
        "entity_name": "Portslade Health Centre",
        "name": "Portslade Health Centre",
        "inst_id": "phc_0001",
    },
    {
        "entity_id": 40,
        "entity_name": "Greens Norton & Weedon",
        "name": "Greens Norton & Weedon",
        "inst_id": "GNW_0001",
    },
    {
        "entity_id": 41,
        "entity_name": "Beaconsfield",
        "name": "Beaconsfield",
        "inst_id": "BCF_0001",
    },
    {
        "entity_id": 29,
        "entity_name": "Lakeside",
        "name": "Lakeside Yaxley",
        "inst_id": "LKYAX_0006",
    },
    {
        "entity_id": 42,
        "entity_name": "Pinehill Surgery",
        "name": "Pinehill Surgery",
        "inst_id": "pi_0001",
    },
    {
        "entity_id": 43,
        "entity_name": "Felixstowe Road",
        "name": "Felixstowe Road",
        "inst_id": "FSR_0001",
    },
    {
        "entity_id": 44,
        "entity_name": "Compass House Medical",
        "name": "Compass House Medical",
        "inst_id": "CHM_0001",
    },
    {
        "entity_id": 29,
        "entity_name": "Lakeside",
        "name": "Lakeside Oundle",
        "inst_id": "lakeside_0007",
    },
    {
        "entity_id": 45,
        "entity_name": "Mile Oak Surgery",
        "name": "Mile Oak Surgery",
        "inst_id": "mos_0001",
    },
]


class Command(BaseCommand):
    help = "Seed GPEntity and GPInst records and backfill InstanceRuleConfig defaults for active rules."

    def handle(self, *args, **options):
        with transaction.atomic():
            entity_map = {}

            # Create or fetch GPEntity instances directly mapping to explicit entity IDs
            for row in INSTANCE_DATA:
                entity_name = row["entity_name"]
                if entity_name not in entity_map:
                    entity, created = GPEntity.objects.get_or_create(
                        name=entity_name
                    )
                    entity_map[entity_name] = entity
                    self.stdout.write(
                        f"{'Created' if created else 'Exists '} entity: {entity.name}"
                    )

            # Create or update GPInst objects
            insts = []
            for row in INSTANCE_DATA:
                inst, created = GPInst.objects.get_or_create(
                    inst_id=row["inst_id"],
                    defaults={
                        "entity": entity_map[row["entity_name"]],
                        "name": row["name"],
                        "is_active": True,
                    },
                )
                insts.append(inst)
                self.stdout.write(
                    f"{'Created' if created else 'Exists '} instance: {inst.name} ({inst.inst_id})"
                )

            self._backfill_rule_configs(insts)

    def _backfill_rule_configs(self, insts):
        """
        Populate InstanceRuleConfig entries for active rules where missing.
        """
        active_rules = list(Rule.objects.filter(is_active=True))
        existing_pairs = set(
            InstanceRuleConfig.objects.filter(
                instance__in=insts
            ).values_list("instance_id", "rule_id")
        )

        new_configs = [
            InstanceRuleConfig(
                instance=inst,
                rule=rule,
                is_enabled=True,
                values=rule.default_values(),
            )
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