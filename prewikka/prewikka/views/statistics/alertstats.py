# Copyright (C) 2019-2020 CS GROUP - France. All Rights Reserved.
# Author: Antoine Luong <antoine.luong@c-s.fr>
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

from __future__ import absolute_import, division, print_function, unicode_literals

import functools
import operator

from prewikka import hookmanager, statistics, usergroup, utils, version, view
from prewikka.dataprovider import Criterion
from prewikka.renderer import RendererItem

from .utils import compute_charts_infos
from .statistics import chart_class, StaticStats


_DEFAULT_GRAPHS = [
    {
        'title': N_("Severities"),
        'category': "diagram",
        'type': "pie",
        'path': "alert.assessment.impact.severity",
        'description': N_("This graph shows the severities of the reported alerts. "
                          "There are 5 existing severities: n/a, info, low, medium, and high.")
    },
    {
        'title': N_("Top {limit} Analyzer Node Locations"),
        'category': "diagram",
        'type': "pie",
        'path': "alert.analyzer(-1).node.location",
        'description': N_("This graph shows the most recurrent locations of the analyzers reporting an alert.")
    },
    {
        'title': N_("Timeline"),
        'category': "chronology",
        'type': "timeline",
        'path': "alert.assessment.impact.severity",
        'description': N_("This graph shows the evolution of the alerts severities over time.")
    },
    {
        'title': N_("Top {limit} Source Addresses"),
        'category': "diagram",
        'type': "horizontal-bar",
        'path': "alert.source.node.address.address",
        'description': N_("This graph shows the most common alert source IP addresses.")
    },
    {
        'title': N_("Top {limit} Targeted Addresses"),
        'category': "diagram",
        'type': "horizontal-bar",
        'path': "alert.target.node.address.address",
        'description': N_("This graph shows the most common alert target IP addresses.")
    },
    {
        'title': N_("Top {limit} Classifications"),
        'category': "diagram",
        'type': "pie",
        'path': "alert.classification.text",
        'description': N_("This graph shows the most recurrent classifications of the reported alerts. "
                          "The classification is a short description of the alert.")
    },
    {
        'title': N_("Top {limit} Classifications Trend"),
        'category': "chronology",
        'type': "timeline",
        'path': "alert.classification.text",
        'description': N_("This graph shows the evolution of the alerts classifications over time.")
    },
    {
        'title': N_("Top {limit} Analyzer Classes"),
        'category': "diagram",
        'type': "pie",
        'path': "alert.analyzer(-1).class",
        'description': N_("This graph shows the most recurrent types of the first analyzer reporting an alert. "
                          "For further details on existing types, please visit "
                          "https://www.prelude-siem.org/projects/prelude/wiki/DevelAgentClassification")
    },
    {
        'title': N_("Top {limit} Analyzer Classes Trend"),
        'category': "chronology",
        'type': "timeline",
        'path': "alert.analyzer(-1).class",
        'description': N_("This graph shows the evolution of the type of the analyzers, reporting an alert, over time.")
    }
]


