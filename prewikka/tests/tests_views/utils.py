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
Utils for `prewikka.views` tests.
"""

import prelude

from prewikka.dataprovider import Criterion


def create_heartbeat(heartbeat_id, heartbeat_date=None, heartbeat_interval=600, status='', analyzer_id=None):
    """
    Create an IDMEF Heartbeat for test suite.

    :param str heartbeat_id: Heartbeat ID.
    :param str heartbeat_date: Optional Heartbeat date.
    :param str heartbeat_interval: default interval.
    :param str status: Add "Analyzer status" in additional data.
    :param str analyzer_id: Analyzer ID, based on heartbeat_id if not specified.
    :return: An IDMEF object with Heartbeat information.
    :rtype: prelude.IDMEF
    """
    if not analyzer_id:
        analyzer_id = heartbeat_id.replace('-', '')

    idmef = prelude.IDMEF()
    if heartbeat_date:
        idmef.set('heartbeat.create_time', heartbeat_date)

    idmef.set('heartbeat.messageid', heartbeat_id)
    idmef.set('heartbeat.heartbeat_interval', heartbeat_interval)
    idmef.set('heartbeat.analyzer(0).analyzerid', analyzer_id)
    idmef.set('heartbeat.analyzer(0).name', 'prelude-testing')
    idmef.set('heartbeat.analyzer(0).manufacturer', 'https://www.prelude-siem.com')
    idmef.set('heartbeat.analyzer(0).node.name', 'testing.prelude')
    idmef.set('heartbeat.additional_data(0).meaning', 'Analyzer status')
    idmef.set('heartbeat.additional_data(0).data', status)

    return idmef


def delete_heartbeat(heartbeat_id):
    """
    Delete a Heartbeat in database after tests.

    :param str heartbeat_id: Heartbeat ID.
    :type heartbeat_id: str
    :return: None.
    """
    env.dataprovider.delete(Criterion('heartbeat.messageid', '=', heartbeat_id))


def get_heartbeat(heartbeat_id):
    """
    Delete a Heartbeat in database after tests.

    :param str heartbeat_id: Heartbeat ID.
    """
    return env.dataprovider.get(Criterion('heartbeat.messageid', '=', heartbeat_id))


def create_alert(alert_id):
    """
    Create an IDMEF Alert for test suite.

    :param str alert_id: Alert ID.
    :return: An IDMEF object with alert information.
    :rtype: prelude.IDMEF
    """
    idmef = prelude.IDMEF()
    idmef.set('alert.messageid', alert_id)
    idmef.set('alert.analyzer(0).analyzerid', alert_id.replace('-', ''))
    idmef.set('alert.analyzer(0).name', 'prelude-testing')
    idmef.set('alert.analyzer(0).manufacturer', 'https://www.prelude-siem.com')
    idmef.set('alert.analyzer(0).node.name', 'testing.prelude')

    return idmef


def get_alert(alert_id):
    """
    Get an alert for test suite.

    :param str alert_id: Alert ID.
    :return: alert if exists.
    :rtype: prewikka.utils.misc.CachingIterator
    """
    return env.dataprovider.get(Criterion('alert.messageid', '=', alert_id))


def create_correlation_alert(alert_id, correlation_name, correlated_alertid='correlated_alert_ident'):
    """
    Create a correlation alert for test suite.

    :param str alert_id: Alert ID.
    :param str correlation_name: alert.correlation_alert.name IDMEF value.
    :return: An IDMEF object with correlation alert information.
    :rtype: prelude.IDMEF
    """
    idmef = create_alert(alert_id)
    idmef.set('alert.correlation_alert.name', correlation_name)
    idmef.set('alert.correlation_alert.alertident(0).alertident', correlated_alertid)

    return idmef
