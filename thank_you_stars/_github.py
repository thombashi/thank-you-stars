import os

from github import Github

from ._config import app_config_mgr
from ._logger import logger


def extract_github_api_token(options):
    if options.token:
        return options.token

    token_error_msg = "specify personal access token with --token TOKEN or --setup option."

    try:
        configs = app_config_mgr.load()
    except ValueError:
        logger.debug(
            "GitHub personal access token not found in the config file {:s}. {:s}".format(
                app_config_mgr.config_filepath, token_error_msg
            )
        )

    if configs and configs.get("token"):
        return configs["token"].strip()

    logger.debug(
        "config file {:s} not found. {:s}".format(app_config_mgr.config_filepath, token_error_msg)
    )

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        logger.debug("GITHUB_TOKEN not defined")

    return token


def create_github_client(options):
    return Github(extract_github_api_token(options), per_page=100)
