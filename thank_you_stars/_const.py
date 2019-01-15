# encoding: utf-8

from __future__ import unicode_literals


PACKAGE_NAME = "thank-you-stars"


class StarStatus(object):
    STARRED = "starred"
    NOT_STARRED = "not starred"
    NOT_FOUND = "not found"
    NOT_AVAILABLE = "not available"


class Default(object):
    CONFIG_FILENAME = ".{:s}.json".format(PACKAGE_NAME)
    CONFIG_FILEPATH = "~/.{:s}.json".format(PACKAGE_NAME)
