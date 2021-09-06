# Copyright (C) 2019-2021 CS GROUP - France. All Rights Reserved.
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

import functools
import operator

from prewikka import hookmanager, statistics, usergroup, version, view
from prewikka.dataprovider import Criterion
from prewikka.renderer import RendererItem

from .utils import compute_charts_infos
from .statistics import chart_class, StaticStats


_DEFAULT_GRAPHS = [
    {
        'title': N_("Severities"),
        'category': "diagram",
        'type': "pie",
        'path': "idmefv2.severity",
        'description': N_("This graph shows the severities of the reported alerts. "
                          "There are 5 existing severities: n/a, info, low, medium, and high.")
    },
    {
        'title': N_("Top {limit} Analyzer locations"),
        'category': "diagram",
        'type': "pie",
        'path': "idmefv2.analyzer.location",
        'description': N_("This graph shows the most recurrent locations of the analyzers reporting an alert.")
    },
    {
        'title': N_("Timeline"),
        'category': "chronology",
        'type': "timeline",
        'path': "idmefv2.severity",
        'description': N_("This graph shows the evolution of the alerts severities over time.")
    },
    {
        'title': N_("Top {limit} Source Addresses"),
        'category': "diagram",
        'type': "horizontal-bar",
        'path': "idmefv2.source.ip",
        'description': N_("This graph shows the most common alert source IP addresses.")
    },
    {
        'title': N_("Top {limit} Targeted Addresses"),
        'category': "diagram",
        'type': "horizontal-bar",
        'path': "idmefv2.target.ip",
        'description': N_("This graph shows the most common alert target IP addresses.")
    },
    {
        'title': N_("Top {limit} Classifications"),
        'category': "diagram",
        'type': "pie",
        'path': "idmefv2.category",
        'description': N_("This graph shows the most recurrent classifications of the reported alerts. "
                          "The classification is a short description of the alert.")
    },
    {
        'title': N_("Top {limit} Classifications Trend"),
        'category': "chronology",
        'type': "timeline",
        'path': "idmefv2.category",
        'description': N_("This graph shows the evolution of the alerts classifications over time.")
    },
    {
        'title': N_("Top {limit} Analyzer Classes"),
        'category': "diagram",
        'type': "pie",
        'path': "idmefv2.analyzer.category",
        'description': N_("This graph shows the most recurrent analyzer classes")
    },
    {
        'title': N_("Top {limit} Analyzer Classes Trend"),
        'category': "chronology",
        'type': "timeline",
        'path': "idmefv2.analyzer.category",
        'description': N_("This graph shows the evolution of the analyzer classes, reporting an alert, over time.")
    }
]


