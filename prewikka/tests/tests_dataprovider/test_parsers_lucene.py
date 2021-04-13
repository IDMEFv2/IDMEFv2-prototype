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
Tests for `prewikka.dataprovider.parsers.lucene`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from prewikka.dataprovider import Criterion, ParserError
from prewikka.dataprovider.parsers.lucene import CriteriaTransformer, parse
from tests.tests_dataprovider.utils import criteria_equal


def test_parse():
    """
    Test `prewikka.dataprovider.parsers.criteria.parse()` method.
    """
    tr = CriteriaTransformer()

    # Single-quoted string
    assert criteria_equal(
        parse("alert.classification.text:'foo'", transformer=tr),
        Criterion("alert.classification.text", "<>*", "foo")
    )

    # Double-quoted string
    assert criteria_equal(
        parse("alert.classification.text:\"foo\"", transformer=tr),
        Criterion("alert.classification.text", "<>*", "foo")
    )

    # Unquoted string
    assert criteria_equal(
        parse("alert.classification.text:foo", transformer=tr),
        Criterion("alert.classification.text", "<>*", "foo")
    )

    # Space after colon
    assert criteria_equal(
        parse("alert.classification.text: foo", transformer=tr),
        Criterion("alert.classification.text", "<>*", "foo")
    )

    # Wildcard
    assert criteria_equal(
        parse("alert.classification.text:foo*", transformer=tr),
        Criterion("alert.classification.text", "~", "foo.*")
    )

    # Regex
    assert criteria_equal(
        parse("alert.classification.text:/foo|bar/", transformer=tr),
        Criterion("alert.classification.text", "~", "foo|bar")
    )

    # Inclusive range
    assert criteria_equal(
        parse("alert.target(0).service.port:[1 TO 1024]", transformer=tr),
        Criterion("alert.target(0).service.port", ">=", "1") & Criterion("alert.target(0).service.port", "<=", "1024")
    )

    # Escaping quote
    assert criteria_equal(
        parse("alert.classification.text:\"a\\\"b\"", transformer=tr),
        Criterion("alert.classification.text", "<>*", "a\"b")
    )

    # Handling backslash
    assert criteria_equal(
        parse("alert.classification.text:'*a\\*b\\\\*'", transformer=tr),
        Criterion("alert.classification.text", "<>*", "*a\\*b\\\\*")
    )

    # Required/excluded/optional clauses
    assert criteria_equal(
        parse("+alert.classification.text:foo alert.classification.text:bar -alert.classification.text:baz", transformer=tr),
        Criterion("alert.classification.text", "<>*", "foo") &
        Criterion(operator="!", right=Criterion("alert.classification.text", "<>*", "baz"))
    )

    # Unmatched parenthesis
    with pytest.raises(ParserError):
        parse("(alert.classification.text:foo")
