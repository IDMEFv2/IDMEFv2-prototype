# VERSION: 1.0
# AUTHOR: Prelude Team <support.prelude@csgroup.eu>
# DESCRIPTION: Triggered by multiple failed login attempts
# Copyright (C) 2006 G Ramon Gomez <gene at gomezbrothers dot com>
# Copyright (C) 2009-2021 CS GROUP - France <support.prelude@csgroup.eu>
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
from preludecorrelator.pluginmanager import Plugin
from preludecorrelator.context import Context


class BruteForcePlugin(Plugin):
    def _BruteForce(self, idmef):
        sadd = [sorted(node.get('node.address(*).address')) for node in idmef.get('alert.source(*)', False)]
        tadd = [sorted(node.get('node.address(*).address')) for node in idmef.get('alert.target(*)', False)]

        for source in sadd:
            if not source:
                continue

            for target in tadd:
                if not target:
                    continue

                ctx = Context(("BRUTE ST", source, target), {"expire": 120, "threshold": 5, "alert_on_expire": True},
                              update=True, idmef=idmef, ruleid=self.name)
                if ctx.getUpdateCount() == 0:
                    ctx.set("alert.classification.text", "Brute Force attack")
                    ctx.set("alert.correlation_alert.name", "Multiple failed login")
                    ctx.set("alert.assessment.impact.severity", "high")
                    ctx.set("alert.assessment.impact.description",
                            "Multiple failed attempts have been made to login using different account")

    def _BruteUserForce(self, idmef):
        userid = idmef.get("alert.target(*).user.user_id(*).name")
        if not userid:
            return

        for user in userid:
            ctx = Context(("BRUTE USER", user), {"expire": 120, "threshold": 5, "alert_on_expire": True},
                          update=True, idmef=idmef, ruleid=self.name)
            if ctx.getUpdateCount() == 0:
                ctx.set("alert.classification.text", "Brute Force attack")
                ctx.set("alert.correlation_alert.name", "Multiple failed login against a single account")
                ctx.set("alert.assessment.impact.severity", "high")
                ctx.set("alert.assessment.impact.description",
                        "Multiple failed attempts have been made to login to a user account")

    def run(self, idmef):
        if not idmef.match("alert.classification.text", re.compile("[Ll]ogin|[Aa]uthentication")):
            return

        # FIXME: In the future, we might want to include successfull authentication
        # following a number of failed events, so that generated CorrelationAlert
        # includes full details.
        if idmef.get("alert.assessment.impact.completion") == "succeeded":
            return

        self._BruteForce(idmef)
        self._BruteUserForce(idmef)
