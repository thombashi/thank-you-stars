# encoding: utf-8

from __future__ import absolute_import, unicode_literals

from ._common import get_github_repo_id
from ._logger import logger


def fetch_starred_repo_list(github_client, cache_mgr):
    github_user = github_client.get_user()
    cache_filepath = cache_mgr.get_misc_cache_filepath(github_user.login, "starred")

    if cache_mgr.is_cache_available(cache_filepath):
        logger.debug(
            "load starred repositories cache: user={}, path={}".format(
                github_user.login, cache_filepath
            )
        )
        with cache_filepath.open() as f:
            return [line.strip() for line in f]

    logger.debug(
        "write starred repositories cache: user={}, path={}".format(
            github_user.login, cache_filepath
        )
    )
    starred_repo_list = []
    with cache_filepath.open(mode="w") as f:
        for repo in github_user.get_starred():
            repo_id = get_github_repo_id(repo)

            f.write("{}\n".format(repo_id))
            starred_repo_list.append(repo_id)

    return starred_repo_list
