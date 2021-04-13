# Copyright (C) 2015-2021 CS GROUP - France. All Rights Reserved.
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

from prewikka import error, template, utils, version, view


def name_to_path(name):
    return name.lower().replace(" ", "_")


class Custom(view.View):
    plugin_name = "Embedding websites"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Embedding of external websites")

    def __init__(self):
        for appli in env.config.appli:
            permissions = self._make_list(appli.get("permission"))

            for name, url in self._get_tabs(appli):
                v = CustomView(appli.section, name, url)
                view.route(
                    name_to_path("/%s/%s" % (appli.section, name)),
                    method=v.render,
                    methods=None,
                    permissions=permissions,
                    menu=(appli.section, name),
                    help=appli.get("help")
                )

    @staticmethod
    def _make_list(value):
        if not value:
            return []

        return [x.strip() for x in value.split(",")]

    def _get_tabs(self, appli):
        base_url = appli.get("base_url", "").rstrip('/')
        tabs = self._make_list(appli.tab)
        tab_urls = self._make_list(appli.tab_url)

        if len(tab_urls) != len(tabs):
            raise error.PrewikkaUserError(N_("Could not load tabs"), N_("A URL should be defined for each tab"))

        for i, url in enumerate(tab_urls):
            if not url.startswith('http://') and not url.startswith('https://'):
                tab_urls[i] = "%s/%s" % (base_url, url)

        return zip(tabs, tab_urls)


class CustomView(view.View):
    def __init__(self, section, name, url):
        self.view_id = name_to_path("custom_%s_%s" % (section, name))
        self._view_url = url
        view.View.__init__(self)

    def render(self):
        extra_url = ""
        if env.request.parameters:
            if 'extra_url' in env.request.parameters:
                extra_url = "/" + env.request.parameters.pop('extra_url')

            extra_url += "?" + utils.urlencode(env.request.parameters)

        dataset = template.PrewikkaTemplate(__name__, "templates/custom.mak").dataset(
            custom_url=self._view_url + extra_url
        )
        return dataset.render()
