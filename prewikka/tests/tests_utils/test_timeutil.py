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
Tests for `prewikka.utils.timeutil`.
"""

import datetime

from prewikka.utils import timeutil


class UTC(datetime.tzinfo):
    """
    TimeZone with UTC.
    """
    def utcoffset(self, datetime_):
        return datetime.timedelta(0)

    def tzname(self, datetime_):
        return 'UTC'

    def dst(self, datetime_):
        return datetime.timedelta(0)


def test_now():
    """
    Test `prewikka.utils.timeutil.now()`.
    """
    assert timeutil.now()


def test_utcnow():
    """
    Test `prewikka.utils.timeutil.utcnow()`.
    """
    assert timeutil.utcnow().ctime() == datetime.datetime.now(tz=UTC()).ctime()


def test_get_timestamp_from_str():
    """
    Test `prewikka.utils.timeutil.get_timestamp_from_string()`.
    """
    assert not timeutil.get_timestamp_from_string(None)
    assert not timeutil.get_timestamp_from_string('1973-11-28 21:33:09') == 123456789


def test_get_timestamp_from_dt():
    """
    Test `prewikka.utils.timeutil.get_timestamp_from_datetime()`.
    """
    datetime_ = datetime.datetime(year=1973, month=11, day=28, hour=21, minute=33, second=9, tzinfo=UTC())

    assert timeutil.get_timestamp_from_datetime(datetime_) == 123370389
