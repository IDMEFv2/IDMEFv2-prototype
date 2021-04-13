# Copyright (C) 2014-2021 CS GROUP - France. All Rights Reserved.
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

import collections
import os.path
import mako.exceptions
import mako.lookup
import mako.template
import pkg_resources

from prewikka import siteconfig
from prewikka.utils import cache


_MAKO_FILTERS = ["html.escape"]
_MAKO_GENERIC_ARGS = {
    "default_filters": _MAKO_FILTERS,
    "buffer_filters": _MAKO_FILTERS,
    "input_encoding": 'utf8', "imports": [
        'from prewikka.utils import html, json',
        'from prewikka.utils.html.helpers import checked, disabled, selected, csrftoken'
    ],
    "future_imports": ["unicode_literals"],
    "module_directory": os.path.join(siteconfig.tmp_dir, "mako")
}

_MODULE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
_MAKO_TEMPLATE_LOOKUP = mako.lookup.TemplateLookup(directories=[_MODULE_PATH], **_MAKO_GENERIC_ARGS)


# We cannot inherit dict directly because it's __json__() method would never be called. Simplejson
# only call the user provided encoding callback when the object is not known to be serializable.

class _Dataset(collections.MutableMapping):
    def __init__(self, template, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        self._template = template

    def render(self):
        return self._template.render(**self._d)

    def __json__(self):
        return self.render()

    def __len__(self):
        return self._d.__len__()

    def __setitem__(self, key, value):
        return self._d.__setitem__(key, value)

    def __getitem__(self, key):
        return self._d.__getitem__(key)

    def __delitem__(self, key):
        return self._d.__delitem__(key)

    def __iter__(self):
        return self._d.__iter__()


class _PrewikkaTemplate(object):
    def __init__(self, *args):
        if len(args) == 2:
            self._name = pkg_resources.resource_filename(*args)
        else:
            self._name = args[0]

        self._error = None

        try:
            self._template = mako.template.Template(filename=self._name, lookup=_MAKO_TEMPLATE_LOOKUP, **_MAKO_GENERIC_ARGS)
        except Exception as e:
            self._error = e

    def __json__(self):
        return self._template.render()

    def dataset(self, *args, **kwargs):
        return _Dataset(self, *args, **kwargs)

    def render(self, **kwargs):
        if self._error:
            raise self._error

        return self._template.render(**kwargs)


class _PrewikkaTemplateProxy(object):
    @cache.memoize("cache")
    def __call__(self, *args):
        return _PrewikkaTemplate(*args)

    @classmethod
    def __instancecheck__(cls, instance):
        return isinstance(instance, (_PrewikkaTemplate, _Dataset))


PrewikkaTemplate = _PrewikkaTemplateProxy()
