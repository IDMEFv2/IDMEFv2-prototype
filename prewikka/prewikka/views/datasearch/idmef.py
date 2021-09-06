# coding: utf-8
# Copyright (C) 2017-2021 CS GROUP - France. All Rights Reserved.
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

"""DataSearch IDMEF view."""

from prewikka import dataprovider, resource, response, template, utils, view
from prewikka.localization import format_datetime

from . import datasearch

import collections
import prelude


class IDMEFHighLighter(datasearch.HighLighter):
    _word_separators = ["\n"]


class IDMEFFormatter(datasearch.Formatter):
    highlighter = IDMEFHighLighter

    def _format_time(self, finfo, root, obj):
        href = None
        if root["%s.messageid" % self.type]:
            href = url_for("%ssummary.render" % self.type, messageid=root["%s.messageid" % self.type], _default=None, **env.request.menu.get_parameters())

        return resource.HTMLNode("a", format_datetime(obj), href=href, title=_("See IDMEF details"), **{"data-toggle": "tooltip", "data-container": "#main"})

    def _format_value(self, obj, iclass, default="", label=True, _class="", tooltip=None):
        key = text_type(iclass)
        if not obj:
            return default

        value = obj.get(key)
        if not value:
            return default

        if label:
            label = resource.HTMLNode("label", key, ":")
        else:
            label = ""

        field = ".".join([obj.path.split(".", 1)[-1], key])

        kwargs = {}
        if tooltip:
            kwargs = {
                "title": tooltip,
                "data-toggle": "tooltip",
                "data-placement": "top",
                "data-container": "#main"
            }

        return resource.HTMLNode("li", label, self.format_value(field, value), _class="%s %s dp-%d" % (_class, key, self._get_priority(iclass)), **kwargs)

    @staticmethod
    def _get_priority(obj):
        return int(obj.getAttributes().get("priority", 100))

    def _format_object(self, root, child, iclass):
        out2 = []
        key = text_type(iclass)

        child = child if isinstance(child, collections.Iterable) else [child]
        for j in filter(None, map(lambda x: self._format_generic(root, x), child)):
            out2.append(resource.HTMLNode("ul", *j, _class="object %s dp-%d" % (key, self._get_priority(iclass))))

        if out2:
            if iclass.isList():
                return resource.HTMLNode("ul", *[resource.HTMLNode("li", o) for o in out2], _class="list %s dp-%d" % (key, self._get_priority(iclass)))
            else:
                return resource.HTMLNode("", resource.HTMLNode("label", key, _class=key), out2[0])

    def _format_generic(self, root, obj):
        out = []

        for iclass in sorted(self.get_childs(obj), key=self._get_priority):
            child = obj.get(text_type(iclass))
            if child is None:
                continue

            if self._get_priority(iclass) != 0:
                continue

            vtype = iclass.getValueType()
            if vtype == prelude.IDMEFValue.TYPE_CLASS:
                o = self._format_object(root, child, iclass)
                ret = resource.HTMLNode("li", o) if o else None
            else:
                ret = self._format_value(obj, iclass)

            if ret:
                out.append(ret)

        return out

    def format(self, finfo, root, obj):
        if finfo.path in self._objects:
            return self._objects[finfo.path](finfo, root, obj)

        try:
            cl = prelude.IDMEFClass(finfo.path)
            if cl.getValueType() == prelude.IDMEFValue.TYPE_CLASS:
                return self._format_object(root, obj, cl)
        except Exception:
            pass

        return datasearch.Formatter.format(self, finfo, root, obj)

    def get_childs(self, obj):
        i = 0
        cl = prelude.IDMEFClass(obj.getId())
        while True:
            try:
                child = cl.get(i)
            except Exception:
                break

            i += 1
            yield child

    def __contains__(self, k):
        return k in self._objects


