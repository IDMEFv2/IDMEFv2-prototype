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

import collections
import re

from prewikka import hookmanager, localization, resource, response, template, utils, version, view
from prewikka.dataprovider import Criterion
from prewikka.localization import format_datetime
from prewikka.views.datasearch import datasearch, elasticsearch


class IDMEFv2Formatter(datasearch.Formatter):
    highlighter = elasticsearch.ElasticsearchHighLighter

    def __init__(self, data_type):
        datasearch.Formatter.__init__(self, data_type)
        self._objects = {"idmefv2.create_time": self._format_time}

    def _format_time(self, finfo, root, obj):
        href = None
        if root.get("idmefv2.id"):
            href = url_for("IDMEFv2DataSearch.details", alertid=root["idmefv2.id"], _default=None, **env.request.menu.get_parameters())

        return resource.HTMLNode("a", format_datetime(obj), href=href, title=_("See IDMEF details"), **{"data-toggle": "tooltip", "data-container": "#main"})

    def format(self, finfo, root, obj):
        if finfo.path in self._objects:
            return self._objects[finfo.path](finfo, root, obj)

        if isinstance(obj, list):
            children = filter(None, [resource.HTMLNode("li", self.format(finfo, root, o)) for o in obj])
            return resource.HTMLNode("ul", *children, _class="object", **{"data-value": utils.json.dumps(obj)})

        return datasearch.Formatter.format(self, finfo, root, obj)

    def format_value(self, field, value):
        node = datasearch.Formatter.format_value(self, re.sub(r"\(\d+\)", "", field), value)

        if field != "severity":
            return node

        class_ = {
            "Info": "btn-info",
            "Low": "btn-success",
            "Medium": "btn-warning",
            "High": "btn-danger",
        }.get(self.highlighter.get_clean_value(value), "btn-default2")

        node._extra = {"_classes": class_}
        return node


class IDMEFv2QueryParser(datasearch.QueryParser):
    _default_sort_order = ["idmefv2.create_time/order_desc"]

    def _groupby_query(self):
        return env.dataprovider.query(self.get_paths(), self.all_criteria, limit=self.limit, offset=self.offset, type=self.type)

    def _query(self):
        order_by = self._sort_order or self._default_sort_order

        return env.dataprovider.get(self.all_criteria, limit=self.limit, offset=self.offset, type=self.type, order_by=order_by)


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
    query_parser = IDMEFv2QueryParser
    criterion_config_default = "criterion"
    groupby_default = ["severity"]
    sort_path_default = "create_time"
    default_columns = collections.OrderedDict([
        ("idmefv2.severity", N_("Severity")),
        ("idmefv2.create_time", N_("Create time")),
        ("idmefv2.category(0)", N_("Category")),
        ("idmefv2.description", N_("Description")),
        ("idmefv2.source(0).ip", N_("Source")),
        ("idmefv2.target(0).ip", N_("Target")),
    ])

    def _get_default_cells(self, obj, search):
        cells = datasearch.DataSearch._get_default_cells(self, obj, search)
        cells["_criteria"] = Criterion("%s.id" % self.type, "=", obj["%s.id" % self.type])
        return cells

    def _get_fields(self):
        return set(env.dataprovider.get_paths(self.type)) | set(self._main_fields)

    def _get_column_property(self, field, pi):
        pi.column_index = pi.path
        if "(" in field:  # Cannot group on list elements
            pi.groupable = False

        return datasearch.COLUMN_PROPERTIES(label=self.default_columns.get("idmefv2.%s" % field, field.capitalize()),
                                            name=field,
                                            index=field,
                                            width=25 if field == "idmefv2.id" else None,
                                            hidden="idmefv2.%s" % field not in self.default_columns)

    def _recurse_idmef(self, output, obj, path=None):
        if isinstance(obj, dict):
            for k, v in obj.items():
                self._recurse_idmef(output, v, "%s.%s" % (path, k) if path else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                self._recurse_idmef(output, v, "%s(%d)" % (path, i))
        else:
            output[path] = obj

    @view.route("/idmefv2/forensic/details/<alertid>")
    def details(self, alertid):
        alert = env.dataprovider.get(Criterion("idmefv2.id", "==", alertid))[0]
        dataset = template.PrewikkaTemplate(__name__, "templates/idmefdetails.mak").dataset({
            "alert": alert._obj.obj["idmefv2"]
        })

        return dataset.render()

    def ajax_details(self):
        result = env.dataprovider.get(utils.json.loads(env.request.parameters["_criteria"]))[0]
        out = {}
        self._recurse_idmef(out, result._obj.obj["idmefv2"])
        return response.PrewikkaResponse(template.PrewikkaTemplate("prewikka.views.datasearch", "templates/details.mak").dataset(
            fields_info=sorted(out.keys(), key=utils.path_sort_key),
            fields_value=out,
            transform=lambda x: re.sub(r"\(\d+\)", "", x)
        ))

    @hookmanager.register("HOOK_RISKOVERVIEW_DATA", _order=3)
    def _set_alerts_summary(self):
        severities = ["High", "Medium", "Low", "Info"]
        alerts = dict(env.dataprovider.query(
            ["idmefv2.severity/group_by", "count(idmefv2.id)"],
            env.request.menu.get_criteria()
        ))

        labels = {
            "Info": utils.AttrObj(title=_("Minimal severity"), label="label-info"),
            "Low": utils.AttrObj(title=_("Low severity"), label="label-success"),
            "Medium": utils.AttrObj(title=_("Medium severity"), label="label-warning"),
            "High": utils.AttrObj(title=_("High severity"), label="label-danger")
        }

        data = []
        for i in severities:
            data.append(
                resource.HTMLNode("a", localization.format_number(alerts.get(i, 0), short=True),
                                  title=labels[i].title, _class="label " + labels[i].label,
                                  href=url_for("IDMEFv2DataSearch.forensic", criteria=Criterion("idmefv2.severity", "==", i)))
            )

        return utils.AttrObj(
            name="idmefv2",
            title=resource.HTMLNode("a", _("Alerts"), href=url_for("IDMEFv2DataSearch.forensic")),
            data=data
        )
