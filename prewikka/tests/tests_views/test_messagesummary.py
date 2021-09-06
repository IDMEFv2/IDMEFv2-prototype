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
Tests `prewikka.views.messagesummary.messagesummary`.
"""

import pytest

from tests.utils.fixtures import load_view_for_fixtures
from tests.tests_views.utils import create_alert, create_correlation_alert, create_heartbeat


_heartbeat_id = 'edd972ea-aaaf-11e8-a6e7'
_alert_id = '79e0ce14-46b6-11e7-9ab4'
_correlation_alert_id = 'c9b37c54-bf56-11e5-9602'


@pytest.fixture(scope='module')
def messagesummary_fixtures(request):
    """
    Fixture for messagesummary tests.

    :return: view for messagesummary.
    :rtype: prewikka.view.View
    """
    view = load_view_for_fixtures(request.param)
    view.process_parameters()

    heartbeat = create_heartbeat(_heartbeat_id)
    env.dataprovider._backends["heartbeat"]._db.insert(heartbeat)

    alert = create_alert(_alert_id)
    env.dataprovider._backends["alert"]._db.insert(alert)

    correlation_alert = create_correlation_alert(_correlation_alert_id, 'correlation_alert_1', _alert_id)
    env.dataprovider._backends["alert"]._db.insert(correlation_alert)

    def tear_down():
        """
        TearDown
        """
        env.dataprovider._backends["alert"]._db.remove('alert.messageid')

    request.addfinalizer(tear_down)

    return view


@pytest.mark.parametrize("messagesummary_fixtures", ["HeartbeatSummary.render"], indirect=True)
def test_heartbeat_summary(messagesummary_fixtures):
    """
    Test `prewikka.views.messagesummary.HeartbeatSummary` view.
    """
    view = messagesummary_fixtures
    view.render(messageid=_heartbeat_id)


@pytest.mark.parametrize("messagesummary_fixtures", ["AlertSummary.render"], indirect=True)
def test_alert_summary(messagesummary_fixtures):
    """
    Test `prewikka.views.messagesummary.AlertSummary` view.
    """
    view = messagesummary_fixtures
    view.render(messageid=_alert_id)


@pytest.mark.parametrize("messagesummary_fixtures", ["AlertSummary.render"], indirect=True)
def test_correlation_alert_summary(messagesummary_fixtures):
    """
    Test `prewikka.views.messagesummary.AlertSummary` view with a correlation alert.
    """
    view = messagesummary_fixtures
    view.render(messageid=_correlation_alert_id)
