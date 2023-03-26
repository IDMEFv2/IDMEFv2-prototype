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
Tests for `prewikka.response`.
"""

from collections import OrderedDict
import os

from prewikka.response import PrewikkaResponse, PrewikkaDownloadResponse, PrewikkaFileResponse, PrewikkaRedirectResponse
from tests.utils.vars import TEST_DATA_DIR


class FakeJsonObjClass(object):
    """
    Fake class with __json__ att for test suite.
    """
    foobar = 'bar'

    def __json__(self):
        return {'foo': self.foobar}


def test_prewikka_response():
    """
    Test `prewikka.response.PrewikkaResponse` class.
    """
    response = PrewikkaResponse()

    # response with specifics headers
    headers = OrderedDict(
        (
            ("Content-Type", "text/html"),
            ("Foo", "Bar")
        )
    )
    response_with_headers = PrewikkaResponse(headers=headers, data='Tests !')

    # empty content
    assert response.content() is None

    # add_ext_content()
    response.add_ext_content('foo', 'bar')

    # add_notification()
    response.add_notification('message')

    # content()
    assert response.content() is not None
    assert response_with_headers.content() == 'Tests !'

    # content() with XHR
    env.request.web.is_xhr = True
    response_xhr = PrewikkaResponse(data={'foo': 'bar'})

    assert '"foo": "bar"' in response_xhr.content()

    response_xhr_2 = PrewikkaResponse(data='foobar')

    assert response_xhr_2.content() == 'foobar'

    fooo = FakeJsonObjClass()
    response_xhr_3 = PrewikkaResponse(data=fooo)

    assert response_xhr_3.content() == '{"foo": "bar"}'

    env.request.web.is_xhr = False  # clean

    # write()
    response.write(env.request.web)


def test_prewikka_download_response():
    """
    Test `prewikka.response.PrewikkaDownloadResponse` class.
    """
    # valid file
    response = PrewikkaDownloadResponse('', filename='test.txt')
    response.write(env.request.web)

    # invalid file
    response2 = PrewikkaDownloadResponse('', filename='test')
    response2.write(env.request.web)

    # true file (not str)
    with open(os.path.join(TEST_DATA_DIR, 'file.txt')) as test_file:
        response3 = PrewikkaDownloadResponse(test_file, filename='test.txt')
        response3.write(env.request.web)

    # other possibilities
    response4 = PrewikkaDownloadResponse('', filename='test.jpg', type='image/jpeg')
    response4.write(env.request.web)

    response5 = PrewikkaDownloadResponse('')
    response5.write(env.request.web)

    response6 = PrewikkaDownloadResponse('', size=42)
    response6.write(env.request.web)


def test_prewikka_file_response():
    """
    Test `prewikka.response.PrewikkaFileResponse` class.
    """
    path = os.path.join(TEST_DATA_DIR, 'file.txt')

    # default response
    response = PrewikkaFileResponse(path)
    response.write(env.request.web)

    # modified-since
    env.request.web.headers['if-modified-since'] = '2012-01-19 17:21:00 UTC'
    response2 = PrewikkaFileResponse(path)
    response2.write(env.request.web)

    # modified-since + 304 code
    env.request.web.headers['if-modified-since'] = '2030-01-19 17:21:00 UTC'
    response3 = PrewikkaFileResponse(path)
    response3.write(env.request.web)


def test_prewikka_redirect_response():
    """
    Test `prewikka.response.PrewikkaRedirectResponse` class.
    """
    response = PrewikkaRedirectResponse('https://google.com')

    assert response.code == 302
