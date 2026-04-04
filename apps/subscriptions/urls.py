from django.urls import path

from . import views

app_name = 'subscriptions'

urlpatterns = [
    path('', views.subscription_page, name='subscription_page'),
    path('create/', views.create_subscription, name='create_subscription'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]
