# VERSION: 1.0
# AUTHOR: Prelude Team <support.prelude@csgroup.eu>
# DESCRIPTION: Triggered by a host becoming the source of many alerts after having been the target of similar alerts
# Copyright (C) 2006 G Ramon Gomez <gene at gomezbrothers dot com>
# Copyright (C) 2009-2021 CS GROUP - France <support.prelude@csgroup.eu>
# All Rights Reserved.
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

# This rule looks for events against a host, records the messageid, then sets
# a timer of 600 seconds.   If the host then replays the event against
# other hosts multiple times, an event is generated.

from preludecorrelator import context
from preludecorrelator.pluginmanager import Plugin


class WormPlugin(Plugin):
    REPEAT = 5

    def __init__(self, env):
        Plugin.__init__(self, env)
        self.__repeat_target = self.getConfigValue("repeat-target", self.REPEAT, type=int)

    def run(self, idmef):
        ctxt = idmef.get("alert.classification.text")
        if not ctxt:
            return

        # Create context for classification combined with all the target.
        tlist = {}
        for target in idmef.get("alert.target(*).node.address(*).address"):
            ctx = context.Context(("WORM HOST", ctxt, target), {"expire": 300},
                                  overwrite=False, idmef=idmef, ruleid=self.name)
            if ctx.getUpdateCount() == 0:
                ctx._target_list = {}

            tlist[target] = True

        for source in idmef.get("alert.source(*).node.address(*).address"):
            # We are trying to see whether a previous target is now attacking other hosts
            # thus, we check whether a context exist with this classification combined to
            # this source.
            ctx = context.search(("WORM HOST", ctxt, source))
            if not ctx:
                continue

            plen = len(ctx._target_list)
            ctx._target_list.update(tlist)

            nlen = len(ctx._target_list)
            if nlen > plen:
                ctx.update(idmef=idmef)

            if nlen >= self.__repeat_target:
                ctx.set("alert.classification.text", "Possible Worm Activity")
                ctx.set("alert.correlation_alert.name", "Source host is repeating actions taken against it recently")
                ctx.set("alert.assessment.impact.severity", "high")
                ctx.set("alert.assessment.impact.description",
                        source + " has repeated actions taken against it recently at least %d times. It may have been "
                                 "infected with a worm." % self.__repeat_target)
                ctx.alert()
                ctx.destroy()
