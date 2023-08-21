from django.contrib.admin.apps import AdminConfig


class BildungsplattformAdminConfig(AdminConfig):
    default_site = 'bildungsplattform.admin.BildungsplattformAdminSite'
