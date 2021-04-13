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
Tests for `prewikka.baseview`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import copy

import pytest

from prewikka import hookmanager
from prewikka.error import PrewikkaUserError
from prewikka.utils import AttrObj, mkdownload
from tests.utils.fixtures import load_view_for_fixtures


@pytest.fixture()
def baseview_fixtures(request):
    """
    Fixtures for tests of `prewikka.baseview`.
    """
    # view
    load_view_for_fixtures('BaseView.render')

    # dataset
    backup_dataset = copy(env.request.dataset)
    dataset = {'document': AttrObj()}
    env.request.dataset = dataset

    def tear_down():
        """
        TearDown
        """
        env.request.dataset = backup_dataset

    request.addfinalizer(tear_down)


def test_baseview_download(baseview_fixtures):
    """
    Test `prewikka.baseview.BaseView.download` method.
    """
    from prewikka.baseview import BaseView

    base_view = BaseView()

    # invalid user
    with pytest.raises(PrewikkaUserError):
        base_view.download('invalid_user', 42, 'test.txt')

    # valid user
    filename = 'test.txt'
    file_created = mkdownload(filename, user=env.request.user.name)
    base_view.download(env.request.user.name, file_created._id, file_created._dlname)

    # no user
    with pytest.raises(PrewikkaUserError):
        filename = 'test2.txt'
        file_created = mkdownload(filename)
        base_view.download(True, file_created._id, file_created._dlname)


def test_baseview_logout(baseview_fixtures):
    """
    Test `prewikka.baseview.BaseView.logout` method.
    """
    from prewikka.baseview import BaseView

    base_view = BaseView()

    assert base_view.logout().code == 302


def test_baseview_render(baseview_fixtures):
    """
    Test `prewikka.baseview.BaseView.render` method.
    """
    from prewikka.baseview import BaseView

    base_view = BaseView()

    # register a fake HOOK to test all lines in baseview
    hookmanager.register('HOOK_LOAD_HEAD_CONTENT', '<script src="foo.js"></script>')
    hookmanager.register('HOOK_LOAD_BODY_CONTENT', '<foo>bar</foo>')

    # default render
    base_view.render()

    # no user
    backup_user = env.request.user
    env.request.user = None
    base_view.render()
    env.request.user = backup_user

    # clean
    hookmanager.unregister('HOOK_LOAD_HEAD_CONTENT', '<script src="foo.js"></script>')
    hookmanager.unregister('HOOK_LOAD_BODY_CONTENT', '<foo>bar</foo>')
