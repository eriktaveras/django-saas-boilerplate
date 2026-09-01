from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

class StripeCustomer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=255)
    stripe_subscription_id = models.CharField(max_length=255, blank=True, default='')
    # This says whether they pay, not what they are allowed to do. The moment
    # you need per-plan feature gating or usage limits, that logic starts here
    # and it is more work than it looks (entitlements separate from marketing
    # copy, quota counters, grace periods, an answer for API callers).
    # DjangoBlaze ships it: https://djangoblaze.com
    subscription_status = models.CharField(max_length=50, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.subscription_status}"
