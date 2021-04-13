# Copyright (C) 2018-2021 CS GROUP - France. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
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

import re

from prewikka import resource, utils


_SENTINEL = object()


class LinkManager(object):
    """Contextual link manager"""

    def __init__(self):
        self._links = {}

        for i in env.config.url:
            self._init_url(i.get_instance_name() or "other", i)

    def add_link(self, label, paths, urlgencb):
        self._register_link(paths, label, urlgencb)

    def _register_link(self, paths, label, url):
        for path in paths:
            self._links.setdefault(path, []).append((label, url))

    def _init_url(self, type, config):
        for option, value in config.items():
            if not self._check_option(option, value):
                continue

            paths = filter(None, re.split('\s|,', config.get("paths", "")))
            self._register_link(list(paths) + [type], option, value)

    def _check_option(self, option, value):
        return option != "paths"

    def get_links(self, path=None, arg=None):
        if arg is None:
            raise ValueError("Parameter 'arg' cannot be None")

        d = {path: self._links.get(path, [])} if path else self._links

        for path, links in d.items():
            for label, url in links:
                yield self._get_link(label, url, arg, path=path)

    def _get_link(self, label, value, arg, path=None):
        d = {"data-path": path} if path else {}
        if callable(value):
            value = value(arg)
        else:
            value = value.replace("$value", utils.url.quote_plus(arg.encode("utf-8")))

        return resource.HTMLNode("a", _(label.capitalize()), href=value, **d)
