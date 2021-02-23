# -*- coding: utf-8 -*-
# Copyright (C) 2020 CS GROUP - France. All Rights Reserved.
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

""" ChartJS pie plugin """

from .. import ChartJSRenderer
from prewikka.renderer import RendererUtils, RendererNoDataException
from prewikka import version


class ChartJSCircularPlugin(ChartJSRenderer):
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__

    def render(self, data, query=None, **kwargs):
        """ Return the HTML for this chart

        Keyword arguments:
        data -- List of tuple containing the data for this chart
                [(count, value, link), ]
        """

        rutils = RendererUtils(kwargs)
        labels = []
        colors = []
        pie_data = []
        mapping = {}

        for i, d in enumerate(data):
            for count, value, link in d:
                label = rutils.get_label(value)
                pie_data.append(count)
                labels.append(label)
                mapping[label] = link
                colors.append(self._rgba(rutils.get_color(value), 1))

        if not pie_data:
            raise RendererNoDataException

        options = {
            "labels": labels,
            "datasets": [{
                "backgroundColor": colors,
                "data": pie_data
            }]
        }

        return self.generate_html(kwargs, options, {"layout": {"padding": {"bottom": 20}}}, self.renderer_type, mapping)


class ChartJSPiePlugin(ChartJSCircularPlugin):
    """ ChartJS pie plugin """

    renderer_type = "pie"

    plugin_name = "ChartJS : Pie"
    plugin_description = N_("ChartJS Pie renderer type")


class ChartJSDoughnutPlugin(ChartJSCircularPlugin):
    """ ChartJS doughnut plugin """

    renderer_type = "doughnut"

    plugin_name = "ChartJS : Doughnut"
    plugin_description = N_("ChartJS Doughnut renderer type")
