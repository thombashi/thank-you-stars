PACKAGE_NAME = "thank-you-stars"


class StarStatus:
    STARRED = "starred"
    NOT_STARRED = "not starred"
    NOT_FOUND = "not found"
    NOT_AVAILABLE = "not available"


class Default:
    CONFIG_FILENAME = ".{:s}.json".format(PACKAGE_NAME)
    CONFIG_FILEPATH = "~/.{:s}.json".format(PACKAGE_NAME)
