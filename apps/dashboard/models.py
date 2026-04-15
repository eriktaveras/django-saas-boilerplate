from django.conf import settings
from django.db import models
from django.utils import timezone


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    interval = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('yearly', 'Yearly'),
        ],
        default='monthly'
    )
    features = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Subscription Plan'
        verbose_name_plural = 'Subscription Plans'

    def __str__(self):
        return f"{self.name} ({self.get_interval_display()})"

class UserSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='settings'
    )
    # Notification preferences
    notify_comments = models.BooleanField(default=False)
    notify_updates = models.BooleanField(default=False)
    notify_marketing = models.BooleanField(default=False)

    # API settings
    api_key_hash = models.CharField(max_length=64, blank=True, default='')
    api_key_prefix = models.CharField(max_length=12, blank=True, default='')
    api_key_created_at = models.DateTimeField(null=True, blank=True)

    # Subscription settings
    subscription_plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subscribers'
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('cancelled', 'Cancelled'),
            ('trial', 'Trial'),
        ],
        default='inactive'
    )
    subscription_start_date = models.DateTimeField(null=True, blank=True)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    trial_end_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Settings'
        verbose_name_plural = 'User Settings'

    def __str__(self):
        return f"Settings for {self.user.email}"

    @property
    def is_subscription_active(self):
        if self.subscription_status != 'active':
            return False
        if self.subscription_end_date and self.subscription_end_date < timezone.now():
            return False
        return True

    @property
    def is_trial_active(self):
        if self.subscription_status != 'trial':
            return False
        if self.trial_end_date and self.trial_end_date < timezone.now():
            return False
        return True
