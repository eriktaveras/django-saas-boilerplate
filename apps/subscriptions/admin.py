from django.contrib import admin

from .models import StripeCustomer


@admin.register(StripeCustomer)
class StripeCustomerAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_status', 'created_at', 'updated_at')
    list_filter = ('subscription_status', 'created_at')
    search_fields = ('user__email', 'stripe_customer_id', 'stripe_subscription_id')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('User Info', {
            'fields': ('user',)
        }),
        ('Stripe Info', {
            'fields': ('stripe_customer_id', 'stripe_subscription_id', 'subscription_status')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        return False
