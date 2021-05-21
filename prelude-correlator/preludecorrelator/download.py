# Copyright (C) 2014-2021 CS GROUP - France. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
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

try:
    import urllib.request as urlreq
except:
    import urllib2 as urlreq

import os
import time

from preludecorrelator import error
from preludecorrelator.context import Timer


class DownloadCache:
    def _checkPermissions(self):
        dirname = os.path.dirname(self._filename)

        if not os.access(dirname, os.R_OK | os.W_OK | os.X_OK):
            raise error.UserError("DownloadCache directory '%s' does not exist or has wrong permissions" % dirname)

        if os.path.exists(self._filename) and not os.access(self._filename, os.R_OK | os.W_OK):
            raise error.UserError("DownloadCache file '%s' cannot be opened in read-write mode" % self._filename)

    def __init__(self, name, filename, reload, logger, bindata=False):
        self._name = name
        self._filename = filename
        self._reload = reload
        self.__data = None
        self.logger = logger
        self._bindata = bindata

        self._checkPermissions()

        age = self._doInit()
        if self._reload > 0:
            Timer(self._reload - age, self._download).start()

    def _doInit(self):
        age = False
        try:
            st = os.stat(self._filename)
            age = time.time() - st.st_mtime

            # If the data didn't expire, we're good to go
            if self._reload <= 0 or age < self._reload:
                self._load(age)
                return age

        except OSError:
            pass

        try:
            self._download()
        except Exception:
            # There was an error downloading newer data, use any older data that we have, even if it's expired
            # If we don't have any older data available, then this is an error, and there is no fallback.
            if not age:
                raise error.UserError("%s data couldn't be retrieved, and no previous data available" % self._name)
            self._load(age)

        return 0

    def _download(self, timer=None):
        status = "Downloading" if not timer else "Updating"
        self.logger.info("%s %s report, this might take some time...", status, self._name)

        try:
            unparsed_data = self.download()
            self.__data = self.parse(unparsed_data)

            fd = open(self._filename, "wb" if self._bindata else "w")
            self.write(fd, unparsed_data)
            fd.close()

            self.logger.info("%s %s report done.", status, self._name)
        except Exception as e:
            self.logger.error("error %s %s report : %s", status.lower(), self._name, e)
            if not timer:
                raise

        if timer:
            timer.setExpire(self._reload)
            timer.reset()

    def _load(self, age):
        self.__data = self.parse(self.read(open(self._filename, "rb" if self._bindata else "r")))
        self.logger.info("Loaded %s data from a previous run (age=%.2f hours)", self._name, age / 60 / 60)

    def download(self):
        pass

    def parse(self, data):
        return data

    def get(self):
        return self.__data


class HTTPDownloadCache(DownloadCache):
    def __init__(self, name, filename, uri, timeout, reload, logger, bindata=False):
        self.__uri = uri
        self.__timeout = timeout
        DownloadCache.__init__(self, name, filename, reload, logger, bindata)

    def read(self, fd):
        return fd.read()

    def write(self, fd, data):
        fd.write(data)

    def download(self, headers=None):
        if headers is None:
            headers = {'User-Agent': "Prelude-Correlator"}

        con = urlreq.urlopen(urlreq.Request(self.__uri, headers=headers), timeout=self.__timeout)
        data = con.read()

        if not self._bindata:
            _mime_type, _sep, encoding = con.headers['content-type'].partition('charset=')
            data = data.decode(encoding or 'ascii')

        return data
