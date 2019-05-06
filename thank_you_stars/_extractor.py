# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import re
from collections import namedtuple
from difflib import SequenceMatcher

import msgfy
import retryrequests
import simplejson as json
from github.GithubException import RateLimitExceededException, UnknownObjectException
from mbstrdecoder import MultiByteStrDecoder
from pathvalidate import sanitize_filename
from tqdm import tqdm

from ._cache import CacheType, touch
from ._common import get_github_repo_id
from ._const import StarStatus
from ._logger import logger
from ._pip_show import PipShow


Contributor = namedtuple("Contributor", "login_name full_name")


class _GitHubRepoInfo(
    namedtuple("_GitHubRepoInfo", "owner_name repo_name repo_id url match_endpos")
):
    def equals_repo_name(self, name):
        return self.repo_name.lower() == name.lower()


class GitHubStarredInfo(
    namedtuple("GitHubStarredInfo", "pypi_pkg_name github_repo_id star_status is_owned url")
):
    def asdict(self):
        return self._asdict()

    def validate(self):
        if self.star_status not in (
            StarStatus.STARRED,
            StarStatus.NOT_STARRED,
            StarStatus.NOT_FOUND,
            StarStatus.NOT_AVAILABLE,
        ):
            raise ValueError("invalid value: {}".format(self.star_status))


