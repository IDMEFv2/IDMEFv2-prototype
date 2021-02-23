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
Tests for `prewikka.utils.url`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka.utils import url


def test_mkdownload():
    """
    Test `prewikka.utils.url.mkdownload()`.
    """
    dl_file = url.mkdownload('test.txt')

    assert dl_file.__json__()['href']

    dl_file = url.mkdownload('test.txt', user=env.request.user)

    assert dl_file.__json__()['href']


def test_iri2uri():
    """
    Test `prewikka.utils.url.iri2uri()`.
    """
    assert url.iri2uri('http://domain.tld/foo bar.html') == 'http://domain.tld/foo%20bar.html'
    assert url.iri2uri('http://domain.tld/foo:bar.html') == 'http://domain.tld/foo:bar.html'
    assert url.iri2uri('HTTP://www.python.org/doc/#') == 'http://www.python.org/doc/'


def test_urlencode():
    """
    Test `prewikka.utils.url.urlencode()`.
    """
    url_encode = url.urlencode([('foo', 1), ('bar', 2), ('42', '&')])

    assert url_encode == 'foo=1&bar=2&42=%26'
