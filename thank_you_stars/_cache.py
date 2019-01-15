# encoding: utf-8

from __future__ import absolute_import, division, unicode_literals

import enum
from datetime import datetime
from functools import total_ordering

import msgfy
import simplejson as json
from datetimerange import DateTimeRange
from path import Path
from pathvalidate import sanitize_filename, sanitize_filepath

from ._const import PACKAGE_NAME
from ._logger import logger


_BASE_CACHE_DIR_PATH = "~/.cache/{:s}".format(PACKAGE_NAME)


def sec_to_hour(sec):
    return sec / (60 ** 2)


def hour_to_sec(hour):
    return hour * (60 ** 2)


def touch(filepath):
    with open(filepath, "w"):
        pass


@enum.unique
class CacheType(enum.Enum):
    GITHUB = "GitHub"
    PIP = "pip"
    PYPI = "PyPI"


@total_ordering
class CacheTime(object):
    @property
    def seconds(self):
        return self.__second

    @property
    def hour(self):
        return sec_to_hour(self.seconds)

    def __init__(self, seconds=None, days=None):
        if seconds is not None and days is None:
            self.__second = seconds
        elif seconds is None and days is not None:
            self.__second = hour_to_sec(24) * days

        else:
            raise ValueError("seconds={}, days={}".format(seconds, days))

    def __eq__(self, other):
        return self.seconds == other.seconds

    def __lt__(self, other):
        return self.seconds < other.seconds


class CacheManager(object):
    def __init__(self, user_name, cache_type, cache_lifetime):
        self.__base_dir = (
            Path(
                "~/.cache/{package}/{user}/{cache_type}".format(
                    package=PACKAGE_NAME, user=user_name, cache_type=cache_type
                )
            )
            .expand()
            .normpath()
        )
        self.__cache_lifetime = cache_lifetime

    def is_cache_available(self, cache_file_path):
        if not cache_file_path.isfile():
            logger.debug("cache not found: {}".format(cache_file_path))
            return False

        try:
            dtr = DateTimeRange(datetime.fromtimestamp(cache_file_path.mtime), datetime.now())
        except OSError:
            return False

        if not dtr.is_valid_timerange():
            return False

        cache_elapsed = CacheTime(dtr.get_timedelta_second())
        cache_msg = "path={path}, lifetime={lifetime:.1f}h, elapsed={elapsed:.1f}h".format(
            path=cache_file_path, lifetime=self.__cache_lifetime.hour, elapsed=cache_elapsed.hour
        )

        if cache_elapsed < self.__cache_lifetime:
            logger.debug("cache available: {}".format(cache_msg))
            return True

        logger.debug("cache expired: {}".format(cache_msg))

        return False

    def __get_pkg_cache_dir(self, package_name):
        cache_dir = self.__base_dir.joinpath(sanitize_filename(package_name).lower())
        cache_dir.makedirs_p()

        return cache_dir

    def get_pkg_cache_filepath(self, package_name, filename):
        return self.__get_pkg_cache_dir(package_name).joinpath(sanitize_filename(filename))

    def remove_pkg_cache(self, package_name, filename):
        filepath = self.get_pkg_cache_filepath(package_name, filename)
        logger.debug("remove cache: {}".format(filepath))
        filepath.remove_p()

    def __get_misc_cache_dir(self, classifier_name):
        cache_dir = self.__base_dir.joinpath(sanitize_filepath(classifier_name))
        cache_dir.makedirs_p()

        return cache_dir

    def get_misc_cache_filepath(self, classifier_name, filename):
        return self.__get_misc_cache_dir(classifier_name).joinpath(sanitize_filename(filename))

    def remove_misc_cache(self, classifier_name, filename):
        filepath = self.get_misc_cache_filepath(classifier_name, filename)
        logger.debug("remove cache: {}".format(filepath))
        filepath.remove_p()

    def load_json(self, cache_file_path):
        with cache_file_path.open() as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                logger.error(
                    "failed to load cache file '{}': {}".format(
                        cache_file_path, msgfy.to_error_message(e)
                    )
                )

        return None
