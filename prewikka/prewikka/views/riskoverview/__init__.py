# Copyright (C) 2014-2021 CS GROUP - France. All Rights Reserved.
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

import collections
import pkg_resources

from prewikka import hookmanager, resource, template, version, view


class RiskOverview(view.View):
    plugin_name = "Risk Overview"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Top page risk overview")
    plugin_htdocs = (("riskoverview", pkg_resources.resource_filename(__name__, 'htdocs')),)

    """ Retrieving info for risk overview table """
    def __init__(self):
        self._widgets = env.config.riskoverview.keys()
        view.View.__init__(self)

    @hookmanager.register("HOOK_TOPLAYOUT_EXTRA_CONTENT")
    def _toplayout_extra_content(self):
        # Don't show the risk overview if the user is not logged in
        if not env.request.user:
            return

        return resource.HTMLSource(template.PrewikkaTemplate(__name__, "templates/riskoverview.mak").render())

    @view.route("/riskoverview")
    def riskoverview(self):
        # Don't show the risk overview if the user is not logged in
        if not env.request.user:
            return

        # We don't use groupby because the result won't be sorted then.
        objs = collections.OrderedDict((w, None) for w in self._widgets)

        for i in filter(None, hookmanager.trigger("HOOK_RISKOVERVIEW_DATA", _except=env.log.debug)):
            if i.name not in objs and self._widgets:
                continue
            elif objs.get(i.name) is None:
                objs[i.name] = i
            else:
                for j in i.data:
                    objs[i.name].data.append(j)

        return view.ViewResponse(template.PrewikkaTemplate(__name__, "templates/table.mak").render(data=filter(None, objs.values())))
