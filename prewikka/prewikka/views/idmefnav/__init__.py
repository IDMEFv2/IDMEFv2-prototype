# coding: utf-8
# Copyright (C) 2016-2021 CS GROUP - France. All Rights Reserved.
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

import pkg_resources

from prewikka import template, version, view
from . import graph_generator


class IDMEFNav(view.View):
    _HTDOCS_DIR = pkg_resources.resource_filename(__name__, 'htdocs')

    plugin_name = "IDMEFNav"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("IDMEF navigator")
    plugin_htdocs = (("idmefnav", _HTDOCS_DIR),)

    def __init__(self):
        view.View.__init__(self)
        self.schema = graph_generator.Schema(self._HTDOCS_DIR)
        self.schema.image_load()

    @view.route("/help/idmefnav", methods=['GET'], menu=(N_("Help"), N_("IDMEF")))
    def render(self):
        idmef_class = env.request.parameters.get("idmef_class", "IDMEF-Message")
        if idmef_class not in self.schema:
            raise view.InvalidParameterValueError("idmef_class", idmef_class)

        dset = template.PrewikkaTemplate(__name__, "templates/idmefnav.mak").dataset()
        dset["schema"] = self.schema[idmef_class]
        dset["schema"]['svg'] = dset["schema"]['svg'].replace(graph_generator._LINK_TAG, url_for('idmefnav.render'))
        dset["full_schema"] = self.schema

        return dset.render()
