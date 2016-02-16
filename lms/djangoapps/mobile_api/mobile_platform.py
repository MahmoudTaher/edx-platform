"""
Platform related operations for Mobile APP
"""
import abc
import re


class MobilePlatform:
    """
    MobilePlatform class creates an instance of platform based on user agent and supports platform
    related operations
    """
    __metaclass__ = abc.ABCMeta
    version = None

    def __init__(self, version):
        self.version = version

    @classmethod
    def create_instance(cls, user_agent, user_agent_regex):
        """ Returns platform instance if user_agent matches with USER_AGENT_REGEX """
        match = re.search(user_agent_regex, user_agent)
        if match:
            return cls(match.group('version'))

    @classmethod
    def get_instance(cls, user_agent):
        """
        It creates an instance of one of the supported mobile platforms (i.e. iOS, Android) by regex comparison
        of user-agent.

        Parameters:
            user_agent: user_agent of mobile app

        Returns:
            instance of one of the supported mobile platforms (i.e. iOS, Android)
        """
        for subclass in PLATFORM_CLASSES.values():
            instance = subclass.create_instance(user_agent, subclass.USER_AGENT_REGEX)
            if instance:
                return instance


class Ios(MobilePlatform):
    """ iOS platform """
    USER_AGENT_REGEX = (r'\((?P<version>[0-9]+.[0-9]+.[0-9]+(.[0-9a-zA-Z]*)?); OS Version [0-9.]+ '
                        r'\(Build [0-9a-zA-Z]*\)\)')
    NAME = "iOS"


class Android(MobilePlatform):
    """ Android platform """
    USER_AGENT_REGEX = (r'Dalvik/[.0-9]+ \(Linux; U; Android [.0-9]+; (.*) Build/[0-9a-zA-Z]*\) '
                        r'(.*)/(?P<version>[0-9]+.[0-9]+.[0-9]+(.[0-9a-zA-Z]*)?)')
    NAME = "Android"


# a list of all supported mobile platforms
PLATFORM_CLASSES = {Ios.NAME: Ios, Android.NAME: Android}
