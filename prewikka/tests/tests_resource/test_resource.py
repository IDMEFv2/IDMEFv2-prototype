# Copyright (C) 2018-2020 CS GROUP - France. All Rights Reserved.
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
Tests for `prewikka.resource`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka.resource import Link, CSSLink, JSLink, HTMLSource, CSSSource, JSSource, HTMLNode
from prewikka.utils import json


def test_link():
    """
    Test `prewikka.resource.Link` class.
    """
    Link()


def test_css_link():
    """
    Test `prewikka.resource.CSSLink` class.
    """
    assert text_type(CSSLink('style.css')) == '<link rel="stylesheet" type="text/css" href="style.css" />'


def test_js_link():
    """
    Test `prewikka.resource.JSLink` class.
    """
    assert text_type(JSLink('script.js')) == '<script type="text/javascript" src="script.js"></script>'


def test_html_source():
    """
    Test `prewikka.resource.HTMLSource` class.
    """
    HTMLSource()


def test_css_source():
    """
    Test `prewikka.resource.CSSSource` class.
    """
    assert text_type(CSSSource('body > div {overflow: auto;}')) == '<style type="text/css">body > div {overflow: auto;}</style>'


def test_js_source():
    """
    Test `prewikka.resource.JSSource` class.
    """
    assert text_type(JSSource('var foo = bar.baz() > 0;')) == '<script type="text/javascript">var foo = bar.baz() > 0;</script>'


def test_html_node():
    """
    Test `prewikka.resource.HTMLNode` class.
    """
    node = HTMLNode('a')

    assert node.to_string() == str(node)
    assert json.dumps(node)

    node2 = HTMLNode('a', **{'_icon': 'gears', 'class': 'foobar', 'test': 'true'})

    assert str(node2)

    assert not node == node2

    assert node < node2
