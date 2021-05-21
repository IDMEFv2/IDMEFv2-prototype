# VERSION: 1.0
# AUTHOR: Prelude Team <support.prelude@csgroup.eu>
# DESCRIPTION: Triggered by two SSH attempts happening to the same target and user but through different methods
# Copyright (C) 2009-2021 CS GROUP - France. All Rights Reserved.
# Author: Sebastien Tricaud <stricaud@inl.fr>
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

from preludecorrelator.pluginmanager import Plugin
from preludecorrelator.context import Context


def alert(ctx):
    if len(ctx.authtype) > 1:
        ctx.set("alert.classification.text", "Multiple authentication methods")
        ctx.set("alert.correlation_alert.name", "Multiple authentication methods")
        ctx.set("alert.assessment.impact.severity", "medium")
        ctx.set("alert.assessment.impact.description",
                "Multiple ways of authenticating a single user have been found over SSH. If passphrase is the only "
                "allowed method, make sure you disable passwords.")
        ctx.alert()
    ctx.destroy()


class OpenSSHAuthPlugin(Plugin):
    def run(self, idmef):
        if idmef.get("alert.analyzer(-1).manufacturer") != "OpenSSH":
            return

        if idmef.get("alert.assessment.impact.completion") != "succeeded":
            return

        data = idmef.get("alert.additional_data('Authentication method').data")
        if not data:
            return

        data = data[0]
        for username in idmef.get("alert.target(*).user.user_id(*).name"):
            for target in idmef.get("alert.target(*).node.address(*).address"):
                ctx = Context(("SSHAUTH", target, username), {"expire": 30, "alert_on_expire": alert},
                              update=True, ruleid=self.name)
                if ctx.getUpdateCount() == 0:
                    ctx.authtype = {data: True}
                    ctx.addAlertReference(idmef)

                elif data not in ctx.authtype:
                    ctx.authtype[data] = True
                    ctx.addAlertReference(idmef)