@chart_class
class ProtocolChart(statistics.DiagramChart):
    def get_data(self):
        return [list(self._get_data())]

    def _get_data(self):
        criteria = env.request.menu.get_criteria() + (
            Criterion("idmefv2.source.protocol", "=*", "udp") |
            Criterion("idmefv2.source.protocol", "=*", "tcp"))

        try:
            results = env.dataprovider.query(
                [
                    "idmefv2.target.port/group_by",
                    "idmefv2.source.protocol/group_by",
                    "idmefv2.target.service/group_by",
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

        for port, protocol, service_name, count in results:
            if not port:
                continue

            if protocol:
                proto = set(["tcp", "udp"]) & set([p.lower() for p in protocol])
                if len(proto) == 1:
                    protocol = proto[0]
                else:
                    protocol = None

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
            criteria = Criterion("idmefv2.target.port", "=*", port)
            link = None
            linkview = env.viewmanager.get(datatype="idmefv2", keywords=["listing"])
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
            (Criterion("idmefv2.analyzer.category", "=*", cls) for cls in ("HIDS", "NIDS", "WIDS"))
        ),
        'Correlation': Criterion("idmefv2.status", "=", "Incident"),
        'Simple': Criterion("idmefv2.status", "!=", "Incident"),
    }

    _CATEGORIZATION_GRAPHS = [
        {
            "title": N_("Top {limit} Classifications Trend"),
            "category": "chronology",
            "path": "idmefv2.category",
            "width": 12,
        },
        {
            "title": N_("Top {limit} Classifications"),
            "category": "diagram",
            "path": "idmefv2.category",
        },
        {
            "title": N_("Top {limit} Alert References"),
            "category": "diagram",
            "path": "idmefv2.reference",
        },
        {
            "title": N_("Alert: Severity"),
            "category": "diagram",
            "path": "idmefv2.severity",
        },
        {
            "title": N_("Top {limit} Alert Impact Types"),
            "category": "diagram",
            "path": "idmefv2.analyzer.type",
        }]

    _SOURCE_GRAPHS = [
        {
            "title": N_("Top {limit} Sources Trend"),
            "category": "chronology",
            "path": "idmefv2.source.ip",
            "width": 12,
        },
        {
            "title": N_("Top {limit} Source Addresses"),
            "category": "diagram",
            "path": "idmefv2.source.ip",
        },
        {
            "title": N_("Top {limit} Source Users"),
            "category": "diagram",
            "path": "idmefv2.source.user",
        }]

    _TARGET_GRAPHS = [
        {
            "title": N_("Top {limit} Targeted Addresses"),
            "category": "diagram",
            "path": "idmefv2.target.ip",
        },
        {
            "title": N_("Top {limit} Targeted Ports"),
            "category": "diagram",
            "class": "ProtocolChart",
        },
        {
            "title": N_("Top {limit} Targeted Users"),
            "category": "diagram",
            "path": "idmefv2.target.user",
        },
        {
            "title": N_("Top {limit} Targeted Services"),
            "category": "diagram",
            "path": "idmefv2.target.service",
        }]

    _ANALYZER_GRAPHS = [
        {
            "title": N_("Top {limit} Analyzer Classes Trend"),
            "category": "chronology",
            "path": "idmefv2.analyzer.category",
        },
        {
            "title": N_("Top {limit} Analyzers"),
            "category": "diagram",
            "path": [
                "idmefv2.analyzer.name",
                "idmefv2.analyzer.hostname"
            ],
        },
        {
            "title": N_("Top {limit} Analyzer Models"),
            "category": "diagram",
            "path": "idmefv2.analyzer.model",
        },
        {
            "title": N_("Top {limit} Analyzer Classes"),
            "category": "diagram",
            "path": "idmefv2.analyzer.category",
        },
        {
            "title": N_("Top {limit} Analyzer Node Addresses"),
            "category": "diagram",
            "path": "idmefv2.analyzer.ip",
        },
        {
            "title": N_("Top {limit} Analyzer Node Locations"),
            "category": "diagram",
            "path": "idmefv2.analyzer.location",
        }]

    _METROLOGY_GRAPHS = [
        {
            'category': 'chronology',
            'title': N_('Number of source addresses'),
            'aggregate': 'count(distinct(idmefv2.source.ip))',
            'criteria': _MONITORING_CRITERIA['Simple'],
            'legend': False,
        },
        {
            'category': 'chronology',
            'title': N_('Number of target addresses'),
            'aggregate': 'count(distinct(idmefv2.target.ip))',
            'criteria': _MONITORING_CRITERIA['Simple'],
            'legend': False,
        },
        {
            'category': 'chronology',
            'title': N_('Number of simple alerts'),
            'aggregate': 'count(idmefv2.id)',
            'criteria': _MONITORING_CRITERIA['Simple'],
            'legend': False,
        },
        {
            'category': 'chronology',
            'title': N_('Number of alerts per analyzer type'),
            'path': ['idmefv2.analyzer.type'],
            'criteria': _MONITORING_CRITERIA['Simple'],
        },
        {
            'category': 'chronology',
            'title': N_('Number of alerts'),
            'aggregate': 'count(idmefv2.id)',
            'legend': False,
        },
        {
            'category': 'chronology',
            'title': N_('Number of correlation alerts'),
            'aggregate': 'count(idmefv2.id)',
            'criteria': _MONITORING_CRITERIA['Correlation'],
            'legend': False,
        },
        {
            'category': 'chronology',
            'title': N_('Number of machines/devices'),
            'aggregate': 'count(idmefv2.target.ip)',
            'criteria': _MONITORING_CRITERIA['Simple'],
            'legend': False,
        },
        {
            'category': 'chronology',
            'title': N_('Number of machines/devices per analyzer type (HIDS, NIDS)'),
            'path': 'idmefv2.analyzer.type',
            'criteria': _MONITORING_CRITERIA['Analyzer'],
            'aggregate': 'count(idmefv2.target.ip)',
            'legend': True,
        }]

    _CHARTS_INFOS = [(N_('Categorizations'), None, _CATEGORIZATION_GRAPHS),
                     (N_('Sources'), None, _SOURCE_GRAPHS),
                     (N_('Targets'), None, _TARGET_GRAPHS),
                     (N_('Analyzers'), None, _ANALYZER_GRAPHS),
                     (N_('Metrology'), None, _METROLOGY_GRAPHS)]

    _PREDEFINED_GRAPHS = compute_charts_infos(_CHARTS_INFOS)

    def __init__(self):
        env.dataprovider.check_datatype("idmefv2")
        StaticStats.__init__(self)

        hookmanager.register("HOOK_DASHBOARD_DEFAULT_GRAPHS", _DEFAULT_GRAPHS)

    @view.route("/statistics/alerts", methods=["GET", "POST"], menu=(N_("Statistics"), N_("Alerts")), datatype="idmefv2", help="#alertstats")
    def render(self):
        # Call again to resolve translation
        self.chart_infos = compute_charts_infos(self._CHARTS_INFOS)
        return self.draw()
