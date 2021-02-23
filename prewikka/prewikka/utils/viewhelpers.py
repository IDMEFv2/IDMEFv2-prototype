# Copyright (C) 2016-2020 CS GROUP - France. All Rights Reserved.
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

from prewikka import response, utils, view


def GridParameters(name):
    class _GridParameters(view.Parameters):
        def register(self):
            self.optional("jqgrid_params_%s" % name, utils.json.loads, {}, persist=True)

    return _GridParameters


class GridAjaxParameters(view.Parameters):
    """Handle parameters sent by jqGrid."""
    def register(self):
        self.optional("query", text_type)  # query string
        self.optional("page", int, 1)  # requested page
        self.optional("rows", int, 10)  # number of rows requested
        self.optional("sort_index", text_type)  # sorting column
        self.optional("sort_order", text_type)  # sort order (asc or desc)

    @utils.deprecated
    def get_response(self, total_results):
        # Ceil division (use // instead of / for Python3 compatibility):
        nb_pages = (total_results - 1) // self["rows"] + 1
        return {"total": nb_pages, "page": self["page"], "rows": [], "records": total_results}


class GridAjaxResponse(response.PrewikkaResponse):
    def __init__(self, rows, total_results, **kwargs):
        response.PrewikkaResponse.__init__(self)

        # Ceil division (use // instead of / for Python3 compatibility):
        kwargs["total"] = (total_results - 1) // int(env.request.parameters.get("rows", 10)) + 1
        kwargs["rows"] = rows
        kwargs["records"] = total_results
        self.data = kwargs
