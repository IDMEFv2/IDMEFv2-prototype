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
Tests for `prewikka.dataprovider` except Criteron() class.
"""

import datetime

import pytest

from prewikka.dataprovider import to_datetime, ResultObject
from prewikka.error import PrewikkaUserError
from prewikka.utils.timeutil import tzutc


def test_to_datetime():
    """
    Test `prewikka.dataprovider.to_datetime` function.
    """
    correct_datetime = datetime.datetime(1973, 11, 29, 21, 33, 9, tzinfo=tzutc())

    assert to_datetime(123456789) == correct_datetime
    assert to_datetime(123456789.3) == correct_datetime.replace(microsecond=300000)
    assert to_datetime('123456789') == correct_datetime
    assert to_datetime('1973-11-29 21:33:09 UTC') == correct_datetime
    assert to_datetime('1973-11-29 21:33:09') == correct_datetime
    assert to_datetime(correct_datetime) == correct_datetime
    assert not to_datetime(None)

    with pytest.raises(PrewikkaUserError):
        to_datetime({})


def test_result_object():
    """
    Test `prewikka.dataprovider.ResultObject` class.
    """
    result = ResultObject({'foo': 'bar', '42': 42})

    assert result.preprocess_value('foobar') == 'foobar'
