from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


# ============================================================
# STANDALONE TESTING ONLY
# ------------------------------------------------------------
# GPEntity, GPInst, User, UserManager below will eventually live
# in automation_app. When this app is merged into the main
# codebase:
#   1. Delete GPEntity, GPInst, User, UserManager from this file.
#   2. Add this import at the top instead:
#          from automation_app.models import GPEntity, GPInst, User
#   3. Update AUTH_USER_MODEL in settings.py to
#      "automation_app.User".
#   4. Wipe + regenerate migrations for both apps.
# Everything else (Rule, InstanceRuleConfig) stays as-is.
# ============================================================


class GPEntity(models.Model):
    name = models.CharField(max_length=250, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name}'


class GPInst(models.Model):
    entity = models.ForeignKey(GPEntity, on_delete=models.SET_NULL, null=True, related_name='instances')
    name = models.CharField(max_length=255, null=True, unique=True)
    inst_id = models.CharField(max_length=35, null=True, blank=True, unique=True)
    address = models.CharField(max_length=255, null=True, blank=True, unique=True)
    recepient_address = models.CharField(max_length=255, null=True, blank=True, unique=True)
    is_active_for_ltc = models.BooleanField(default=False)
    is_active_outlook_notifications = models.BooleanField(default=False)
    inst_order = models.IntegerField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.name}'


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, password2=None):
        """
        Creates and saves a User with the given email, password.
        """
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(
            email,
            password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractUser):
    username = None
    email = models.EmailField(
        verbose_name="email",
        max_length=255,
        unique=True,
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    batch_moniter = models.BooleanField(default=False)
    pbi_rs_access = models.BooleanField(default=False)
    pbi_letter_access = models.BooleanField(default=False)
    monthly_reporting_access = models.BooleanField(default=False)
    drug_list_access = models.BooleanField(default=False)
    xfm_access = models.BooleanField(default=False)
    exective_reporting_access = models.BooleanField(default=False)
    instances = models.ManyToManyField(GPInst, related_name='accounts', blank=True, related_query_name='accounts')
    entity = models.ForeignKey(GPEntity, on_delete=models.SET_NULL, null=True, related_name='users')

    objects = UserManager()

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


IS_DISABLED_NONE = "N"
IS_DISABLED_SYSTEM1 = "S"
IS_DISABLED_EMIS = "E"
IS_DISABLED_BOTH = "B"
IS_DISABLED_CHOICES = [
    (IS_DISABLED_NONE, "None"),
    (IS_DISABLED_SYSTEM1, "System1"),
    (IS_DISABLED_EMIS, "Emis"),
    (IS_DISABLED_BOTH, "Both"),
]


class Rule(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=64)
    rule_type = models.CharField(max_length=64, blank=True, null=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_disabled = models.CharField(
        max_length=1,
        choices=IS_DISABLED_CHOICES,
        default=IS_DISABLED_NONE,
    )
    field_schema = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "display_order"]

    def __str__(self):
        return self.name

    def default_values(self):
        fields = (self.field_schema or {}).get("fields", [])
        values = {}
        for fld in fields:
            field_key = fld.get("fieldKey")
            default_val = fld.get("defaultValue")
            if field_key and default_val is not None:
                values[field_key] = default_val
        return values


class InstanceRuleConfig(models.Model):
    SYSTEM1 = "systemone"
    SYSTEM2 = "emis"
    SYSTEM_TYPE_CHOICES = [
        (SYSTEM1, "System One"),
        (SYSTEM2, "Emis"),
    ]

    instance = models.ForeignKey(
        GPInst,
        on_delete=models.CASCADE,
        related_name="rule_configs",
    )
    rule = models.ForeignKey(
        Rule,
        on_delete=models.PROTECT,
        related_name="instance_configs",
    )
    is_enabled = models.BooleanField(default=True)
    system_type = models.CharField(
        max_length=16,
        choices=SYSTEM_TYPE_CHOICES,
        blank=True,
        null=True,
    )
    values = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["instance", "rule"],
                name="unique_instance_rule",
            )
        ]