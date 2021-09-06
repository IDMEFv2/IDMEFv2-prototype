# Copyright (C) 2016-2021 CS GROUP - France. All Rights Reserved.
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

import collections
import copy
import itertools
import os
import voluptuous
import yaml

from prewikka import error, hookmanager
from prewikka.utils import cache


_SCHEMA = voluptuous.Schema([{
    "name": str,
    "icon": str,
    "default": bool,
    voluptuous.Required("categories", default=[]): [{
        "name": str,
        "icon": str,
        voluptuous.Required("sections", default=[]): [{
            voluptuous.Required("name"): str,
            "icon": str,
            voluptuous.Required("tabs", default=[]): [str],
            "default_tab": str,
            "expand": bool
        }]
    }]
}])


class MenuManager(object):
    default_endpoint = None

    """
    Handle section placement in the menus.
    """
    def __init__(self):
        self._declared_sections = {}
        self._loaded_sections = {}
        self._default_view = None

        filename = env.config.interface.get("menu_order", "menu.yml")
        if not os.path.isabs(filename):
            filename = os.path.join(env.config.basedir, filename)

        try:
            with open(filename, "r") as f:
                self._menus = _SCHEMA(yaml.safe_load(f))
        except (IOError, yaml.error.YAMLError, voluptuous.Invalid) as e:
            raise error.PrewikkaUserError(N_("Menu error"), N_("The provided YAML menu is invalid"), details=e)

        if not self._menus:
            raise error.PrewikkaUserError(N_("Menu error"), N_("Empty menu"))

        default_menu = False

        for menu in self._menus:
            if "name" not in menu and "icon" not in menu:
                raise error.PrewikkaUserError(N_("Menu error"), N_("Menu without a name in %s", filename))

            if menu.get("default"):
                if default_menu:
                    raise error.PrewikkaUserError(N_("Menu error"), N_("Multiple default menus"))

                default_menu = True

            for category in menu["categories"]:
                for section in category["sections"]:
                    if "default_tab" in section:
                        if self._default_view:
                            raise error.PrewikkaUserError(N_("Menu error"), N_("Multiple default views"))

                        self._default_view = (section["name"], section["default_tab"])

                    self._declared_sections[section["name"]] = collections.OrderedDict((v, idx) for idx, v in enumerate(section["tabs"]))

        if not default_menu:
            self._menus[-1]["default"] = True

    @cache.request_memoize("get_sections")
    def get_sections(self):
        ret = {}
        _loaded_sections = copy.deepcopy(self._loaded_sections)

        for section, tab, endpoint in itertools.chain.from_iterable(hookmanager.trigger("HOOK_MENU_LOAD")):
            _loaded_sections.setdefault(section, collections.OrderedDict())[tab] = endpoint

        for section, tabs in _loaded_sections.items():
            if section not in self._declared_sections:
                ret[section] = tabs
            else:
                ret[section] = collections.OrderedDict()
                for name in sorted(tabs.keys(), key=lambda tab: self._declared_sections[section].get(tab, 100)):
                    ret[section][name] = tabs[name]

        return ret

    def get_menus(self):
        return self._menus

    def get_declared_sections(self):
        return self._declared_sections

    def add_section_info(self, section, tab, endpoint, **kwargs):
        self._loaded_sections.setdefault(section, collections.OrderedDict())[tab] = (endpoint, kwargs)

        if (section, tab) == self._default_view:
            self.default_endpoint = endpoint