@chart_class
class ProtocolChart(statistics.DiagramChart):
    def get_data(self):
        return [list(self._get_data())]

    def _get_data(self):
        criteria = env.request.menu.get_criteria() + (
            Criterion("alert.target.service.iana_protocol_number", "==", 6) |
            Criterion("alert.target.service.iana_protocol_number", "==", 17) |
            Criterion("alert.target.service.iana_protocol_name", "=*", "tcp") |
            Criterion("alert.target.service.iana_protocol_name", "=*", "udp") |
            Criterion("alert.target.service.protocol", "=*", "udp") |
            Criterion("alert.target.service.protocol", "=*", "tcp"))

        try:
            results = env.dataprovider.query(
                [
                    "alert.target.service.port/group_by",
                    "alert.target.service.iana_protocol_number/group_by",
                    "alert.target.service.iana_protocol_name/group_by",
                    "alert.target.service.protocol/group_by",
                    "alert.target.service.name/group_by",
                    "count(1)/order_desc"
                ],
                criteria=criteria,
                limit=self.query[0].limit
            )
        except usergroup.PermissionDeniedError:
            results = []

        if not results:
            return

        merge = {
            _("n/a"): {},
            "tcp": {},
            "udp": {}
        }

        for port, iana_protocol_number, iana_protocol_name, protocol, service_name, count in results:
            if not port:
                continue

            if iana_protocol_number:
                protocol = utils.protocol_number_to_name(iana_protocol_number)

            elif iana_protocol_name:
                protocol = iana_protocol_name

            if protocol:
                protocol = protocol.lower()

            if protocol not in merge:
                protocol = _("n/a")

            if not service_name:
                service_name = _("Unknown service")

            port_info = (port, service_name)

            if port_info not in merge[protocol]:
                merge[protocol][port_info] = 0

            merge[protocol][port_info] += count

        results = []
        for protocol, values in merge.items():
            for port_info, count in values.items():
                results.append((port_info[0], port_info[1], protocol, count))

        for port, service, protocol, count in sorted(results, key=operator.itemgetter(3), reverse=True):
            criteria = Criterion("alert.target.service.port", "=", port)
            link = None
            linkview = env.viewmanager.get(datatype="alert", keywords=["listing"])
            if linkview:
                link = linkview[-1].make_url(criteria=criteria, **env.request.menu.get_parameters())

            yield RendererItem(count, ("%d (%s) / %s" % (port, service, protocol),), link)


