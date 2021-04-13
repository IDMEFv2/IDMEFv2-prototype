# Copyright (C) 2004-2021 CS GROUP - France. All Rights Reserved.
# Author: Nicolas Delon <nicolas.delon@prelude-ids.com>
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
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

from __future__ import absolute_import, division, print_function

import abc
import cgi
import sys

from prewikka import error

if sys.version_info >= (3, 0):
    from http import cookies
else:
    import Cookie as cookies


class BufferedWriter(object):
    def __init__(self, wcb, buffersize=8192):
        self._wcb = wcb
        self._dlist = []
        self._len = 0
        self._buffersize = buffersize

    def flush(self):
        self._wcb(b''.join(self._dlist))
        self._dlist = []
        self._len = 0

    def write(self, data):
        self._dlist.append(data)
        self._len += len(data)

        if self._len >= self._buffersize:
            self.flush()


class Request(object):
    def __init__(self, path):
        self.path = path
        self.is_xhr = False
        self.is_stream = False
        self.body = None
        self.arguments = {}
        self._buffer = None
        self._output_cookie = None

        self.path_elements = path.strip('/').split("/")

        cookie = cookies.SimpleCookie(self.get_cookie())
        self.input_cookie = dict(cookie.items())

    def _handle_multipart(self, **kwargs):
        arguments = []
        fs = cgi.FieldStorage(**kwargs)

        for key in fs.keys():
            value = fs[key]
            for i, f in enumerate(value if isinstance(value, list) else [value]):
                arguments.append((key, f if f.filename else f.value))

        return arguments

    def add_cookie(self, param, value, expires=None, path="/", httponly=False):
        if not self._output_cookie:
            self._output_cookie = cookies.SimpleCookie()

        if sys.version_info < (3, 0):
            param = param.encode("ascii")
            value = value.encode("utf8")

        self._output_cookie[param] = value

        if expires is not None:
            self._output_cookie[param]["expires"] = expires

        if path:
            self._output_cookie[param]["path"] = path

        if httponly:
            self._output_cookie[param]["httpOnly"] = httponly

    def delete_cookie(self, param):
        self.add_cookie(param, "deleted", 0)

    def send_stream(self, data, event=None, evid=None, retry=None, sync=False):
        if self._buffer is None:
            self.is_stream = True
            self._buffer = BufferedWriter(self.write)
            self.write = self._buffer.write

            self.send_headers([("Content-Type", "text/event-stream")])

            if retry:
                self._buffer.write(b"retry: %d\n" % retry)

        # Join is used in place of concatenation / formatting, because we
        # prefer performance over readability in this place
        if event:
            self._buffer.write(b"".join([b"event: ", event.encode("utf8"), b"\n"]))

        if data:
            self._buffer.write(b"".join([b"data: ", data.encode("utf8"), b"\n\n"]))

        if sync:
            self._buffer.flush()

    def send_response(self, response):
        """Send a PrewikkaResponse response."""

        if self.is_stream:
            if isinstance(response.data, error.PrewikkaError):
                self.send_stream(response.content(), event="error")

            return self._buffer.flush()

        try:
            response.write(self)

        except Exception as err:
            if self.headers_sent:
                raise  # No way we can do it again

            error.make(err).respond().write(self)

    @abc.abstractmethod
    def headers_sent(self):
        pass

    @abc.abstractmethod
    def send_headers(self, headers=[], code=200, status_text=None):
        pass

    @abc.abstractmethod
    def get_baseurl(self):
        pass

    @abc.abstractmethod
    def get_raw_uri(self, include_qs=False):
        pass

    @abc.abstractmethod
    def get_remote_addr(self):
        pass

    @abc.abstractmethod
    def get_remote_port(self):
        pass

    @abc.abstractmethod
    def get_cookie(self):
        pass

    @abc.abstractmethod
    def write(self, data):
        pass
