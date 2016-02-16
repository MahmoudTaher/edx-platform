"""
ConfigurationModel for the mobile_api djangoapp.
"""
from django.db.models.fields import TextField, DateTimeField, CharField, IntegerField
from lms.djangoapps.mobile_api import utils
from config_models.models import ConfigurationModel
from mobile_api.mobile_platform import PLATFORM_CLASSES


class MobileApiConfig(ConfigurationModel):
    """
    Configuration for the video upload feature.

    The order in which the comma-separated list of names of profiles are given
    is in priority order.
    """
    video_profiles = TextField(
        blank=True,
        help_text="A comma-separated list of names of profiles to include for videos returned from the mobile API."
    )

    @classmethod
    def get_video_profiles(cls):
        """
        Get the list of profiles in priority order when requesting from VAL
        """
        return [profile.strip() for profile in cls.current().video_profiles.split(",") if profile]


class AppVersionConfig(ConfigurationModel):
    """
    Configuration for mobile app versions available.
    """
    PLATFORM_CHOICES = tuple([
        (platform, platform)
        for platform in PLATFORM_CLASSES.keys()
    ])
    KEY_FIELDS = ('platform', 'version')  # combination of mobile platform and version is unique
    platform = CharField(max_length=50, choices=PLATFORM_CHOICES, blank=False)
    version = CharField(
        max_length=50,
        blank=False,
        help_text="Version should be in the format X.X.X.Y where X is a number and Y is alphanumeric"
    )
    major_version = IntegerField()
    minor_version = IntegerField()
    patch_version = IntegerField()
    expire_at = DateTimeField(null=True, blank=True, verbose_name="Expiry date for platform version")

    class Meta:
        ordering = ['-major_version', '-minor_version', '-patch_version']

    def __unicode__(self):
        return "{}_{}".format(self.platform, self.version)

    @classmethod
    def latest_version(cls, platform):
        """ returns latest supported version for a platform """
        latest_version_config = cls.objects.current_set().filter(platform=platform, enabled=True).first()
        if latest_version_config:
            return latest_version_config.version

    @classmethod
    def last_supported_date(cls, platform, version):
        """ returns date when version will get expired for a platform """
        parsed_version = utils.parsed_version(version)
        active_configs = cls.objects.current_set().filter(
            platform=platform,
            enabled=True,
            expire_at__isnull=False
        ).reverse()
        for config in active_configs:
            if utils.parsed_version(config.version) >= parsed_version:
                return config.expire_at

    def save(self, *args, **kwargs):
        """
        parses version into major, minor and patch versions before saving
        """
        self.major_version, self.minor_version, self.patch_version = utils.parsed_version(self.version)
        super(AppVersionConfig, self).save(*args, **kwargs)
