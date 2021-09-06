# Copyright (C) 2018-2021 CS GROUP - France. All Rights Reserved.
#
# This file is part of the Prewikka program.
#
# SPDX-License-Identifier: BSD-2-Clause
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIEDi
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""
Tests for `prewikka.log`.
"""

import os
import sys

import pytest

from prewikka.config import ConfigSection
from prewikka.log import Log
from tests.utils.vars import TEST_DOWNLOAD_DIR


_LOG_FILE = os.path.join(TEST_DOWNLOAD_DIR, 'prewikka.logs')


@pytest.fixture(scope='function')
def log_fixtures(request):
    """
    Fixtures for tests of `prewikka.log`.
    """
    typ, options = request.param
    conf = ConfigSection(typ)
    for k, v in options.items():
        conf[k] = v

    log = Log([conf])

    def tear_down():
        log._logger.handlers = []

    request.addfinalizer(tear_down)

    return log


@pytest.mark.parametrize("log_fixtures", [("syslog", {"level": "debug"})], indirect=True)
def test_log(log_fixtures):
    """
    Test `prewikka.log.Log` class.
    """
    log = log_fixtures
    log.log(10, 'foo bar')
    log.log(20, 'foo bar')
    log.log(30, 'foo bar')
    log.log(40, 'foo bar')
    log.log(50, 'foo bar')

    with pytest.raises(KeyError):
        log.log(60, 'foo bar')

    # with exception
    log.log(10, TypeError())

    # request.web
    env.request.web.is_xhr = True
    log.log(10, 'foo bar')
    env.request.web.is_xhr = False

    env.request.web.is_stream = True
    log.log(10, 'foo bar')
    env.request.web.is_stream = False


@pytest.mark.parametrize("log_fixtures", [("syslog", {"level": "debug"})], indirect=True)
def test_log_syslog(log_fixtures):
    """
    Test `prewikka.log.Log` class.

    With syslog option.
    """
    log = log_fixtures
    log.log(10, 'foo bar')


@pytest.mark.parametrize("log_fixtures", [("file", {"level": "debug", "file": _LOG_FILE})], indirect=True)
def test_log_file(log_fixtures):
    """
    Test `prewikka.log.Log` class.

    With file option.
    """
    log = log_fixtures
    try:
        output_file_size = os.stat(_LOG_FILE).st_size
    except OSError:
        output_file_size = 0

    log.log(10, 'foo bar')

    assert output_file_size != os.stat(_LOG_FILE).st_size


@pytest.mark.xfail(reason='pytest upgrade required (3.0+)')
@pytest.mark.parametrize("log_fixtures", [("debug", {"level": "debug"})], indirect=True)
def test_log_stderr(log_fixtures):
    """
    Test `prewikka.log.Log` class.

    With stderr option.

    FIXME: with pytest 3+, a solution exists to disable std* captured by pytest.
    https://docs.pytest.org/en/3.0.0/capture.html#accessing-captured-output-from-a-test-function
    """
    log = log_fixtures
    initial_stderr = sys.stderr
    log.log(10, 'foo bar')

    assert initial_stderr != sys.stderr


@pytest.mark.parametrize("log_fixtures", [("smtp", {"level": "debug", "host": "localhost", "from": "user@localhost", "to": "root@localhost", "subject": "Prewikka Test"})], indirect=True)
def test_log_smtp(log_fixtures):
    """
    Test `prewikka.log.Log` class.

    With smtp option.
    """
    log = log_fixtures
    log.log(10, 'foo bar')


@pytest.mark.parametrize("log_fixtures", [("nteventlog", {"level": "debug"})], indirect=True)
def test_log_nteventlog(log_fixtures):
    """
    Test `prewikka.log.Log` class.

    With nteventlog option.
    """
    log = log_fixtures
    log.log(10, 'foo bar')


def test_log_invalid_format():
    """
    Test `prewikka.log.Log` class.

    With an invalid format.
    """
    conf = ConfigSection("somethinginvalid")
    conf.level = "debug"

    with pytest.raises(ValueError):
        Log([conf])
