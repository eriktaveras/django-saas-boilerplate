from django.urls import path

from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('settings/', views.settings, name='settings'),
    path('settings/generate-api-key/', views.generate_api_key, name='generate_api_key'),
    path('subscription/plans/', views.subscription_plans, name='subscription_plans'),
    path('subscription/plans/<slug:plan_slug>/subscribe/', views.subscribe_to_plan, name='subscribe_to_plan'),
    path('subscription/cancel/', views.cancel_subscription, name='cancel_subscription'),
    path('subscription/trial/', views.start_trial, name='start_trial'),
]
