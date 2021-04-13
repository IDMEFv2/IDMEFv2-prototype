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
Tests for `prewikka.views.crontab`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy

import pytest

from prewikka import crontab


@pytest.fixture(scope='function')
def crontab_fixtures(request):
    """
    Fixture for crontab tests.

    Scope is function because we edit crontabs in tests.
    :return: view for crontab.
    :rtype: prewikka.view.View
    """
    view = env.viewmanager.get_view(request.param)
    backup_parameters = deepcopy(env.request.parameters)
    env.request.parameters = view.view_parameters(view)
    env.request.view = view
    view.process_parameters()

    crontab_enabled_1 = crontab.add('crontab_enabled_1', '*/2 * * * *', user=env.request.user)
    crontab_enabled_2 = crontab.add('crontab_enabled_2', '37 13 * * *', user=env.request.user)
    crontab_enabled_3 = crontab.add('crontab_enabled_3', '12 * * * *', user=env.request.user)
    crontab_disabled_1 = crontab.add('crontab_disabled_1', '*/2 * * * *', user=env.request.user, enabled=False)
    crontab_disabled_2 = crontab.add('crontab_disabled_2', '37 13 * * *', user=env.request.user, enabled=False)
    crontab_disabled_3 = crontab.add('crontab_disabled_3', '12 * * * *', user=env.request.user, enabled=False)

    def tear_down():
        """
        TearDown

         - Clean "Prewikka_Crontab" table
         - Restore "env.request.parameters" to initial values
        """
        env.db.query('DELETE FROM Prewikka_Crontab')
        env.request.parameters = backup_parameters

    request.addfinalizer(tear_down)

    return {
        'view': view,
        'crontab_enabled_1': crontab_enabled_1,
        'crontab_enabled_2': crontab_enabled_2,
        'crontab_enabled_3': crontab_enabled_3,
        'crontab_disabled_1': crontab_disabled_1,
        'crontab_disabled_2': crontab_disabled_2,
        'crontab_disabled_3': crontab_disabled_3,
    }


@pytest.mark.parametrize("crontab_fixtures", ["crontabview.list"], indirect=True)
def test_list(crontab_fixtures):
    """
    Test `prewikka.view.crontab.CrontabView.list` view.
    """
    view = crontab_fixtures.get('view')

    assert view.render()


@pytest.mark.parametrize("crontab_fixtures", ["crontabview.disable"], indirect=True)
def test_disable(crontab_fixtures):
    """
    Test `prewikka.view.crontab.CrontabView.disable` view.
    """
    view = crontab_fixtures.get('view')

    crontab_1 = crontab_fixtures.get('crontab_enabled_1')

    # count crontab enabled
    crontab_enabled_count = len([ct for ct in crontab.list() if ct.enabled])

    assert crontab_enabled_count >= 1  # raise error if no crontab enabled in fixtures

    env.request.parameters['id'] = [crontab_1]

    assert view.render()

    # ensure crontab is now disabled
    assert len([ct for ct in crontab.list() if ct.enabled]) == crontab_enabled_count - 1


@pytest.mark.parametrize("crontab_fixtures", ["crontabview.disable"], indirect=True)
def test_disable_multiple(crontab_fixtures):
    """
    Test `prewikka.view.crontab.CrontabView.disable` view.

    Multiple crontab.
    """
    view = crontab_fixtures.get('view')

    crontab_1 = crontab_fixtures.get('crontab_enabled_2')
    crontab_2 = crontab_fixtures.get('crontab_enabled_3')

    # count crontab enabled
    crontab_enabled_count = len([ct for ct in crontab.list() if ct.enabled])

    assert crontab_enabled_count >= 2  # raise error if no crontab enabled in fixtures

    env.request.parameters['id'] = [crontab_1, crontab_2]

    assert view.render()

    # ensure crontab are now disabled
    assert len([ct for ct in crontab.list() if ct.enabled]) == crontab_enabled_count - 2


@pytest.mark.parametrize("crontab_fixtures", ["crontabview.enable"], indirect=True)
def test_enable(crontab_fixtures):
    """
    Test `prewikka.view.crontab.CrontabView.enable` view.
    """
    view = crontab_fixtures.get('view')

    crontab_1 = crontab_fixtures.get('crontab_disabled_1')

    # count crontab enabled
    crontab_disabled_count = len([ct for ct in crontab.list() if not ct.enabled])

    assert crontab_disabled_count >= 1  # raise error if no crontab disabled in fixtures

    env.request.parameters['id'] = [crontab_1]

    assert view.render()

    # ensure crontab is now enabled
    assert len([ct for ct in crontab.list() if not ct.enabled]) == crontab_disabled_count - 1


@pytest.mark.parametrize("crontab_fixtures", ["crontabview.enable"], indirect=True)
def test_enable_multiple(crontab_fixtures):
    """
    Test `prewikka.view.crontab.CrontabView.enable` view.

    Multiple crontab.
    """
    view = crontab_fixtures.get('view')

    crontab_1 = crontab_fixtures.get('crontab_disabled_2')
    crontab_2 = crontab_fixtures.get('crontab_disabled_3')

    # count crontab disabled
    crontab_disabled_count = len([ct for ct in crontab.list() if not ct.enabled])

    assert crontab_disabled_count >= 2  # raise error if no crontab disabled in fixtures

    env.request.parameters['id'] = [crontab_1, crontab_2]

    assert view.render()

    # ensure crontab are now enabled
    assert len([ct for ct in crontab.list() if not ct.enabled]) == crontab_disabled_count - 2


@pytest.mark.parametrize("crontab_fixtures", ["crontabview.save"], indirect=True)
def test_save(crontab_fixtures):
    """
    Test `prewikka.view.crontab.CrontabView.save` view.
    """
    view = crontab_fixtures.get('view')
    crontab_1 = crontab_fixtures.get('crontab_disabled_1')

    schedule = '0 12 * * *'
    params = {
        'name': 'New name',
        'schedule': schedule,
        'quick-schedule': schedule,
        'user': env.request.user,
        'ext_type': None,
        'ext_id': None,
        'enabled': True
    }

    env.request.parameters = params

    assert view.render(crontab_1)


@pytest.mark.parametrize("crontab_fixtures", ["crontabview.edit"], indirect=True)
def test_edit(crontab_fixtures):
    """
    Test `prewikka.view.crontab.CrontabView.edit` view.
    """
    view = crontab_fixtures.get('view')
    crontab_1 = crontab_fixtures.get('crontab_disabled_1')

    assert view.render(crontab_1)
