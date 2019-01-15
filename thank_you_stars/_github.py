# encoding: utf-8

from __future__ import absolute_import, unicode_literals

from textwrap import dedent

from github import Github

from ._config import app_config_mgr


def extract_github_api_token(options):
    if options.token:
        return options.token

    token_error_msg = "specify personal access token with --token TOKEN or --setup option."

    try:
        configs = app_config_mgr.load()
    except ValueError:
        raise RuntimeError(
            dedent(
                """\
                GitHub personal access token not found in the config file {:s}. {:s}
                """.format(
                    app_config_mgr.config_filepath, token_error_msg
                )
            )
        )

    if not configs:
        raise RuntimeError(
            dedent(
                """\
                config file {:s} not found. {:s}
                """.format(
                    app_config_mgr.config_filepath, token_error_msg
                )
            )
        )

    return configs["token"].strip()


def create_github_client(options):
    return Github(extract_github_api_token(options), per_page=100)
