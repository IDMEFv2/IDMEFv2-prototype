# coding: utf-8
# Copyright (C) 2018-2020 CS GROUP - France. All Rights Reserved.
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

"""DataSearch heartbeat view."""

from __future__ import absolute_import, division, print_function, unicode_literals

import collections

from prewikka import version

from . import idmef


class HeartbeatFormatter(idmef.IDMEFFormatter):
    def __init__(self, data_type):
        idmef.IDMEFFormatter.__init__(self, data_type)
        self._objects = {"heartbeat.create_time": self._format_time}


class HeartbeatQueryParser(idmef.IDMEFQueryParser):
    _sort_order = ["heartbeat.create_time/order_desc"]


class HeartbeatDataSearch(idmef.IDMEFDataSearch):
    plugin_name = "DataSearch: Heartbeats"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Heartbeat listing page")

    type = "heartbeat"
    name = "heartbeats"
    section = N_("Monitoring")
    tabs = (N_("Heartbeats"), N_("Aggregated heartbeats"))
    formatter = HeartbeatFormatter
    query_parser = HeartbeatQueryParser
    criterion_config_default = "criterion"
    sort_path_default = "create_time"
    groupby_default = ["analyzer(-1).name"]
    default_columns = collections.OrderedDict([
        ("heartbeat.create_time", N_("Date")),
        ("heartbeat.analyzer(-1).name", N_("Agent")),
        ("heartbeat.analyzer(-1).node.address(*).address", N_("Node address")),
        ("heartbeat.analyzer(-1).node.name", N_("Node name")),
        ("heartbeat.analyzer(-1).model", N_("Model"))
    ])
    _delete_confirm = N_("Delete the selected heartbeats?")
