# coding: utf-8
# Copyright (C) 2021 CS-SI. All Rights Reserved.
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

"""DataSearch IDMEFv2 view."""

from __future__ import absolute_import, division, print_function, unicode_literals

import collections
import re

from prewikka import resource, response, template, utils
from prewikka.views.datasearch import datasearch, elasticsearch
from prewikka import version


class IDMEFv2Formatter(datasearch.Formatter):
    highlighter = elasticsearch.ElasticsearchHighLighter

    def __init__(self, data_type):
        datasearch.Formatter.__init__(self, data_type)
        self._objects = {}

    def format(self, finfo, root, obj):
        if finfo.path in self._objects:
            return self._objects[finfo.path](root, obj, finfo.path)

        if isinstance(obj, list):
            children = filter(None, [resource.HTMLNode("li", self.format(finfo, root, o)) for o in obj])
            return resource.HTMLNode("ul", *children, _class="object", **{"data-value": utils.json.dumps(obj)})

        return datasearch.Formatter.format(self, finfo, root, obj)

    def format_value(self, field, value):
        node = datasearch.Formatter.format_value(self, field, value)
        if field != "severity":
            return node

        class_ = {
            "info": "btn-info",
            "low": "btn-success",
            "medium": "btn-warning",
            "high": "btn-danger",
        }.get(value, "btn-default2")

        node._extra = {"_classes": class_}
        return node


class IDMEFv2DataSearch(datasearch.DataSearch):
    plugin_name = "DataSearch: IDMEFv2"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("IDMEFv2 listing page")

    view_permissions = [N_("IDMEFV2_VIEW")]
    view_help = "#incidents"

    type = "idmefv2"
    name = "idmefv2"
    section = N_("Alerts")
    tabs = (N_("Alerts"), N_("Aggregated alerts"))
    formatter = IDMEFv2Formatter
    query_parser = elasticsearch.ElasticsearchQueryParser
    criterion_config_default = "criterion"
    groupby_default = ["severity"]
    sort_path_default = "create_time"
    default_columns = collections.OrderedDict([
        ("idmefv2.severity", N_("Severity")),
        ("idmefv2.create_time", N_("Create time")),
        ("idmefv2.category", N_("Category")),
        ("idmefv2.description", N_("Description")),
        ("idmefv2.source.ip", N_("Source")),
        ("idmefv2.target.ip", N_("Target")),
    ])

    def _get_column_property(self, field, pi):
        return datasearch.COLUMN_PROPERTIES(label=self.default_columns.get("idmefv2.%s" % field, field.capitalize()),
                                            name=field,
                                            index=field,
                                            width=25 if field == "idmefv2.id" else None,
                                            hidden="idmefv2.%s" % field not in self.default_columns)

    def _recurse_idmef(self, output, path, value, rootpath=None):
        if isinstance(value, list):
            for i, v in enumerate(value):
                elems = path.split(".", 1)
                rp = "%s.%s(%d)" % (rootpath, elems[0], i) if rootpath else "%s(%d)" % (elems[0], i)
                self._recurse_idmef(output, elems[1] if len(elems) > 1 else None, v, rp)
        else:
            output["%s.%s" % (rootpath, path) if (rootpath and path) else (rootpath or path)] = value

    def ajax_details(self):
        out = {}
        for param, value in env.request.parameters.items():
            if param in self.fields_info:
                self._recurse_idmef(out, param, value)

        return response.PrewikkaResponse(template.PrewikkaTemplate("prewikka.views.datasearch", "templates/details.mak").dataset(
            fields_info=sorted(out.keys(), key=utils.path_sort_key),
            fields_value=out,
            transform=lambda x: re.sub(r"\(\d+\)", "", x)
        ))
