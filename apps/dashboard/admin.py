from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _


class DashboardAdminSite(AdminSite):
    site_header = _('Dashboard Administration')
    site_title = _('Dashboard Admin')
    index_title = _('Welcome to the Dashboard Admin')

dashboard_admin_site = DashboardAdminSite(name='dashboard_admin')
