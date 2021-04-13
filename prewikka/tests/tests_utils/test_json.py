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
Tests for `prewikka.utils.json`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from datetime import datetime
from StringIO import StringIO

import pytest

from prewikka.dataprovider import Criterion
from prewikka.utils import json


class FakeClass(object):
    """
    Fake class for tests only.
    """
    def __init__(self):
        self.xyz = 1337


def test_json_object():
    """
    Test prewikka.utils.json.JSONObject().
    """
    obj = json.JSONObject()

    assert hasattr(obj, '__jsonobj__')


def test_load():
    """
    Test prewikka.utils.json.load().
    """
    io_stream = StringIO('["streaming API"]')

    assert json.load(io_stream) == ['streaming API']


def test_loads():
    """
    Test prewikka.utils.json.loads().
    """
    assert json.loads('["foo", {"bar": ["baz", null, 1.0, 2]}]') == ['foo', {'bar': ['baz', None, 1.0, 2]}]
    assert json.loads('"\\"foo\\bar"') == '"foo\x08ar'


def test_dump():
    """
    Test prewikka.utils.json.dumps().
    """
    io_stream = StringIO()
    json.dump(['streaming API'], io_stream)

    assert io_stream.getvalue() == '["streaming API"]'


def test_dumps():
    """
    Test prewikka.utils.json.dump().
    """
    assert json.dumps(['foo', {'bar': ['baz', None, 1.0, 2]}]) == '["foo", {"bar": ["baz", null, 1.0, 2]}]'
    assert json.dumps('"foo\x08ar') == '"\\"foo\\bar"'

    # Prewikka objects
    criterion = Criterion('alert.messageid', '=', 'fakemessageid')
    criterion_dumps = json.dumps(criterion)

    assert '{"__prewikka_class__": ["Criterion"' in criterion_dumps
    assert '"operator": "="' in criterion_dumps
    assert '"right": "fakemessageid"' in criterion_dumps
    assert '"left": "alert.messageid"' in criterion_dumps

    # datetime object
    assert json.dumps(datetime(year=2012, month=10, day=12, hour=0, minute=0, second=0)) == \
        '"2012-10-12 00:00:00"'

    # object not JSON serializable
    fake_obj = FakeClass()

    with pytest.raises(TypeError):
        json.dumps(fake_obj)
