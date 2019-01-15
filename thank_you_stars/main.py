#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import argparse
import errno
import os.path
import sys
from textwrap import dedent

import logbook
import msgfy
from github.GithubException import UnknownObjectException
from logbook.more import ColorizedStderrHandler
from subprocrunner import SubprocessRunner
from tqdm import tqdm

from .__version__ import __version__
from ._cache import CacheManager, CacheTime, CacheType
from ._config import app_config_mgr
from ._const import PACKAGE_NAME, Default, StarStatus
from ._extractor import GithubStarredInfoExtractor
from ._github import create_github_client
from ._logger import logger, set_log_level
from ._printer import print_starred_info
from ._starred import fetch_starred_repo_list


def parse_option():
    description = "Give stars a PyPI package and its dependencies."
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=description,
        epilog=dedent(
            """\
            Issue tracker: https://github.com/thombashi/{:s}/issues
            """.format(
                PACKAGE_NAME
            )
        ),
    )

    parser.add_argument(
        "target", help="""PyPI package name or path to the package source code directory"""
    )

    parser.add_argument("--version", action="version", version="%(prog)s {}".format(__version__))

    group = parser.add_argument_group("Configurations")
    group.add_argument("--token", help="GitHub personal access token that has public_repo scope.")
    group.add_argument(
        "--config",
        default=Default.CONFIG_FILEPATH,
        help=dedent(
            """\
            path to a conig file. the config file expected to contain token:
            { "token" : <GitHub personal access token that has public_repo scope> }
            (defaults to %(default)s).",
            """
        ),
    )
    group.add_argument(
        "--setup",
        action="store_true",
        default=False,
        help="setup token interactively, and then starring.",
    )

    group = parser.add_argument_group("Star Status")
    group.add_argument(
        "--check",
        action="store_true",
        default=False,
        help=dedent(
            """\
            list starred status for each package with tabular format and exit.
            does not actually star to found GitHub repositories.
            """
        ),
    )
    group.add_argument("-v", "--verbosity", action="count", help="increase output verbosity.")

    group = parser.add_argument_group("Repository Search")
    group.add_argument(
        "--depth",
        type=int,
        default=1,
        help=dedent(
            """\
            depth to recursively find dependencies of dependencies."
            0 means to star specified the package only.
            1 means to star specified the package and its dependencies.
            equals to 2 or greater will increase the depth of traverse
            that dependencies of dependencies.
            """
        ),
    )
    group.add_argument(
        "--include-owner-repo",
        action="store_true",
        default=False,
        help="starred to repositories that owned by you.",
    )
    group.add_argument(
        "--no-cache", action="store_true", default=False, help="disable the local caches."
    )

    parser.add_argument("--dry-run", action="store_true", default=False, help="Do no harm.")

    dest = "log_level"
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--debug",
        dest=dest,
        action="store_const",
        const=logbook.DEBUG,
        default=logbook.INFO,
        help="for debug print.",
    )
    group.add_argument(
        "--quiet",
        dest=dest,
        action="store_const",
        const=logbook.NOTSET,
        default=logbook.INFO,
        help="suppress execution log messages.",
    )

    group = parser.add_argument_group("Debug")
    group.add_argument(
        "--stacktrace",
        dest="is_output_stacktrace",
        action="store_true",
        default=False,
        help="""print stack trace for debug information.
        --debug option required to see the debug print.
        """,
    )

    return parser.parse_args()


def initialize_cli(options):
    debug_format_str = (
        "[{record.level_name}] {record.channel} {record.func_name} "
        "({record.lineno}): {record.message}"
    )
    if options.log_level == logbook.DEBUG:
        info_format_str = debug_format_str
    else:
        info_format_str = "[{record.level_name}] {record.channel}: {record.message}"

    ColorizedStderrHandler(level=logbook.DEBUG, format_string=debug_format_str).push_application()
    ColorizedStderrHandler(level=logbook.INFO, format_string=info_format_str).push_application()

    set_log_level(options.log_level)
    SubprocessRunner.is_save_history = True

    if options.is_output_stacktrace:
        SubprocessRunner.is_output_stacktrace = options.is_output_stacktrace


