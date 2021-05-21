# VERSION: 1.0
# AUTHOR: Prelude Team <support.prelude@csgroup.eu>
# DESCRIPTION: Triggered when the source IP is present in the CIArmy reputation database
# CATEGORY: CTI
# Copyright (C) 2015-2021 CS GROUP - France. All Rights Reserved.
# Author: Thomas Andrejak <thomas.andrejak@c-s.fr>
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

from preludecorrelator import context, require, log, download
from preludecorrelator.pluginmanager import Plugin

logger = log.getLogger(__name__)


class CIArmyDownloader(download.HTTPDownloadCache):
    def __init__(self, filename, uri, timeout, reload):
        download.HTTPDownloadCache.__init__(self, "CIArmy", filename, uri, timeout, reload, logger)

    def __ipNormalize(self, ip):
        return ".".join([i.lstrip("0") for i in ip.split(".")])

    def parse(self, data):
        ret = []

        for line in data.split("\n"):
            if not line or line[0] == '#':
                continue

            ip = line
            ret.append(self.__ipNormalize(ip))

        return ret


class CIArmyPlugin(Plugin):
    CIARMY_RELOAD = 7 * 24 * 60 * 60
    CIARMY_URI = "https://cinsscore.com/list/ci-badguys.txt"
    CIARMY_TIMEOUT = 10

    def __init__(self, env):
        Plugin.__init__(self, env)

        uri = self.getConfigValue("uri", self.CIARMY_URI)
        timeout = self.getConfigValue("timeout", self.CIARMY_TIMEOUT, type=float)
        reload = self.getConfigValue("reload", self.CIARMY_RELOAD, type=int)
        filename = self.getConfigValue("filename",
                                       require.get_data_filename("ciarmy.dat", module=__name__, profile=env.profile))

        self.__data = CIArmyDownloader(filename, uri, timeout, reload)

    def run(self, idmef):
        data = self.__data.get()

        for source in idmef.get("alert.source(*).node.address(*).address"):
            if source in data:
                ca = context.Context(("CIARMY", source), {"expire": 20, "alert_on_expire": True}, update=True,
                                     idmef=idmef, ruleid=self.name)
                if ca.getUpdateCount() == 0:
                    ca.set("alert.classification.text", "Source IP matching a CTI database")
                    ca.set("alert.correlation_alert.name", "Source IP matching a CTI database")
                    ca.set("alert.assessment.impact.description",
                           "CIArmy gathered this IP address from firewall drop logs (%s)" % source)
                    ca.set("alert.assessment.impact.severity", "high")
