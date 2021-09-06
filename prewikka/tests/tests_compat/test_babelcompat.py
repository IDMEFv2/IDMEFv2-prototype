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
Tests for `prewikka.compat.babelcompat`.
"""

from datetime import timedelta

import pytest

from prewikka.compat.babelcompat import format_timedelta


def test_format_timedelta():
    """
    Test `prewikka.compat.babelcompat.format_timedelta` function.
    """
    # with integer
    assert format_timedelta(0) == '0 second'
    assert format_timedelta(3) == '3 second'
    assert format_timedelta(31) == '31 second'
    assert format_timedelta(314) == '5 minute'
    assert format_timedelta(3141) == '1 hour'
    assert format_timedelta(31415) == '9 hour'
    assert format_timedelta(314159) == '4 day'
    assert format_timedelta(3141592) == '1 month'
    assert format_timedelta(31415926) == '1 year'
    assert format_timedelta(314159265) == '10 year'
    assert format_timedelta(-3) == '3 second'
    assert format_timedelta(-31) == '31 second'
    assert format_timedelta(-314) == '5 minute'
    assert format_timedelta(-3141) == '1 hour'
    assert format_timedelta(-31415) == '9 hour'
    assert format_timedelta(-314159) == '4 day'
    assert format_timedelta(-3141592) == '1 month'
    assert format_timedelta(-31415926) == '1 year'
    assert format_timedelta(-314159265) == '10 year'

    # with timedelta
    assert format_timedelta(timedelta(seconds=42)) == '42 second'
    assert format_timedelta(timedelta(minutes=42)) == '42 minute'
    assert format_timedelta(timedelta(hours=2)) == '2 hour'
    assert format_timedelta(timedelta(days=2)) == '2 day'
    assert format_timedelta(timedelta(weeks=42)) == '10 month'
    assert format_timedelta(timedelta(seconds=-42)) == '42 second'
    assert format_timedelta(timedelta(minutes=-42)) == '42 minute'
    assert format_timedelta(timedelta(hours=-2)) == '2 hour'
    assert format_timedelta(timedelta(days=-2)) == '2 day'
    assert format_timedelta(timedelta(weeks=-42)) == '10 month'


def test_format_granularity():
    """
    Test `prewikka.compat.babelcompat.format_timedelta` function with `granularity` param.
    """
    assert format_timedelta(3, granularity='minute') == '1 minute'
    assert format_timedelta(31, granularity='minute') == '1 minute'
    assert format_timedelta(314, granularity='minute') == '5 minute'
    assert format_timedelta(3141, granularity='minute') == '1 hour'
    assert format_timedelta(-3, granularity='minute') == '1 minute'
    assert format_timedelta(-31, granularity='minute') == '1 minute'
    assert format_timedelta(-314, granularity='minute') == '5 minute'
    assert format_timedelta(-3141, granularity='minute') == '1 hour'


def test_format_add_direction():
    """
    Test `prewikka.compat.babelcompat.format_timedelta` function with `add_direction` param.
    """
    assert format_timedelta(3, add_direction=True) == 'in 3 second'
    assert format_timedelta(31, add_direction=True) == 'in 31 second'
    assert format_timedelta(314, add_direction=True) == 'in 5 minute'
    assert format_timedelta(3141, add_direction=True) == 'in 1 hour'
    assert format_timedelta(31415, add_direction=True) == 'in 9 hour'
    assert format_timedelta(314159, add_direction=True) == 'in 4 day'
    assert format_timedelta(3141592, add_direction=True) == 'in 1 month'
    assert format_timedelta(31415926, add_direction=True) == 'in 1 year'
    assert format_timedelta(314159265, add_direction=True) == 'in 10 year'
    assert format_timedelta(-3, add_direction=True) == '3 second ago'
    assert format_timedelta(-31, add_direction=True) == '31 second ago'
    assert format_timedelta(-314, add_direction=True) == '5 minute ago'
    assert format_timedelta(-3141, add_direction=True) == '1 hour ago'
    assert format_timedelta(-31415, add_direction=True) == '9 hour ago'
    assert format_timedelta(-314159, add_direction=True) == '4 day ago'
    assert format_timedelta(-3141592, add_direction=True) == '1 month ago'
    assert format_timedelta(-31415926, add_direction=True) == '1 year ago'
    assert format_timedelta(-314159265, add_direction=True) == '10 year ago'


@pytest.mark.xfail(reason='Issue #2515')
def test_format_timedelta_format():
    """
    Test `prewikka.compat.babelcompat.format_timedelta` function with `format` param.
    NOTE: format is not used in function (except for testing).
    """
    assert format_timedelta(3, format='narrow') == '3 second'
    assert format_timedelta(3, format='short') == '3 second'
    assert format_timedelta(3, format='medium') == '3 second'
    assert format_timedelta(3, format='long') == '3 second'

    with pytest.raises(Exception):
        format_timedelta(42, format='unknown')


def test_format_timedelta_threshold():
    """
    Test `prewikka.compat.babelcompat.format_timedelta` function with `threshold` param.
    """
    assert format_timedelta(12, threshold=12) == '12 second'
