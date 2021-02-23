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

""" ChartJS bar plugin """

from .. import ChartJSRenderer
from prewikka.renderer import RendererUtils, RendererNoDataException
from prewikka import version


class ChartJSBarPlugin(ChartJSRenderer):
    """ ChartJS bar plugin """

    renderer_type = "bar"

    plugin_name = "ChartJS : Bar"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("ChartJS Bar renderer type")

    def render(self, data, query=None, **kwargs):
        """ Return the HTML for this chart

        Keyword arguments:
        data -- List of tuple containing the data for this chart
                [(count, value, link), ]
        """

        rutils = RendererUtils(kwargs)
        labels = []
        bar_data = []
        mapping = {}

        for count, value, link in data[0]:
            label = rutils.get_label(value)
            bar_data.append(count)
            labels.append(label)
            mapping[label] = link

        color = rutils.get_color(0)

        if not bar_data:
            raise RendererNoDataException

        options = {
            "labels": labels,
            "datasets": [{
                "backgroundColor": self._rgba(color, 0.5),
                "borderColor": self._rgba(color, 0.8),
                "hoverBackgroundColor": self._rgba(color, 0.75),
                "hoverBorderColor": self._rgba(color, 1),
                "data": bar_data
            }]
        }

        return self.generate_html(kwargs, options, {"legend": {"display": False}}, "bar", mapping)
