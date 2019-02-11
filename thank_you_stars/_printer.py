# encoding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

import pydoc
from operator import itemgetter

import subprocrunner
from pytablewriter import MarkdownTableWriter
from pytablewriter.style import Style

from ._const import StarStatus


_NA = "n/a"

_star_status_map = {
    StarStatus.STARRED: "X",
    StarStatus.NOT_STARRED: "",
    StarStatus.NOT_AVAILABLE: _NA,
    StarStatus.NOT_FOUND: _NA,
}


def bool_to_checkmark(value):
    if value is True:
        return "X"
    if value is False:
        return ""

    return value


def pager(text):
    if subprocrunner.Which("less").is_exist():
        pydoc.pipepager(text, cmd="less --chop-long-lines --CLEAR-SCREEN")
    else:
        pydoc.pager(text)


def print_starred_info(starred_info_set, repo_depth_map, verbosity):
    records = []
    for info in sorted(starred_info_set):
        record = [
            info.pypi_pkg_name,
            info.github_repo_id,
            _star_status_map[info.star_status],
            info.is_owned
            if info.star_status in [StarStatus.STARRED, StarStatus.NOT_STARRED]
            else _NA,
            repo_depth_map[info.pypi_pkg_name.lower()],
            info.url,
        ]
        records.append(record)

    writer = MarkdownTableWriter()
    writer.headers = ["Package", "Repository", "Starred", "Owner"]
    if verbosity is not None:
        if verbosity >= 1:
            writer.headers += ["Depth"]

        if verbosity >= 2:
            writer.headers += ["URL"]

    writer.value_matrix = sorted(records, key=itemgetter(4, 0))  # sorted by depth
    writer.margin = 1
    writer.register_trans_func(bool_to_checkmark)
    writer.set_style("Starred", Style(align="center"))
    writer.set_style("Owner", Style(align="center"))
    pager(writer.dumps())
