#!/usr/bin/env python

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

import os

from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.sdist import sdist

try:
    import urllib.request as urlreq
except:
    import urllib2 as urlreq


PRELUDE_CORRELATOR_VERSION = "5.2.0"


class my_sdist(sdist):
    user_options = sdist.user_options + [('disabledl', None, "Disable the download of databases")]
    disabledl = False

    def _downloadDatabase(self, dname, url, filename):
        print("Downloading %s database, this might take a while..." % (dname))
        req = urlreq.Request(url)
        req.add_header('User-agent', 'Mozilla 5.10')
        r = urlreq.urlopen(req)
        fd = open(filename, "w")
        fd.write(r.read())
        fd.close()

    def __init__(self, *args, **kwargs):
        fin = os.popen('git log --summary --stat --no-merges --date=short', 'r')
        fout = open('ChangeLog', 'w')
        fout.write(fin.read())
        fout.close()
        sdist.__init__(self, *args)

    def run(self):
        if self.disabledl:
            print("Automatic downloading of databases is disabled.")
            print("As a result, they won't be included in the generated source distribution.")
        else:
            self._downloadDatabase("DShield", "https://www.dshield.org/ipsascii.html?limit=10000", "rules/dshield.dat")
            self._downloadDatabase("Spamhaus", "https://www.spamhaus.org/drop/drop.txt", "rules/spamhaus_drop.dat")
            self._downloadDatabase("CIArmy", "https://cinsscore.com/list/ci-badguys.txt", "rules/ciarmy.dat")
        sdist.run(self)


class my_install(install):
    def run(self):
        for dirname, flist in self.distribution.data_files:
            prefix = self.prefix
            if self.prefix == "/usr":
                prefix = os.sep

            destdir = os.path.join(os.path.normpath((self.root or '') + prefix), dirname)
            self.mkpath(destdir)

            for f in flist:
                dest = os.path.join(destdir, os.path.basename(f))
                if dest[-4:] == "conf" and os.path.exists(dest):
                    dest += "-dist"

                self.copy_file(f, dest)

        self.distribution.data_files = []
        install.run(self)
        self.init_siteconfig(prefix)

    def init_siteconfig(self, prefix):
        with open(os.path.join(self.install_lib, "preludecorrelator", "siteconfig.py"), "w") as config:
            config.write("conf_dir = '%s'\n" % os.path.abspath(os.path.join(prefix, "etc", "prelude-correlator")))
            config.write("lib_dir = '%s'\n" % os.path.abspath(os.path.join(prefix, "var", "lib", "prelude-correlator")))


setup(
    name="prelude-correlator",
    version=PRELUDE_CORRELATOR_VERSION,
    maintainer="Prelude Team",
    maintainer_email="support.prelude@csgroup.eu",
    author="Yoann Vandoorselaere",
    author_email="yoannv@gmail.com",
    license="BSD",
    url="https://www.prelude-siem.org",
    download_url="https://www.prelude-siem.org/projects/prelude/files",
    description="Prelude-Correlator perform real time correlation of events received by Prelude",
    long_description="""
Prelude-Correlator perform real time correlation of events received by Prelude.

Several isolated alerts, generated from different sensors, can thus
trigger a single CorrelationAlert should the events be related. This
CorrelationAlert then appears within the Prewikka interface and
indicates the potential target information via the set of correlation
rules.

Signature creation with Prelude-Correlator is based on the Python
programming language. Prelude's integrated correlation engine is
distributed with a default set of correlation rules, yet you still
have the opportunity to modify and create any correlation rule that
suits your needs.
""",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Security",
        "Topic :: System :: Monitoring"
    ],
    packages=find_packages(".", exclude=["rules"]),
    entry_points={
        'console_scripts': [
            'prelude-correlator = preludecorrelator.main:main',
        ],
        'preludecorrelator.plugins': [
        ]
    },
    package_data={},
    data_files=[
        ("etc/prelude-correlator", ["prelude-correlator.conf"]),
        ("etc/prelude-correlator/conf.d", ['data/conf.d/README']),
        ("etc/prelude-correlator/rules/python", [
            os.path.join('rules', x) for x in os.listdir('rules') if x.endswith('.py')
        ]),
        ("var/lib/prelude-correlator/prelude-correlator", [
            os.path.join('rules', x) for x in os.listdir('rules') if x.endswith('.dat')
        ])
    ],
    install_requires=["prelude >= 5.2.0"],
    cmdclass={
        'sdist': my_sdist,
        'install': my_install
    }
)
