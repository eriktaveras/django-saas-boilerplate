from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _


class LandingAdminSite(AdminSite):
    site_header = _('Landing Page Administration')
    site_title = _('Landing Admin')
    index_title = _('Welcome to the Landing Admin')

landing_admin_site = LandingAdminSite(name='landing_admin')
