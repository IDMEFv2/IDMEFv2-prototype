# Copyright (C) 2021 CS GROUP - France. All Rights Reserved.
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
Tests for `prewikka.dataprovider.parsers.criteria`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from prewikka.dataprovider import Criterion, ParserError
from prewikka.dataprovider.parsers.criteria import parse
from tests.tests_dataprovider.utils import criteria_equal


def test_parse():
    """
    Test `prewikka.dataprovider.parsers.criteria.parse()` method.
    """
    # Single-quoted string
    assert criteria_equal(
        parse("alert.classification.text = 'foo'"),
        Criterion("alert.classification.text", "==", "foo")
    )

    # Double-quoted string
    assert criteria_equal(
        parse("alert.classification.text = \"foo\""),
        Criterion("alert.classification.text", "==", "foo")
    )

    # Unquoted string
    assert criteria_equal(
        parse("alert.classification.text = foo"),
        Criterion("alert.classification.text", "==", "foo")
    )

    # Escaping quote
    assert criteria_equal(
        parse("alert.classification.text <> \"a\\\"b\""),
        Criterion("alert.classification.text", "<>", "a\"b")
    )

    # Handling backslash
    assert criteria_equal(
        parse("alert.classification.text <> '*a\\*b\\\\*'"),
        Criterion("alert.classification.text", "<>", "*a\\*b\\\\*")
    )

    # Unknown operator
    with pytest.raises(ParserError):
        parse("alert.classification.text >< foo")

    # Path-only
    assert criteria_equal(
        parse("alert.classification.text"),
        Criterion("alert.classification.text", "!=", None)
    )

    # Boolean operators
    assert criteria_equal(
        parse("(alert.classification.text = foo || alert.classification.text = bar) && !alert.assessment.impact.description"),
        (Criterion("alert.classification.text", "==", "foo") | Criterion("alert.classification.text", "==", "bar")) &
        Criterion(operator="!", right=Criterion("alert.assessment.impact.description", "!=", None))
    )
