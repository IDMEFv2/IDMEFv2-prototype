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
Tests `prewikka.views.datasearch.alert`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy

import pytest

from tests.utils.fixtures import load_view_for_fixtures
from tests.tests_views.utils import create_correlation_alert


@pytest.fixture(scope='function')
def datasearch_fixtures(request):
    """
    Fixture for datasearch tests.

    :return: view for alerts.
    :rtype: prewikka.view.View
    """
    backup_parameters = deepcopy(env.request.parameters)

    view = load_view_for_fixtures(request.param)
    view.process_parameters()

    alert_id = '79e0ce14-46b6-11e7-9ab4'
    correlation_alert = create_correlation_alert(alert_id, 'correlation_alert_1')
    env.dataprovider._backends["alert"]._db.insert(correlation_alert)

    def tear_down():
        """
        TearDown
        """
        env.request.parameters = backup_parameters
        env.dataprovider._backends["alert"]._db.remove('alert.messageid')

    request.addfinalizer(tear_down)

    return view


@pytest.mark.parametrize("datasearch_fixtures", ["AlertDataSearch.forensic"], indirect=True)
def test_alerts(datasearch_fixtures):
    """
    Test `prewikka.views.datasearch.alert.AlertDataSearch` view.
    """
    view = datasearch_fixtures
    view.render()


@pytest.mark.parametrize("datasearch_fixtures", ["AlertDataSearch.ajax_timeline"], indirect=True)
def test_alerts_timeline(datasearch_fixtures):
    """
    Test `prewikka.views.datasearch.alert.AlertDataSearch` timeline.
    """
    view = datasearch_fixtures
    view.render()


@pytest.mark.parametrize("datasearch_fixtures", ["AlertDataSearch.ajax_table"], indirect=True)
def test_alerts_table(datasearch_fixtures):
    """
    Test `prewikka.views.datasearch.alert.AlertDataSearch` table.
    """
    view = datasearch_fixtures
    view.render()


@pytest.mark.parametrize("datasearch_fixtures", ["AlertDataSearch.ajax_details"], indirect=True)
def test_alerts_details(datasearch_fixtures):
    """
    Test `prewikka.views.datasearch.alert.AlertDataSearch` details.
    """
    view = datasearch_fixtures

    env.request.parameters["_criteria"] = '{"__prewikka_class__": ["Criterion", {"left": "alert.correlation_alert.name", "operator": "==", "right": "correlation_alert_1"}]}'
    view.render()

    with pytest.raises(IndexError):
        env.request.parameters["_criteria"] = '{"__prewikka_class__": ["Criterion", {"left": "alert.correlation_alert.name", "operator": "==", "right": "foobar"}]}'
        view.render()


@pytest.mark.parametrize("datasearch_fixtures", ["AlertDataSearch.ajax_infos"], indirect=True)
def test_alerts_infos(datasearch_fixtures):
    """
    Test `prewikka.views.datasearch.alert.AlertDataSearch` details.
    """
    view = datasearch_fixtures

    env.request.parameters["_criteria"] = '{"__prewikka_class__": ["Criterion", {"left": "alert.correlation_alert.name", "operator": "==", "right": "correlation_alert_1"}]}'
    env.request.parameters["query"] = 'analyzer(0).name <> "prelude-testing"'
    env.request.parameters["field"] = 'analyzer(0).name'
    env.request.parameters["value"] = 'prelude-testing'

    view.render()