def extract_package_name(options):
    if options.target and options.target != ".":
        return options.target

    if os.path.isfile("setup.py"):
        runner = SubprocessRunner(["python", "setup.py", "--name"])
        if runner.run() == 0:
            return runner.stdout.strip().lower()

    raise ValueError("no package found")


def star_repository(github_client, starred_info_set, cache_mgr_map, options):
    github_user = github_client.get_user()
    starred_count = 0

    for starred_info in sorted(starred_info_set):
        if starred_info.star_status == StarStatus.STARRED:
            logger.info("skip already starred: {}".format(starred_info.github_repo_id))
            continue

        if starred_info.is_owned and not options.include_owner_repo:
            logger.info("skip owned repository: {}".format(starred_info.github_repo_id))
            continue

        if starred_info.star_status == StarStatus.NOT_FOUND:
            logger.info("skip GitHub repository not found: {}".format(starred_info.pypi_pkg_name))
            continue

        if starred_info.star_status == StarStatus.NOT_AVAILABLE:
            logger.info(
                "skip repository that could not get info: {}".format(starred_info.pypi_pkg_name)
            )
            continue

        logger.info("star to {}".format(starred_info.github_repo_id))
        if options.dry_run:
            continue

        try:
            repo_obj = github_client.get_repo(starred_info.github_repo_id)
        except UnknownObjectException as e:
            logger.error(msgfy.to_error_message(e))
            continue

        try:
            github_user.add_to_starred(repo_obj)
            starred_count += 1
            cache_mgr_map[CacheType.PYPI].remove_pkg_cache(
                starred_info.pypi_pkg_name, "starred_info"
            )
        except UnknownObjectException as e:
            logger.error(
                dedent(
                    """\
                    failed to star a repository. the personal access token
                    may not has public_repo scope.
                    msg: {}
                    """.format(
                        msgfy.to_error_message(e)
                    )
                )
            )
            continue

    if starred_count:
        cache_mgr_map[CacheType.GITHUB].remove_misc_cache(github_user.login, "starred")


def setup_config(options):
    if not options.setup:
        return

    return_code = app_config_mgr.configure()
    if return_code:
        sys.exit(return_code)


def main():
    options = parse_option()

    initialize_cli(options)

    setup_config(options)
    """
    if options.setup:
        return_code = app_config_mgr.configure()
        if return_code:
            return return_code
    """

    try:
        github_client = create_github_client(options)
    except RuntimeError as e:
        logger.error(e)
        return errno.EINVAL

    github_user = github_client.get_user()
    user_name = github_user.login
    cache_mgr_map = {CacheType.PIP: CacheManager(user_name, "pip", CacheTime(days=14))}

    if options.no_cache:
        cache_mgr_map[CacheType.GITHUB] = CacheManager(user_name, "GitHub", CacheTime(seconds=10))
        cache_mgr_map[CacheType.PYPI] = CacheManager(user_name, "PyPI", CacheTime(seconds=10))
    else:
        cache_mgr_map[CacheType.GITHUB] = CacheManager(user_name, "GitHub", CacheTime(days=14))
        cache_mgr_map[CacheType.PYPI] = CacheManager(user_name, "PyPI", CacheTime(days=14))

    try:
        extractor = GithubStarredInfoExtractor(
            github_client=github_client,
            max_depth=options.depth,
            cache_mgr_map=cache_mgr_map,
            starred_repo_id_list=fetch_starred_repo_list(
                github_client, cache_mgr_map[CacheType.GITHUB]
            ),
        )
    except ValueError as e:
        logger.error(e)
        return errno.EINVAL

    extractor.list_pypi_packages([(extract_package_name(options), 0)])

    starred_info_set = set()
    for pypi_pkg_name, depth in tqdm(
        sorted(extractor.repo_depth_map.items()), desc="Collect GitHub info"
    ):
        starred_info_set.add(extractor.extract_starred_info(pypi_pkg_name))

    if not starred_info_set:
        logger.error("starred information not found")
        return errno.ENOENT

    if options.check:
        print_starred_info(starred_info_set, extractor.repo_depth_map, options.verbosity)
        return 0

    star_repository(github_client, starred_info_set, cache_mgr_map, options)

    return 0


if __name__ == "__main__":
    sys.exit(main())
