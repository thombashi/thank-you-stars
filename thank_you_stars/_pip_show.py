# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import re
import sys

from subprocrunner import CalledProcessError, SubprocessRunner

from ._logger import logger


class PipShow(object):
    _AUTHOR_REGEXP = re.compile("^Author: (?P<author>.+)", re.MULTILINE)

    cache_mgr = None

    @classmethod
    def execute(cls, package_name):
        cache_file_path = cls.cache_mgr.get_pkg_cache_filepath(package_name, "pip_show")

        if cls.cache_mgr.is_cache_available(cache_file_path):
            logger.debug("load pip show cache from {}".format(cache_file_path))

            with cache_file_path.open() as f:
                return PipShow(f.read())

        proc_runner = SubprocessRunner(["pip", "show", package_name])

        try:
            proc_runner.run(check=True)
        except CalledProcessError as e:
            logger.error(
                "failed to fetch '{}' package info: require an installed PyPI package name".format(
                    package_name
                )
            )
            sys.exit(e.returncode)

        logger.debug("write pip show cache to {}".format(cache_file_path))

        pip_show = proc_runner.stdout
        with cache_file_path.open(mode="w") as f:
            f.write(pip_show)

        return PipShow(pip_show)

    @property
    def content(self):
        return self.__pip_show

    def __init__(self, pip_show_result):
        self.__pip_show = pip_show_result
        self.__requires_regexp = re.compile("Requires: ([a-zA-Z0-9-_.]+(, )?){1,}", re.MULTILINE)

    def extract_author(self):
        match = self._AUTHOR_REGEXP.search(self.__pip_show)
        if not match:
            raise ValueError("author not found in 'pip show'")

        return match.group("author")

    def extract_pypi_pkg_name(self):
        pkg_regexp = re.compile("^Name: (?P<pkg_name>[a-zA-Z0-9_-]+)", re.MULTILINE)
        match = pkg_regexp.search(self.__pip_show)
        if not match:
            raise ValueError("package name not found in 'pip show'")

        return match.group("pkg_name")

    def extract_requires(self):
        match = self.__requires_regexp.search(self.__pip_show)
        if not match:
            return []

        return match.group().split(": ")[1].split(", ")
