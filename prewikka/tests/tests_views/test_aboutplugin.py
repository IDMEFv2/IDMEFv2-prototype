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
Tests for `prewikka.views.aboutplugin`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy

import pytest


@pytest.fixture
def aboutplugin_fixtures(request):
    """
    Fixture for aboutplugin tests.

    :return: view for aboutplugin.
    :rtype: prewikka.view.View
    """
    view = env.viewmanager.get_view(request.param)
    env.request.parameters = view.view_parameters(view)
    env.request.view = view

    return view


@pytest.mark.parametrize("aboutplugin_fixtures", ["aboutplugin.render_get"], indirect=True)
def test_render_get(aboutplugin_fixtures):
    """
    Test `prewikka.views.aboutplugin.render_get` view.
    """
    view = aboutplugin_fixtures

    view.render()


@pytest.mark.parametrize("aboutplugin_fixtures", ["aboutplugin.enable"], indirect=True)
def test_enable(aboutplugin_fixtures):
    """
    Test `prewikka.views.aboutplugin.enable` view.
    """
    view = aboutplugin_fixtures
    backup_parameters = deepcopy(env.request.parameters)

    env.request.parameters['enable_plugin'] = 'prewikka.views.filter.filter:FilterView'

    view.render()

    # clean
    env.request.parameters = backup_parameters


@pytest.mark.parametrize("aboutplugin_fixtures", ["aboutplugin.update"], indirect=True)
def test_update(aboutplugin_fixtures):
    """
    Test `prewikka.views.aboutplugin.update` view.
    """
    view = aboutplugin_fixtures

    view.render()
