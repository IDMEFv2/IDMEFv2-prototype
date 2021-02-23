# -*- coding: utf-8 -*-
# Copyright (C) 2018-2020 CS GROUP - France. All Rights Reserved.
# Author: Sélim Menouar <selim.menouar@c-s.fr>
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

""" ChartJS line plugin (multiple line) """

from .. import ChartJSRenderer
from prewikka.renderer import RendererUtils, RendererNoDataException
from prewikka import version


class ChartJSTimePlugin(ChartJSRenderer):
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__

    def render(self, data, query=None, xlegend=[], **kwargs):
        """ Return the HTML for this chart

        Keyword arguments:
        data -- List containing the data for this chart
        xlegend -- List containing the xAxis legend
        """

        link_mapping = {}
        options = {"labels": xlegend, "datasets": []}
        opts = {}
        if kwargs.get("stacked"):
            opts["scales"] = {
                "xAxes": [{"stacked": True}],
                "yAxes": [{"stacked": True}]
            }

        rutils = RendererUtils(kwargs)

        for index, item in enumerate(data):
            label = rutils.get_label(item.series)
            color = rutils.get_color(item.series)
            options["datasets"].append({
                "label": label,
                "fill": ("-1" if index else "origin") if kwargs.get("stacked") else False,
                "backgroundColor": self._rgba(color, 1 if self._chart_type == "bar" else 0.2),
                "borderColor": self._rgba(color, 1),
                "pointBackgroundColor": self._rgba(color, 1),
                "pointBorderColor": "#fff",
                "pointHoverBackgroundColor": "#fff",
                "pointHoverBorderColor": self._rgba(color, 1),
                "data": item.values
            })

            link_mapping[label] = {}
            for i, link in enumerate(item.links):
                link_mapping[label][xlegend[i]] = link

        if not options["datasets"]:
            raise RendererNoDataException

        return self.generate_html(kwargs, options, opts, self._chart_type, link_mapping, True)


class ChartJSTimelinePlugin(ChartJSTimePlugin):
    """ ChartJS timeline plugin """

    renderer_type = "timeline"
    _chart_type = "line"

    plugin_name = "ChartJS : Timeline"
    plugin_description = N_("ChartJS Timeline renderer type")

    def render(self, data, **kwargs):
        return ChartJSTimePlugin.render(self, data, **kwargs)


class ChartJSTimebarPlugin(ChartJSTimePlugin):
    """ ChartJS timebar plugin """

    renderer_type = "timebar"
    _chart_type = "bar"

    plugin_name = "ChartJS : Timebar"
    plugin_description = N_("ChartJS Timebar renderer type")

    def render(self, data, **kwargs):
        return ChartJSTimePlugin.render(self, data, stacked=True, **kwargs)
