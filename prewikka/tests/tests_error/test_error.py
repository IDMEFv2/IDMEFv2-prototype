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
Tests for `prewikka.error`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from prewikka.error import RedirectionError, PrewikkaError, PrewikkaUserError, NotImplementedError
from prewikka.template import PrewikkaTemplate


def test_redirection_error():
    """
    Test `prewikka.error.RedirectionError` error.
    """
    error = RedirectionError('/', 302)

    with pytest.raises(RedirectionError):
        raise error

    assert error.respond()


def test_prewikka_error():
    """
    Test `prewikka.error.PrewikkaError` error.
    """
    error = PrewikkaError('An error occurred !')

    with pytest.raises(PrewikkaError):
        raise error

    assert str(error)
    assert error.respond()

    # empty message
    error = PrewikkaError('')

    with pytest.raises(PrewikkaError):
        raise error

    assert not str(error)
    assert error.respond()

    # name
    error = PrewikkaError('An error occurred !', name='Unknown error')

    with pytest.raises(PrewikkaError):
        raise error

    assert str(error)
    assert error.respond()

    # details
    error = PrewikkaError('An error occurred !', details='Some details about the error.')

    with pytest.raises(PrewikkaError):
        raise error

    assert str(error)
    assert error.respond()

    # log_priority
    error = PrewikkaError('An error occurred !', log_priority=40)

    with pytest.raises(PrewikkaError):
        raise error

    assert str(error)
    assert error.respond()

    # log_user
    error = PrewikkaError('An error occurred !', log_user='john')

    with pytest.raises(PrewikkaError):
        raise error

    assert str(error)
    assert error.respond()

    # template
    template = PrewikkaTemplate('prewikka', 'templates/baseview.mak')
    error = PrewikkaError('An error occurred !', template=template)

    with pytest.raises(PrewikkaError):
        raise error

    assert str(error)
    assert error.respond()

    # code
    error = PrewikkaError('An error occurred !', code=503)

    with pytest.raises(PrewikkaError):
        raise error

    assert str(error)
    assert error.respond()

    # traceback disabled then enabled
    backup_traceback = env.config.general.get('enable_error_traceback')
    env.config.general.enable_error_traceback = 'no'
    error = PrewikkaError('An error occurred !', template=template)
    env.config.general.enable_error_traceback = backup_traceback

    assert error.respond()

    # env.request.web.is_stream
    env.request.web.is_stream = not env.request.web.is_stream
    error = PrewikkaError('An error occurred !', template=template)

    assert error.respond()

    env.request.web.is_stream = not env.request.web.is_stream


def test_prewikka_user_error():
    """
    Test `prewikka.error.PrewikkaUserError` error.
    """
    # default
    error = PrewikkaUserError()

    with pytest.raises(PrewikkaUserError):
        raise error

    assert not str(error)

    # name
    error = PrewikkaUserError(name='NAME')

    with pytest.raises(PrewikkaUserError):
        raise error

    assert not str(error)  # message is required

    # message
    error = PrewikkaUserError(message='A message')

    with pytest.raises(PrewikkaUserError):
        raise error

    assert str(error)

    # name + message
    error = PrewikkaUserError(name='NAME', message='A message')

    with pytest.raises(PrewikkaUserError):
        raise error

    assert str(error)


def test_not_implemented_error():
    """
    Test `prewikka.error.NotImplementedError` error.
    """
    # default
    error = NotImplementedError()

    with pytest.raises(NotImplementedError):
        raise error

    assert str(error)