class GithubStarredInfoExtractor(object):
    _MATCH_THRESHOLD = 0.6

    @property
    def repo_depth_map(self):
        return self.__repo_depth_map

    def __init__(self, github_client, max_depth, cache_mgr_map, starred_repo_id_list):
        self.__github_client = github_client
        self.__github_user = github_client.get_user()
        self.__max_depth = max_depth
        self.__starred_repo_id_list = starred_repo_id_list
        self.__repo_depth_map = {}

        self.__github_cache_mgr = cache_mgr_map[CacheType.GITHUB]
        self.__pypi_cache_mgr = cache_mgr_map[CacheType.PYPI]

        PipShow.cache_mgr = cache_mgr_map[CacheType.PIP]

        if self.__max_depth < 0:
            raise ValueError("max_depth must be greater or equal to zero")

        self.__github_repo_url_regexp = re.compile(
            "http[s]?://github.com/(?P<user_name>[a-zA-Z0-9][a-zA-Z0-9-]*?)/(?P<repo_name>[a-zA-Z0-9-_.]+)",
            re.MULTILINE,
        )

    def list_pypi_packages(self, pypi_pkg_name_queue):
        prev_depth = None
        total = self.__max_depth + 1
        i = 0

        with tqdm(desc="Collect package info", total=total) as pbar:
            while pypi_pkg_name_queue:
                pypi_pkg_name, depth = pypi_pkg_name_queue.pop(0)

                if prev_depth is None:
                    prev_depth = depth
                elif prev_depth != depth:
                    i += 1
                    pbar.update(1)
                    prev_depth = depth

                if pypi_pkg_name in self.__repo_depth_map:
                    logger.debug("skip: already checked: {}".format(pypi_pkg_name))
                    self.__repo_depth_map[pypi_pkg_name] = min(
                        depth, self.__repo_depth_map[pypi_pkg_name]
                    )
                    continue

                self.__repo_depth_map[pypi_pkg_name] = depth
                pip_show = PipShow.execute(pypi_pkg_name)

                if depth < self.__max_depth:
                    for require_package in pip_show.extract_requires():
                        # recursively search repositories
                        pypi_pkg_name_queue.append((require_package.lower(), depth + 1))

            while i < total:
                i += 1
                pbar.update(1)

    def extract_starred_info(self, pypi_pkg_name):
        cache_filepath = self.__pypi_cache_mgr.get_pkg_cache_filepath(pypi_pkg_name, "starred_info")

        if self.__github_cache_mgr.is_cache_available(cache_filepath):
            cache_data = self.__github_cache_mgr.load_json(cache_filepath)
            if cache_data:
                try:
                    info = GitHubStarredInfo(**cache_data)
                    info.validate()
                    return info
                except (TypeError, ValueError) as e:
                    logger.debug("failed to load cache: {}".format(msgfy.to_debug_message(e)))

        pip_show = PipShow.execute(pypi_pkg_name)
        github_repo_info = self.__find_github_repo_info_from_text(pip_show.content)

        if github_repo_info:
            return self.__register_starred_status(pypi_pkg_name, github_repo_info, depth=0)

        try:
            starred_info = self.__traverse_github_repo(pip_show, pypi_pkg_name, depth=0)
            if starred_info:
                return starred_info

            return GitHubStarredInfo(
                pypi_pkg_name=pypi_pkg_name,
                github_repo_id="[Repository not found]",
                star_status=StarStatus.NOT_FOUND,
                is_owned=None,
                url=None,
            )
        except RateLimitExceededException as e:
            logger.error(msgfy.to_error_message(e))

            return GitHubStarredInfo(
                pypi_pkg_name=pypi_pkg_name,
                github_repo_id="Exceed API rate limit",
                star_status=StarStatus.NOT_AVAILABLE,
                is_owned=None,
                url=None,
            )

    def __extract_github_repo_info(self, repo):
        owner_name = repo.owner.login
        repo_name = repo.name
        repo_id = "{}/{}".format(owner_name, repo_name)

        return _GitHubRepoInfo(
            owner_name=owner_name,
            repo_name=repo_name,
            repo_id=repo_id,
            url="https://github.com/{}".format(repo_id),
            match_endpos=None,
        )

    @staticmethod
    def __normalize_pkg_name(name):
        return re.sub("python", "", name, flags=re.IGNORECASE).lower()

    def __fetch_pypi_info(self, pypi_pkg_name):
        cache_filepath = self.__pypi_cache_mgr.get_pkg_cache_filepath(pypi_pkg_name, "pypi_desc")

        if self.__pypi_cache_mgr.is_cache_available(cache_filepath):
            logger.debug("load PyPI info cache: {}".format(cache_filepath))

            cache_data = self.__pypi_cache_mgr.load_json(cache_filepath)
            if cache_data:
                return cache_data

        r = retryrequests.get("https://pypi.org/pypi/{}/json".format(pypi_pkg_name))
        if r.status_code != 200:
            return None

        pypi_info = r.json().get("info")

        with cache_filepath.open(mode="w") as f:
            logger.debug("write PyPI info cache: {}".format(cache_filepath))
            f.write(json.dumps(pypi_info))

        return pypi_info

    def __find_github_repo_info_from_text(self, text, pos=0):
        match = self.__github_repo_url_regexp.search(text, pos)

        if not match:
            return None

        owner_name = match.group("user_name")
        repo_name = match.group("repo_name")
        repo_id = "{}/{}".format(owner_name, repo_name)
        negative_cache_filepath = self.__github_cache_mgr.get_misc_cache_filepath(
            repo_id, "negative"
        )

        if self.__github_cache_mgr.is_cache_available(negative_cache_filepath):
            return None

        try:
            repo_obj = self.__github_client.get_repo(repo_id)  # noqa: W0612
        except UnknownObjectException as e:
            if e.status == 404:
                logger.debug(
                    "create negative cache for a GitHub repo: {}".format(negative_cache_filepath)
                )
                touch(negative_cache_filepath)

                return None

            raise

        return _GitHubRepoInfo(
            owner_name=owner_name,
            repo_name=repo_name,
            repo_id=repo_id,
            url="https://github.com/{}".format(repo_id),
            match_endpos=match.endpos,
        )

    def __traverse_github_repo(self, pip_show, pypi_pkg_name, depth):
        pypi_info = self.__fetch_pypi_info(pypi_pkg_name)
        negative_cache_filepath = self.__pypi_cache_mgr.get_pkg_cache_filepath(
            pypi_pkg_name, "negative"
        )

        if self.__github_cache_mgr.is_cache_available(negative_cache_filepath):
            logger.debug(
                " negative cache for a PyPI package found: {}".format(negative_cache_filepath)
            )
            return None

        if pypi_info:
            pos = 0

            while True:
                github_repo_info = self.__find_github_repo_info_from_text(
                    pypi_info.get("description"), pos
                )

                if not github_repo_info:
                    break

                pos = github_repo_info.match_endpos

                if github_repo_info.equals_repo_name(pypi_pkg_name):
                    return self.__register_starred_status(pypi_pkg_name, github_repo_info, depth)

            logger.debug("search at github: {}".format(pypi_pkg_name))
            results = self.__github_client.search_repositories(
                query="{} language:python".format(pypi_pkg_name), sort="stars", order="desc"
            )
            author_name = pip_show.extract_author()
            author_email = pypi_info.get("author_email")

            for i, repo in enumerate(results.get_page(0)):
                if self.__calc_match_ratio(pypi_pkg_name, repo.name) < self._MATCH_THRESHOLD:
                    continue

                if i > 4:
                    break

                github_repo_info = self.__extract_github_repo_info(repo)

                if self.__search_github_repo(
                    github_repo_info.repo_id, author_name, "author_name"
                ) and self.__search_github_repo(
                    github_repo_info.repo_id, author_email, "author_email"
                ):
                    return self.__register_starred_status(pypi_pkg_name, github_repo_info, depth)

                try:
                    if author_email.rsplit(".", 1)[0] == repo.organization.email.rsplit(".", 1)[0]:
                        return self.__register_starred_status(
                            pypi_pkg_name, github_repo_info, depth
                        )
                except AttributeError:
                    pass

                if self.__search_contributor_github(repo, pypi_pkg_name, author_name):
                    return self.__register_starred_status(pypi_pkg_name, github_repo_info, depth)

            logger.debug(
                "create negative cache for a PyPI package: {}".format(negative_cache_filepath)
            )
            touch(negative_cache_filepath)

        return None

    def __calc_match_ratio(self, a, b):
        if not a or not b:
            return 0

        return SequenceMatcher(
            a=self.__normalize_pkg_name(a), b=self.__normalize_pkg_name(b)
        ).ratio()

    def __match_contributor(self, repo_id, pip_author_name, github_contributor_name):
        for author_name in pip_author_name.split(", "):
            match_ratio = self.__calc_match_ratio(author_name, github_contributor_name)
            if match_ratio >= self._MATCH_THRESHOLD:
                logger.debug(
                    "found contributor: repo={}, github_user={}, pip_author={}, match_ratio={}".format(
                        repo_id, github_contributor_name, author_name, match_ratio
                    )
                )
                return True

        return False

    def __search_github_repo(self, repo_id, search_value, category_name):
        cache_filepath = self.__github_cache_mgr.get_misc_cache_filepath(
            "/".join([repo_id, category_name]), sanitize_filename(search_value)
        )

        msg_template = "source {result} include {category}: repo={repo} path={path}"

        if self.__github_cache_mgr.is_cache_available(cache_filepath):
            with cache_filepath.open() as f:
                try:
                    if int(f.read()):
                        logger.debug(
                            msg_template.format(
                                result="found",
                                category=category_name,
                                repo=repo_id,
                                path=cache_filepath,
                            )
                        )
                        return True
                    else:
                        logger.debug(
                            msg_template.format(
                                result="not found",
                                category=category_name,
                                repo=repo_id,
                                path=cache_filepath,
                            )
                        )
                        return False
                except ValueError as e:
                    logger.warn(msgfy.to_error_message(e))

        query = "{} in:file language:python repo:{}".format(search_value, repo_id)
        logger.debug("search {}: {}".format(category_name, query))
        results = self.__github_client.search_code(query)
        search_regexp = re.compile(search_value, re.MULTILINE)

        with cache_filepath.open(mode="w") as f:
            for content_file in results.get_page(0):
                decoded_content = MultiByteStrDecoder(content_file.decoded_content).unicode_str
                if not search_regexp.search(decoded_content):
                    continue

                logger.debug(
                    msg_template.format(
                        result="found", category=category_name, repo=repo_id, path=content_file.path
                    )
                )

                f.write("1")
                return True

            f.write("0")

        return False

    def __search_contributor_github(self, repo, pypi_pkg_name, author_name):
        repo_id = get_github_repo_id(repo)
        cache_filepath = self.__github_cache_mgr.get_misc_cache_filepath(repo_id, "contributors")

        if self.__github_cache_mgr.is_cache_available(cache_filepath):
            logger.debug("load contributors cache: {}".format(cache_filepath))

            with cache_filepath.open() as f:
                for line in f:
                    contributor = Contributor(**json.loads(line))

                    if self.__match_contributor(repo_id, author_name, contributor.full_name):
                        return True

                    if self.__match_contributor(repo_id, author_name, contributor.login_name):
                        return True

            logger.debug(
                "contributor not found in the contributors cache: pkg={}, author={}".format(
                    pypi_pkg_name, author_name
                )
            )

            return False

        logger.debug("find contributors: {}".format(repo_id))
        with cache_filepath.open(mode="w") as f:
            for contributor in repo.get_contributors():
                contributor_map = {"login_name": contributor.login, "full_name": contributor.name}
                f.write("{}\n".format(json.dumps(contributor_map)))

                for contributor_name in (contributor.name, contributor.login):
                    if self.__match_contributor(repo_id, author_name, contributor_name):
                        logger.debug(
                            "found contributor: auth={}, contributor={}".format(
                                author_name, contributor_name
                            )
                        )
                        return True

        logger.debug("author not found in the github repository: {}".format(repo_id))

        return False

    def __register_starred_status(self, pypi_pkg_name, repo_info, depth):
        repo_id = repo_info.repo_id
        logger.debug("found a GitHub repository: {}".format(repo_id))

        starred_info = GitHubStarredInfo(
            pypi_pkg_name=pypi_pkg_name,
            github_repo_id=repo_id,
            star_status=StarStatus.STARRED
            if repo_id in self.__starred_repo_id_list
            else StarStatus.NOT_STARRED,
            is_owned=self.__github_user.login == repo_info.owner_name,
            url=repo_info.url,
        )

        cache_filepath = self.__pypi_cache_mgr.get_pkg_cache_filepath(pypi_pkg_name, "starred_info")
        logger.debug("write starred_info cache: {}".format(cache_filepath))
        with cache_filepath.open(mode="w") as f:
            json.dump(starred_info.asdict(), f, indent=4)

        return starred_info
