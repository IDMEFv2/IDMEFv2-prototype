# VERSION: 1.0
# AUTHOR: Prelude Team <support.prelude@csgroup.eu>
# DESCRIPTION: Triggered by a successful action happening outside of business hours
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

import time
from preludecorrelator.idmef import IDMEF
from preludecorrelator.pluginmanager import Plugin


# Alert only on saturday and sunday, and everyday from 6:00pm to 9:00am.
class BusinessHourPlugin(Plugin):
    def run(self, idmef):

        t = time.localtime(int(idmef.get("alert.create_time")))

        if not (t.tm_wday == 5 or t.tm_wday == 6 or t.tm_hour < 9 or t.tm_hour > 17):
            return

        if idmef.get("alert.assessment.impact.completion") != "succeeded":
            return

        ca = IDMEF(ruleid=self.name)
        ca.addAlertReference(idmef)
        ca.set("alert.classification", idmef.get("alert.classification"))
        ca.set("alert.correlation_alert.name", "Critical system activity on day off")
        ca.alert()