class AlertStats(StaticStats):
    plugin_name = "Statistics: Alerts"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Statistics page about alerts")
    plugin_require = ["prewikka.views.statistics:Statistics"]

    _DEFAULT_ATTRIBUTES = {
        "global": {"height": 5, "width": 6},
        "chronology": {"type": "timeline"},
        "diagram": {"type": "pie"}
    }

    _MONITORING_CRITERIA = {
        'Analyzer': functools.reduce(
            lambda x, y: x | y,
            (Criterion("alert.analyzer(-1).class", "~", cls) for cls in ("HIDS", "Host IDS", "NIDS", "Network IDS"))
        ),
        'Correlation': Criterion("alert.correlation_alert.name", "!=", None),
        'Simple': Criterion("alert.correlation_alert.name", "=", None)
    }

    _CATEGORIZATION_GRAPHS = [
        {
            "title": N_("Top {limit} Classifications Trend"),
            "category": "chronology",
            "path": "alert.classification.text",
            "width": 12,
        },
        {
            "title": N_("Top {limit} Classifications"),
            "category": "diagram",
            "path": "alert.classification.text",
        },
        {
            "title": N_("Top {limit} Alert References"),
            "category": "diagram",
            "path": "alert.classification.reference.name",
        },
        {
            "title": N_("Alert: Severity"),
            "category": "diagram",
            "path": "alert.assessment.impact.severity",
        },
        {
            "title": N_("Top {limit} Alert Impact Types"),
            "category": "diagram",
            "path": "alert.assessment.impact.type",
        }]

    _SOURCE_GRAPHS = [
        {
            "title": N_("Top {limit} Sources Trend"),
            "category": "chronology",
            "path": "alert.source.node.address.address",
            "width": 12,
        },
        {
            "title": N_("Top {limit} Source Addresses"),
            "category": "diagram",
            "path": "alert.source.node.address.address",
        },
        {
            "title": N_("Top {limit} Source Users"),
            "category": "diagram",
            "path": "alert.source.user.user_id.name",
        }]

    _TARGET_GRAPHS = [
        {
            "title": N_("Top {limit} Targeted Addresses"),
            "category": "diagram",
            "path": "alert.target.node.address.address",
        },
        {
            "title": N_("Top {limit} Targeted Ports"),
            "category": "diagram",
            "class": "ProtocolChart",
        },
        {
            "title": N_("Top {limit} Targeted Users"),
            "category": "diagram",
            "path": "alert.target.user.user_id.name",
        },
        {
            "title": N_("Top {limit} Targeted Processes"),
            "category": "diagram",
            "path": "alert.target.process.name",
        }]

    _ANALYZER_GRAPHS = [
        {
            "title": N_("Top {limit} Analyzer Classes Trend"),
            "category": "chronology",
            "path": "alert.analyzer(-1).class",
        },
        {
            "title": N_("Top {limit} Analyzers"),
            "category": "diagram",
            "path": [
                "alert.analyzer(-1).name",
                "alert.analyzer(-1).node.name"
            ],
        },
        {
            "title": N_("Top {limit} Analyzer Models"),
            "category": "diagram",
            "path": "alert.analyzer(-1).model",
        },
        {
            "title": N_("Top {limit} Analyzer Classes"),
            "category": "diagram",
            "path": "alert.analyzer(-1).class",
        },
        {
            "title": N_("Top {limit} Analyzer Node Addresses"),
            "category": "diagram",
            "path": "alert.analyzer(-1).node.address.address",
        },
        {
            "title": N_("Top {limit} Analyzer Node Locations"),
            "category": "diagram",
            "path": "alert.analyzer(-1).node.location",
        }]

    _METROLOGY_GRAPHS = [
        {
            'category': 'chronology',
            'title': N_('Number of source addresses'),
            'aggregate': 'count(distinct(alert.source.node.address.address))',
            'criteria': _MONITORING_CRITERIA['Simple'],
            'legend': False,
        },
        {
            'category': 'chronology',
            'title': N_('Number of target addresses'),
            'aggregate': 'count(distinct(alert.target.node.address.address))',
            'criteria': _MONITORING_CRITERIA['Simple'],
            'legend': False,
        },
        {
            'category': 'chronology',
            'title': N_('Number of simple alerts'),
            'aggregate': 'count(alert.classification.text)',
            'criteria': _MONITORING_CRITERIA['Simple'],
            'legend': False,
        },
        {
            'category': 'chronology',
            'title': N_('Number of alerts per analyzer type'),
            'path': ['alert.analyzer(-1).class'],
            'criteria': _MONITORING_CRITERIA['Simple'],
        },
        {
            'category': 'chronology',
            'title': N_('Number of alerts'),
            'aggregate': 'count(alert.messageid)',
            'legend': False,
        },
        {
            'category': 'chronology',
            'title': N_('Number of correlation alerts'),
            'aggregate': 'count(alert.classification.text)',
            'criteria': _MONITORING_CRITERIA['Correlation'],
            'legend': False,
        },
        {
            'category': 'chronology',
            'title': N_('Number of machines/devices'),
            'aggregate': 'count(alert.target.node.address.address)',
            'criteria': _MONITORING_CRITERIA['Simple'],
            'legend': False,
        },
        {
            'category': 'chronology',
            'title': N_('Number of machines/devices per analyzer type (HIDS, NIDS)'),
            'path': 'alert.analyzer(-1).class',
            'criteria': _MONITORING_CRITERIA['Analyzer'],
            'aggregate': 'count(alert.target.node.address.address)',
            'legend': True,
        }]

    _CHARTS_INFOS = [(N_('Categorizations'), None, _CATEGORIZATION_GRAPHS),
                     (N_('Sources'), None, _SOURCE_GRAPHS),
                     (N_('Targets'), None, _TARGET_GRAPHS),
                     (N_('Analyzers'), None, _ANALYZER_GRAPHS),
                     (N_('Metrology'), None, _METROLOGY_GRAPHS)]

    _PREDEFINED_GRAPHS = compute_charts_infos(_CHARTS_INFOS)

    def __init__(self):
        env.dataprovider.check_datatype("alert")
        StaticStats.__init__(self)

        hookmanager.register("HOOK_DASHBOARD_DEFAULT_GRAPHS", _DEFAULT_GRAPHS)

    @view.route("/statistics/alerts", methods=["GET", "POST"], menu=(N_("Statistics"), N_("Alerts")), datatype="alert", help="#alertstats")
    def render(self):
        # Call again to resolve translation
        self.chart_infos = compute_charts_infos(self._CHARTS_INFOS)
        return self.draw()
