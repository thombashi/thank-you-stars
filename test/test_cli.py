"""
.. codeauthor:: Tsuyoshi Hombashi <tsuyoshi.hombashi@gmail.com>
"""

import errno
import sys

import pytest
from subprocrunner import SubprocessRunner


TYS_CMD = [sys.executable, "-m", "thank_you_stars"]
CHK_OPT = "--check"
DEPTH_OPT = "--depth"
DRY_RUN_OPT = "--dry-run"


class Test_tys:
    @pytest.mark.parametrize(
        ["command", "expected"],
        [
            [TYS_CMD + ["pytablewriter", DRY_RUN_OPT], 0],
            [TYS_CMD + ["thank-you-stars", CHK_OPT], 0],
            [TYS_CMD + ["thank-you-stars", CHK_OPT, "--include-owner-repo", DEPTH_OPT, 3], 0],
            [TYS_CMD + ["pytablewriter", DRY_RUN_OPT, DEPTH_OPT, -1], errno.EINVAL],
        ],
    )
    def test_normal(self, command, expected):
        runner = SubprocessRunner(command)
        assert runner.run() == expected, runner.stderr
