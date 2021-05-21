# VERSION: 1.0
# AUTHOR: Prelude Team <support.prelude@csgroup.eu>
# DESCRIPTION: Triggered when events have not been dropped for a host known to be protected by a firewall
# Copyright (C) 2009-2021 CS GROUP - France. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>
#
# This file is part of the Prelude-Correlator program.
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

import re
import time
from preludecorrelator import context
from preludecorrelator.pluginmanager import Plugin


def _evict(ctx):
    now = time.time()
    for target, values in ctx._protected_hosts.items():
        if now - values[0] > ctx._flush_protected_hosts:
            ctx._protected_hosts.pop(target)

    ctx.reset()


def _alert(ctx):
    cnt = 0
    fw = context.search("FIREWALL INFOS")

    for idmef in ctx.candidates:
        source = idmef.get("alert.source(0).node.address(0).address")
        target = idmef.get("alert.target(0).node.address(0).address")
        dport = str(idmef.get("alert.target(0).service.port", 0))

        if target not in fw._protected_hosts:
            continue

        if (source + dport) in fw._protected_hosts[target][1]:
            continue

        cnt += 1
        ctx.addAlertReference(idmef)

    if cnt > 0:
        ctx.set("alert.classification.text", "Events hit target")
        ctx.set("alert.assessment.impact.severity", "medium")
        ctx.set("alert.assessment.impact.description",
                "The target are known to be protected by a Firewall device, but a set of event have not been dropped")
        ctx.set("alert.correlation_alert.name", "No firewall block observed")
        ctx.alert()

    ctx.destroy()


class FirewallPlugin(Plugin):
    def __init__(self, env):
        Plugin.__init__(self, env)
        self._flush_protected_hosts = self.getConfigValue("flush-protected-hosts", 3600, type=int)

    def run(self, idmef):
        source = idmef.get("alert.source(0).node.address(0).address")
        scat = idmef.get("alert.source(0).node.address(0).category")
        target = idmef.get("alert.target(0).node.address(0).address")
        tcat = idmef.get("alert.target(0).node.address(0).category")

        dport = idmef.get("alert.target(0).service.port")
        if not source or not target or not dport:
            return

        if scat not in ("ipv4-addr", "ipv6-addr") or tcat not in ("ipv4-addr", "ipv6-addr"):
            return

        ctx = context.Context("FIREWALL INFOS",
                              {"expire": self._flush_protected_hosts, "alert_on_expire": _evict},
                              update=True, ruleid=self.name)
        if ctx.getUpdateCount() == 0:
            ctx._protected_hosts = {}
            ctx._flush_protected_hosts = self._flush_protected_hosts

        if idmef.match("alert.classification.text", re.compile("[Pp]acket [Dd]ropped|[Dd]enied")):
            if target not in ctx._protected_hosts:
                ctx._protected_hosts[target] = [0, {}]

            ctx._protected_hosts[target][0] = float(idmef.getTime())
            ctx._protected_hosts[target][1][source + str(dport)] = True
        else:
            if target not in ctx._protected_hosts:
                return

            if time.time() - ctx._protected_hosts[target][0] > self._flush_protected_hosts:
                ctx._protected_hosts.pop(target)
                return

            if (source + str(dport)) in ctx._protected_hosts[target][1]:
                return

            ctx = context.Context(("FIREWALL", source), {"expire": 120, "alert_on_expire": _alert},
                                  update=True, ruleid=self.name)
            if ctx.getUpdateCount() == 0:
                ctx.candidates = []

            ctx.candidates.append(idmef)
