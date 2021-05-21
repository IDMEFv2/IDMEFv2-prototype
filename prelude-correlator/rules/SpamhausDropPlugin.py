# VERSION: 1.0
# AUTHOR: Prelude Team <support.prelude@csgroup.eu>
# DESCRIPTION: Triggered when the source IP is present in the Spamhaus reputation database
# CATEGORY: CTI
# Copyright (C) 2009-2021 CS GROUP - France. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>
# Author: Wes Young <wes@barely3am.com>
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

from preludecorrelator import require, log, download
from preludecorrelator.pluginmanager import Plugin, PluginDependenciesError
from preludecorrelator.context import Context

try:
    # Note:
    #   Versions 0.7.10 to 0.7.15 (inclusive) are known to be very slow
    #   due to a bug in python-netaddr.
    #   See https://github.com/drkjam/netaddr/issues/94 for more information
    import netaddr
except:
    raise PluginDependenciesError("missing netaddr module, https://pypi.python.org/pypi/netaddr")

logger = log.getLogger(__name__)

if tuple(int(x) for x in netaddr.__version__.split(".")) >= (0, 7):
    from netaddr import IPAddress, IPNetwork, IPSet
else:
    from netaddr import IP as IPAddress
    from netaddr import CIDR as IPNetwork

    class IPSet(list):
        def __contains__(self, y):
            for i in iter(self):
                if y in i:
                    return True

            return False

        def add(self, obj):
            self.append(obj)


class SpamhausDownload(download.HTTPDownloadCache):
    def __init__(self, filename, uri, timeout, reload):
        download.HTTPDownloadCache.__init__(self, "SpamhausDrop", filename, uri, timeout, reload, logger)

    def parse(self, data):
        mynets = IPSet()

        for line in data.split("\n"):
            if not line or line[0] == ';':
                continue

            ip, sbl = line.split(';')
            ip = IPNetwork(ip.strip())
            mynets.add(ip)

        return mynets


class SpamhausDropPlugin(Plugin):
    RELOAD = 7 * 24 * 60 * 60
    URI = "https://www.spamhaus.org/drop/drop.txt"
    TIMEOUT = 10

    def __init__(self, env):
        Plugin.__init__(self, env)

        reload = self.getConfigValue("reload", self.RELOAD, type=int)
        filename = self.getConfigValue("filename", require.get_data_filename("spamhaus_drop.dat",
                                                                             module=__name__,
                                                                             profile=env.profile))
        uri = self.getConfigValue("uri", self.URI)
        timeout = self.getConfigValue("timeout", self.TIMEOUT, type=float)

        self.__data = SpamhausDownload(filename, uri, timeout, reload)

    def run(self, idmef):
        for source in idmef.get("alert.source(*).node.address(*).address"):
            try:
                addr = IPAddress(source)
            except:
                continue

            if addr in self.__data.get():
                ca = Context(("SPAMHAUS", source), {"expire": 20, "alert_on_expire": True},
                             update=True, idmef=idmef, ruleid=self.name)
                if ca.getUpdateCount() == 0:
                    ca.set("alert.classification.text", "Source IP matching a CTI database")
                    ca.set("alert.correlation_alert.name", "Source IP matching a CTI database")
                    ca.set("alert.assessment.impact.description",
                           "Spamhaus gathered this IP address in their DROP list - %s" % source)
                    ca.set("alert.assessment.impact.severity", "medium")
