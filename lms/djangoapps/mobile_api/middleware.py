"""
Middleware for Mobile APIs
"""
from datetime import datetime
from django.core.cache import cache
from django.http import HttpResponse
from pytz import UTC
from mobile_api.mobile_platform import MobilePlatform
from mobile_api.models import AppVersionConfig
from mobile_api.utils import parsed_version
from openedx.core.lib.mobile_utils import is_request_from_mobile_app
from request_cache.middleware import RequestCache


class AppVersionUpgrade(object):
    """
    Middleware class to keep track of mobile application version being used
    """
    LATEST_VERSION_HEADER = 'EDX-APP-LATEST-VERSION'
    UPGRADE_DEADLINE_HEADER = 'EDX-APP-UPGRADE-DATE'
    NO_LAST_SUPPORTED_DATE = 'NO_LAST_SUPPORTED_DATE'
    NO_LATEST_VERSION = 'NO_LATEST_VERSION'
    USER_APP_VERSION = 'USER_APP_VERSION'

    def process_request(self, request):
        """
        raises HTTP Upgrade Require error if request is from mobile native app and
        user app version is no longer supported
        """
        version_data = self.get_info_for_version(request)
        if version_data:
            last_supported_date = version_data[self.UPGRADE_DEADLINE_HEADER]
            if last_supported_date != self.NO_LAST_SUPPORTED_DATE:
                if datetime.now().replace(tzinfo=UTC) > last_supported_date:
                    return HttpResponse(status=426)

    def process_response(self, _request, response):
        """
        If request is from mobile native app, then add headers to response;
        1. EDX-APP-LATEST-VERSION; if user app version < latest available version
        2. EDX-APP-UPGRADE-DATE; if user app version < min supported version and timestamp < expiry of that version
        """
        version_data = self.get_info_for_version(_request)
        if version_data:
            upgrade_deadline = version_data[self.UPGRADE_DEADLINE_HEADER]
            if upgrade_deadline != self.NO_LAST_SUPPORTED_DATE:
                response[self.UPGRADE_DEADLINE_HEADER] = upgrade_deadline.isoformat()
            latest_version = version_data[self.LATEST_VERSION_HEADER]
            user_app_version = version_data[self.USER_APP_VERSION]
            if (latest_version != self.NO_LATEST_VERSION and
                    parsed_version(user_app_version) < parsed_version(latest_version)):
                response[self.LATEST_VERSION_HEADER] = latest_version
        return response

    def get_cache_key_name(self, user_agent, field):
        """ get key name to use to cache any property against user agent """
        return "mobile_api.app_version_upgrade.{}.{}".format(field, user_agent)

    def get_info_for_version(self, request):
        """
        It sets request cache data for last_supported_date and latest_version with memcached values if exists against
        user-agent else computes the values for specific platform and sets it in both memcache (for next
        server interaction from same user-agent/platform) and request cache
        """
        user_agent = request.META.get('HTTP_USER_AGENT')
        if user_agent:
            request_cache_dict = RequestCache.get_request_cache().data
            last_supported_date = request_cache_dict.get(self.UPGRADE_DEADLINE_HEADER, None)
            latest_version = request_cache_dict.get(self.LATEST_VERSION_HEADER, None)
            user_app_version = request_cache_dict.get(self.USER_APP_VERSION, None)
            if last_supported_date and latest_version and user_app_version:
                return {
                    self.UPGRADE_DEADLINE_HEADER: last_supported_date,
                    self.LATEST_VERSION_HEADER: latest_version,
                    self.USER_APP_VERSION: user_app_version,
                }

            platform = self.get_platform(request, user_agent)
            if platform:
                request_cache_dict[self.USER_APP_VERSION] = platform.version
                cached_data = cache.get_many([
                    self.get_cache_key_name(user_agent, self.UPGRADE_DEADLINE_HEADER),
                    self.get_cache_key_name(platform.NAME, self.LATEST_VERSION_HEADER)
                ])

                last_supported_date = cached_data.get(
                    self.get_cache_key_name(user_agent, self.UPGRADE_DEADLINE_HEADER),
                    None
                )
                if not last_supported_date:
                    last_supported_date = self.get_last_supported_date(platform.NAME, platform.version)
                    cache.set(
                        self.get_cache_key_name(user_agent, self.UPGRADE_DEADLINE_HEADER),
                        last_supported_date,
                        3600
                    )
                request_cache_dict[self.UPGRADE_DEADLINE_HEADER] = last_supported_date

                latest_version = cached_data.get(
                    self.get_cache_key_name(platform.NAME, self.LATEST_VERSION_HEADER),
                    None
                )
                if not latest_version:
                    latest_version = self.get_latest_version(platform.NAME)
                    cache.set(
                        self.get_cache_key_name(platform.NAME, self.LATEST_VERSION_HEADER),
                        latest_version,
                        3600
                    )
                request_cache_dict[self.LATEST_VERSION_HEADER] = latest_version

                return {
                    self.UPGRADE_DEADLINE_HEADER: last_supported_date,
                    self.LATEST_VERSION_HEADER: latest_version,
                    self.USER_APP_VERSION: platform.version,
                }

    def get_platform(self, request, user_agent):
        """
        determines the platform for mobile app making the request
        returns None if request is not from native mobile app or does not belong to supported platforms
        """
        if is_request_from_mobile_app(request):
            return MobilePlatform.get_instance(user_agent)

    def get_last_supported_date(self, platform_name, platform_version):
        """ get expiry date of app version for a platform """
        return AppVersionConfig.last_supported_date(platform_name, platform_version) or self.NO_LAST_SUPPORTED_DATE

    def get_latest_version(self, platform_name):
        """ get latest app version available for platform """
        return AppVersionConfig.latest_version(platform_name) or self.NO_LATEST_VERSION
