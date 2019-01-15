# encoding: utf-8

"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

from __future__ import print_function, unicode_literals

import errno

import pytest
from subprocrunner import SubprocessRunner


TYS_CMD = "thank-you-stars"
CHK_OPT = "--check"
DEPTH_OPT = "--depth"
DRY_RUN_OPT = "--dry-run"


class Test_tys(object):
    @pytest.mark.parametrize(
        ["command", "expected"],
        [
            [[TYS_CMD, "pytablewriter", DRY_RUN_OPT], 0],
            [[TYS_CMD, "thank-you-stars", CHK_OPT], 0],
            [[TYS_CMD, "thank-you-stars", CHK_OPT, "--include-owner-repo", DEPTH_OPT, 3], 0],
            [[TYS_CMD, "pytablewriter", DRY_RUN_OPT, DEPTH_OPT, -1], errno.EINVAL],
        ],
    )
    def test_normal(self, command, expected):
        assert SubprocessRunner(command).run() == expected
