"""
Django admin dashboard configuration for LMS XBlock infrastructure.
"""

from django.contrib import admin
from config_models.admin import ConfigurationModelAdmin, KeyedConfigurationModelAdmin
from mobile_api.models import MobileApiConfig, AppVersionConfig

admin.site.register(MobileApiConfig, ConfigurationModelAdmin)


class AppVersionConfigAdmin(KeyedConfigurationModelAdmin):
    """ Admin class for AppVersionConfig model """
    fields = ('platform', 'version', 'expire_at', 'enabled')
    list_filter = ['platform']

    class Meta(object):
        ordering = ['-major_version', '-minor_version', '-patch_version']

    def get_list_display(self, request):  # pylint: disable=unused-variable
        """ defines fields to display in list view """
        return ['change_date', 'changed_by', 'platform', 'version', 'expire_at', 'enabled', 'edit_link']

admin.site.register(AppVersionConfig, AppVersionConfigAdmin)