class IDMEFQueryParser(datasearch.QueryParser):
    def _groupby_query(self):
        return env.dataprovider.query(self.get_paths(), self.all_criteria, limit=self.limit, offset=self.offset, type=self.type)

    def _query(self):
        order_by = self._sort_order or self._default_sort_order

        # FIXME: we could avoid performing two queries if libpreludedb supported CURSOR.
        ret = env.dataprovider.get(self.all_criteria, limit=self.limit, offset=self.offset, type=self.type, order_by=order_by)
        ret.total = env.dataprovider.query(["count(1)"], self.all_criteria, type=self.type)[0][0]

        return ret


class IDMEFDataSearch(datasearch.DataSearch):
    view_permissions = [N_("IDMEF_VIEW")]
    expert_enabled = True

    def __init__(self, *args, **kwargs):
        self._extra_table_fields = []

        config = env.config.datasearch.get_instance_by_name(self.type)
        if config:
            self._extra_table_fields = [x.strip() for x in config.get("extra_fields").split(",")]

        datasearch.DataSearch.__init__(self, *args, **kwargs)
        view.route("/%s/delete" % self.type, method=self.delete, methods=["POST"], permissions=["IDMEF_ALTER"])
        self.columns_properties["create_time"].width = 110

    def _get_default_cells(self, obj, search):
        cells = datasearch.DataSearch._get_default_cells(self, obj, search)
        cells["_criteria"] = dataprovider.Criterion("%s.messageid" % self.type, "=", obj["%s.messageid" % self.type])
        return cells

    def _get_fields(self):
        return set(env.dataprovider.get_paths(self.type)) | set(self._main_fields) | set(self._extra_table_fields)

    def _get_column_property(self, field, pi):
        pi.column_index = pi.path

        hidden = pi.path not in self._main_fields
        if hidden and pi.path not in self._extra_table_fields:
            return None

        label = self.default_columns.get("%s.%s" % (self.type, field), field.capitalize())
        sortable = prelude.IDMEFPath(pi.path).getValueType() != prelude.IDMEFValue.TYPE_CLASS

        return datasearch.COLUMN_PROPERTIES(label=label, name=field, index=field, hidden=hidden, sortable=sortable)

    def get_forensic_actions(self):
        ret = []

        if env.request.user.has("IDMEF_ALTER"):
            ret = [resource.HTMLNode("button", _("Delete"), **{
                "form": "datasearch_grid_form",
                "type": "submit",
                "formaction": url_for(".delete"),
                "formmethod": "POST",
                "class": "btn btn-danger needone",
                "data-confirm": _(self._delete_confirm),
            })]

        return datasearch.DataSearch.get_forensic_actions(self) + ret

    def delete(self):
        criteria = dataprovider.Criterion()
        for i in env.request.parameters.getlist("criteria", type=utils.json.loads):
            criteria |= i

        if criteria:
            env.dataprovider.delete(criteria)
            return response.PrewikkaResponse({"type": "reload", "target": "#main", "options": {"current": False}})

    def _recurse_idmef(self, output, obj):
        for i in self._formatter.get_childs(obj):
            vtype = i.getValueType()
            child = obj.get(i.getName())
            if child is None:
                continue

            if vtype == prelude.IDMEFValue.TYPE_CLASS:
                if isinstance(child, collections.Iterable):
                    for j in child:
                        self._recurse_idmef(output, j)
                else:
                    self._recurse_idmef(output, child)

            else:
                if isinstance(child, utils.CachingIterator):
                    for idx, j in enumerate(child):
                        path = obj.path + "." + i.getName() + "(%d)" % idx
                        output[path.split(".", 1)[-1]] = j
                else:
                    path = obj.path + "." + i.getName()
                    output[path.split(".", 1)[-1]] = child

    def ajax_details(self):
        obj = env.dataprovider.get(utils.json.loads(env.request.parameters["_criteria"]))[0]

        out = {}
        self._recurse_idmef(out, obj)

        return response.PrewikkaResponse(template.PrewikkaTemplate(__name__, "templates/details.mak").dataset(fields_info=sorted(out.keys(), key=utils.path_sort_key), fields_value=out))
