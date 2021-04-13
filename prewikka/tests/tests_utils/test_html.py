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
Tests for `prewikka.utils.html`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka.utils.html import escape, escapejs
from prewikka.utils.html.helpers import selected, checked, disabled


def test_escape():
    """
    Test `prewikka.utils.html.escape()`.
    """
    assert text_type(escape(None)) == ''
    assert text_type(escape('')) == ''
    assert text_type(escape('foo')) == 'foo'
    assert text_type(escape('foo bar')) == 'foo bar'
    assert text_type(escape('<script>alert();</script>')) == '&lt;script&gt;alert();&lt;/script&gt;'


def test_escapejs():
    """
    Test `prewikka.utils.html.escapejs()`.
    """
    assert text_type(escapejs('')) == '""'
    assert text_type(escapejs('foo')) == '"foo"'
    assert text_type(escapejs('foo bar')) == '"foo bar"'
    assert text_type(escapejs('<script>alert();</script>')) == '"\\u003cscript\\u003ealert();\\u003c/script\\u003e"'


def test_selected():
    """
    Test `prewikka.utils.html.selected()`.
    """
    assert selected('') == ''
    assert selected('foo') == 'selected'
    assert selected(False) == ''
    assert selected(True) == 'selected'


def test_checked():
    """
    Test `prewikka.utils.html.checked()`.
    """
    assert checked('') == ''
    assert checked('foo') == 'checked'
    assert checked(False) == ''
    assert checked(True) == 'checked'


def test_disabled():
    """
    Test `prewikka.utils.html.disabled()`.
    """
    assert disabled('') == ''
    assert disabled('foo') == 'disabled'
    assert disabled(False) == ''
    assert disabled(True) == 'disabled'
