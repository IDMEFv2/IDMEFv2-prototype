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
Tests for `prewikka.views.agents`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy
from datetime import datetime, timedelta

import pytest

from tests.tests_views.utils import create_heartbeat, delete_heartbeat, get_heartbeat, create_alert, get_alert


@pytest.fixture
def agents_fixtures(request):
    """
    Fixture for agents tests.

    :return: view for agents.
    :rtype: prewikka.view.View
    """
    view = env.viewmanager.get_view(request.param)
    env.request.parameters = view.view_parameters(view)
    env.request.view = view
    view.process_parameters()

    env.idmef_db = env.dataprovider._backends["alert"]._db

    return view


@pytest.mark.parametrize("agents_fixtures", ["agents.agents"], indirect=True)
def test_agents(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.agents` view.
    """
    view = agents_fixtures

    idmef = create_heartbeat('01123581-3213-4558-9144')
    env.idmef_db.insert(idmef)

    assert view.render()

    # clean
    delete_heartbeat('01123581-3213-4558-9144')


@pytest.mark.parametrize("agents_fixtures", ["agents.agents"], indirect=True)
def test_agents_online(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.agents` view.
    """
    view = agents_fixtures
    backup_parameters = deepcopy(env.request.parameters)

    idmef = create_heartbeat('01123581-3213-4558-9144', status='online')
    env.idmef_db.insert(idmef)

    env.request.parameters['status'] = ['online']

    assert view.render()

    # clean
    delete_heartbeat('01123581-3213-4558-9144')
    env.request.parameters = backup_parameters


@pytest.mark.parametrize("agents_fixtures", ["agents.agents"], indirect=True)
def test_agents_status_unknown(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.agents` view.
    """
    view = agents_fixtures
    backup_parameters = deepcopy(env.request.parameters)

    idmef = create_heartbeat('01123581-3213-4558-9144', status='online')
    env.idmef_db.insert(idmef)

    env.request.parameters['status'] = ['unknown']

    assert view.render()

    # clean
    delete_heartbeat('01123581-3213-4558-9144')
    env.request.parameters = backup_parameters


@pytest.mark.parametrize("agents_fixtures", ["agents.delete"], indirect=True)
def test_delete_heartbeat(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.delete` view.

    Type(s): Heartbeat (x1)
    """
    view = agents_fixtures
    backup_parameters = deepcopy(env.request.parameters)

    idmef_id = '01123581-3213-4558-9144'
    idmef = create_heartbeat(idmef_id)
    env.idmef_db.insert(idmef)

    env.request.parameters['types'] = ['heartbeat']
    env.request.parameters['id'] = [idmef_id.replace('-', '')]

    assert len(get_heartbeat(idmef_id)) == 1
    assert view.render()
    assert len(get_heartbeat(idmef_id)) == 0

    # clean
    env.request.parameters = backup_parameters


@pytest.mark.parametrize("agents_fixtures", ["agents.delete"], indirect=True)
def test_delete_heartbeat_multiple(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.delete` view.

    Type(s): Heartbeat (x2)
    """
    view = agents_fixtures
    backup_parameters = deepcopy(env.request.parameters)

    idmef_id = '01123581-3213-4558-9144'
    idmef_id_2 = '01123581-3213-4558-9145'
    idmef = create_heartbeat(idmef_id)
    idmef_2 = create_heartbeat(idmef_id_2)
    env.idmef_db.insert(idmef)
    env.idmef_db.insert(idmef_2)

    env.request.parameters['types'] = ['heartbeat']
    env.request.parameters['id'] = [idmef_id.replace('-', ''), idmef_id_2.replace('-', '')]

    assert len(get_heartbeat(idmef_id)) == 1
    assert len(get_heartbeat(idmef_id_2)) == 1
    assert view.render()
    assert len(get_heartbeat(idmef_id)) == 0
    assert len(get_heartbeat(idmef_id_2)) == 0

    # clean
    env.request.parameters = backup_parameters


@pytest.mark.parametrize("agents_fixtures", ["agents.delete"], indirect=True)
def test_delete_alert(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.delete` view.

    Type(s): Alert (x1)
    """
    view = agents_fixtures
    backup_parameters = deepcopy(env.request.parameters)

    idmef_id = '01123581-3213-4558-9144'
    idmef = create_alert(idmef_id)
    env.idmef_db.insert(idmef)

    env.request.parameters['types'] = ['alert']
    env.request.parameters['id'] = [idmef_id.replace('-', '')]

    assert len(get_alert(idmef_id)) == 1
    assert view.render()
    assert len(get_alert(idmef_id)) == 0

    # clean
    env.request.parameters = backup_parameters


@pytest.mark.parametrize("agents_fixtures", ["agents.delete"], indirect=True)
def test_delete_alert_multiple(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.delete` view.

    Type(s): Alert (x2)
    """
    view = agents_fixtures
    backup_parameters = deepcopy(env.request.parameters)

    idmef_id = '01123581-3213-4558-9144'
    idmef_id_2 = '01123581-3213-4558-9145'
    idmef = create_alert(idmef_id)
    idmef_2 = create_alert(idmef_id_2)
    env.idmef_db.insert(idmef)
    env.idmef_db.insert(idmef_2)

    env.request.parameters['types'] = ['alert']
    env.request.parameters['id'] = [idmef_id.replace('-', ''), idmef_id_2.replace('-', '')]

    assert len(get_alert(idmef_id)) == 1
    assert len(get_alert(idmef_id_2)) == 1
    assert view.render()
    assert len(get_alert(idmef_id)) == 0
    assert len(get_alert(idmef_id_2)) == 0

    # clean
    env.request.parameters = backup_parameters


@pytest.mark.parametrize("agents_fixtures", ["agents.delete"], indirect=True)
def test_delete_alert_and_heartbeat(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.delete` view.

    Type(s): Alert (x2, one deleted and one not deleted) + Heartbeat (x1)
    """
    view = agents_fixtures
    backup_parameters = deepcopy(env.request.parameters)

    idmef_id = '01123581-3213-4558-9144'
    idmef_id_2 = '01123581-3213-4558-9145'  # not deleted
    idmef_id_3 = '01123581-3213-4558-91456'
    idmef = create_alert(idmef_id)
    idmef_2 = create_alert(idmef_id_2)
    idmef_3 = create_heartbeat(idmef_id_3)
    env.idmef_db.insert(idmef)
    env.idmef_db.insert(idmef_2)
    env.idmef_db.insert(idmef_3)

    env.request.parameters['types'] = ['alert', 'heartbeat']
    env.request.parameters['id'] = [idmef_id.replace('-', ''), idmef_id_3.replace('-', '')]

    assert len(get_alert(idmef_id)) == 1
    assert len(get_alert(idmef_id_2)) == 1
    assert len(get_heartbeat(idmef_id_3)) == 1
    assert view.render()
    assert len(get_alert(idmef_id)) == 0
    assert len(get_alert(idmef_id_2)) == 1
    assert len(get_heartbeat(idmef_id_3)) == 0

    # clean
    env.request.parameters = backup_parameters


@pytest.mark.parametrize("agents_fixtures", ["agents.delete"], indirect=True)
def test_delete_unknown_type(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.delete` view.

    Type(s): unknown
    """
    view = agents_fixtures
    backup_parameters = deepcopy(env.request.parameters)

    env.request.parameters['types'] = ['unknown']
    env.request.parameters['id'] = [42]

    assert view.render()

    # clean
    env.request.parameters = backup_parameters


@pytest.mark.parametrize("agents_fixtures", ["agents.analyze"], indirect=True)
def test_analyze(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.analyze` view.
    """
    view = agents_fixtures

    idmef_id = '01123581-3213-4558-9144'
    idmef = create_heartbeat(idmef_id)
    env.idmef_db.insert(idmef)

    assert view.render(idmef_id.replace('-', ''))

    # clean
    delete_heartbeat(idmef_id)


@pytest.mark.parametrize("agents_fixtures", ["agents.analyze"], indirect=True)
def test_analyze_mult(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.analyze` view.

    Multiple heartbeats.
    """
    view = agents_fixtures

    analyzer_id = '123456'
    idmef_id = '01123581-3213-4558-9144'
    idmef_id_2 = '01123581-3213-4558-9145'
    idmef_id_3 = '01123581-3213-4558-9146'
    idmef = create_heartbeat(idmef_id, status='Online', analyzer_id=analyzer_id)
    idmef_2 = create_heartbeat(idmef_id_2, status='Online', analyzer_id=analyzer_id)
    idmef_3 = create_heartbeat(idmef_id_3, status='Online', analyzer_id=analyzer_id)
    env.idmef_db.insert(idmef)
    env.idmef_db.insert(idmef_2)
    env.idmef_db.insert(idmef_3)

    assert view.render(analyzer_id)

    # clean
    delete_heartbeat(idmef_id)
    delete_heartbeat(idmef_id_2)
    delete_heartbeat(idmef_id_3)


@pytest.mark.parametrize("agents_fixtures", ["agents.analyze"], indirect=True)
def test_analyze_mult_no_status(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.analyze` view.

    Multiple heartbeats without `additional_data('Analyzer status')`.
    """
    view = agents_fixtures

    analyzer_id = '123456'
    idmef_id = '01123581-3213-4558-9144'
    idmef_id_2 = '01123581-3213-4558-9145'
    idmef = create_heartbeat(idmef_id, analyzer_id=analyzer_id)
    idmef_2 = create_heartbeat(idmef_id_2, analyzer_id=analyzer_id)
    env.idmef_db.insert(idmef)
    env.idmef_db.insert(idmef_2)

    assert view.render(analyzer_id)

    # clean
    delete_heartbeat(idmef_id)
    delete_heartbeat(idmef_id_2)


@pytest.mark.parametrize("agents_fixtures", ["agents.analyze"], indirect=True)
def test_analyze_mult_no_interval(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.analyze` view.

    Multiple heartbeats without `heartbeat.heartbeat_interval`.
    """
    view = agents_fixtures

    analyzer_id = '123456'
    idmef_id = '01123581-3213-4558-9144'
    idmef_id_2 = '01123581-3213-4558-9145'
    idmef = create_heartbeat(idmef_id, heartbeat_interval=None, status='Online', analyzer_id=analyzer_id)
    idmef_2 = create_heartbeat(idmef_id_2, heartbeat_interval=None, status='Online', analyzer_id=analyzer_id)
    env.idmef_db.insert(idmef)
    env.idmef_db.insert(idmef_2)

    assert view.render(analyzer_id)

    # clean
    delete_heartbeat(idmef_id)
    delete_heartbeat(idmef_id_2)


@pytest.mark.parametrize("agents_fixtures", ["agents.analyze"], indirect=True)
def test_analyze_mult_missing(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.analyze` view.

    Multiple heartbeats with "missing" status.
    """
    view = agents_fixtures

    analyzer_id = '123456'
    idmef_id = '01123581-3213-4558-9144'
    idmef_id_2 = '01123581-3213-4558-9145'
    idmef = create_heartbeat(idmef_id, heartbeat_date='2013-01-01 10:09:08', status='Online',
                             analyzer_id=analyzer_id)
    idmef_2 = create_heartbeat(idmef_id_2, heartbeat_date='2013-12-11 10:19:08', status='Online',
                               analyzer_id=analyzer_id)
    env.idmef_db.insert(idmef)
    env.idmef_db.insert(idmef_2)

    assert view.render(analyzer_id)

    # clean
    delete_heartbeat(idmef_id)
    delete_heartbeat(idmef_id_2)


@pytest.mark.parametrize("agents_fixtures", ["agents.analyze"], indirect=True)
def test_analyze_mult_starting(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.analyze` view.

    Multiple heartbeats with "starting" status.
    """
    view = agents_fixtures

    analyzer_id = '123456'
    idmef_id = '01123581-3213-4558-9144'
    idmef_id_2 = '01123581-3213-4558-9145'
    idmef = create_heartbeat(idmef_id, status='starting', analyzer_id=analyzer_id)
    idmef_2 = create_heartbeat(idmef_id_2, status='starting', analyzer_id=analyzer_id)
    env.idmef_db.insert(idmef)
    env.idmef_db.insert(idmef_2)

    assert view.render(analyzer_id)

    # clean
    delete_heartbeat(idmef_id)
    delete_heartbeat(idmef_id_2)


@pytest.mark.parametrize("agents_fixtures", ["agents.analyze"], indirect=True)
def test_analyze_mult_after_ext(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.analyze` view.

    Multiple heartbeats with "starting" status after "exiting" status.
    """
    view = agents_fixtures

    analyzer_id = '123456'
    idmef_id = '01123581-3213-4558-9144'
    idmef_id_2 = '01123581-3213-4558-9145'
    idmef = create_heartbeat(idmef_id, status='exiting', analyzer_id=analyzer_id)
    idmef_2 = create_heartbeat(idmef_id_2, status='starting', analyzer_id=analyzer_id)
    env.idmef_db.insert(idmef)
    env.idmef_db.insert(idmef_2)

    assert view.render(analyzer_id)

    # clean
    delete_heartbeat(idmef_id)
    delete_heartbeat(idmef_id_2)


@pytest.mark.parametrize("agents_fixtures", ["agents.analyze"], indirect=True)
def test_analyze_mult_running(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.analyze` view.

    Multiple heartbeats with "running" status.
    """
    view = agents_fixtures

    analyzer_id = '123456'
    idmef_id = '01123581-3213-4558-9144'
    idmef_id_2 = '01123581-3213-4558-9145'
    idmef = create_heartbeat(idmef_id, status='running', analyzer_id=analyzer_id)
    idmef_2 = create_heartbeat(idmef_id_2, status='running', analyzer_id=analyzer_id)
    env.idmef_db.insert(idmef)
    env.idmef_db.insert(idmef_2)

    assert view.render(analyzer_id)

    # clean
    delete_heartbeat(idmef_id)
    delete_heartbeat(idmef_id_2)


@pytest.mark.parametrize("agents_fixtures", ["agents.analyze"], indirect=True)
def test_analyze_mult_run_unexint(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.analyze` view.

    Multiple heartbeats with "running" status but unexpected interval between 2 heartbeats.
    """
    view = agents_fixtures

    analyzer_id = '123456'
    idmef_id = '01123581-3213-4558-9144'
    idmef_id_2 = '01123581-3213-4558-9145'
    current_date = datetime.now()
    previous_date = current_date - timedelta(seconds=600)
    idmef = create_heartbeat(idmef_id,
                             status='running',
                             heartbeat_date=current_date.strftime('%Y-%m-%d %H:%M:%S'),
                             analyzer_id=analyzer_id,
                             heartbeat_interval=599)
    idmef_2 = create_heartbeat(idmef_id_2,
                               status='running',
                               heartbeat_date=previous_date.strftime('%Y-%m-%d %H:%M:%S'),
                               analyzer_id=analyzer_id,
                               heartbeat_interval=599)
    env.idmef_db.insert(idmef)
    env.idmef_db.insert(idmef_2)

    assert view.render(analyzer_id)

    # clean
    delete_heartbeat(idmef_id)
    delete_heartbeat(idmef_id_2)


@pytest.mark.parametrize("agents_fixtures", ["agents.analyze"], indirect=True)
def test_analyze_mult_exiting(agents_fixtures):
    """
    Test `prewikka.views.agents.agents.Agents.analyze` view.

    Multiple heartbeats with "exiting" status.
    """
    view = agents_fixtures

    analyzer_id = '123456'
    idmef_id = '01123581-3213-4558-9144'
    idmef_id_2 = '01123581-3213-4558-9145'
    idmef = create_heartbeat(idmef_id, status='exiting', analyzer_id=analyzer_id)
    idmef_2 = create_heartbeat(idmef_id_2, status='exiting', analyzer_id=analyzer_id)
    env.idmef_db.insert(idmef)
    env.idmef_db.insert(idmef_2)

    assert view.render(analyzer_id)

    # clean
    delete_heartbeat(idmef_id)
    delete_heartbeat(idmef_id_2)
