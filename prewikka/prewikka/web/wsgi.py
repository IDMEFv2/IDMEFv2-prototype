# Copyright (C) 2015-2021 CS GROUP - France. All Rights Reserved.
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

import werkzeug.wsgi
import wsgiref.headers
import wsgiref.util

from prewikka import main, utils
from prewikka.web import request

from prewikka.compat.jquery_unparam import jquery_unparam


defined_status = {
    200: 'Ok',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    500: 'Internal Server Error',
}


class WSGIRequest(request.Request):
    def __init__(self, environ, start_response):
        self._write = None
        self._environ = environ
        self._headers = None
        self._start_response = start_response
        self.method = environ['REQUEST_METHOD']

        request.Request.__init__(self, self._wsgi_get_unicode("PATH_INFO"))
        self.arguments = jquery_unparam(self._wsgi_get_str("QUERY_STRING"))

        if self.method in ('POST', 'PUT', 'PATCH'):
            multipart = environ.get('CONTENT_TYPE', "").startswith('multipart/form-data')
            if multipart:
                arg = self._handle_multipart(fp=environ['wsgi.input'], environ=environ)
            else:
                arg = environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))
                self.body = arg = arg.decode("utf8")

            self.arguments.update(jquery_unparam(arg, multipart=multipart))

        if self._environ.get("HTTP_X_REQUESTED_WITH", "") == "XMLHttpRequest":
            self.is_xhr = True

        # Force request type when client wait explicitly for "text/event-stream"
        if self._environ.get("HTTP_ACCEPT", "text/html") == "text/event-stream":
            self.is_stream = True

    def _wsgi_get_bytes(self, key, default=None):
        value = self._environ.get(key, default)

        # Under Python 3, non-ASCII values in the WSGI environ are arbitrarily
        # decoded with ISO-8859-1. This is wrong for Prewikka where UTF-8 is the
        # default. Re-encode to recover the original bytestring.
        if value is not None:
            return value.encode("ISO-8859-1")

    def _wsgi_get_unicode(self, key, default=None):
        value = self._wsgi_get_bytes(key, default)
        if value is not None:
            return value.decode("utf8")

    def _wsgi_get_str(self, key, default=None):
        value = self._wsgi_get_bytes(key, default)
        if value is not None:
            return value.decode("utf8")

    def get_target_origin(self):
        return "%s://%s" % (self._environ.get("wsgi.url_scheme"), werkzeug.wsgi.get_host(self._environ))

    def get_origin(self):
        ret = self._wsgi_get_unicode("HTTP_ORIGIN")
        if ret:
            return ret

        ret = self._wsgi_get_unicode("HTTP_REFERER")
        if not ret:
            return None

        scheme, netloc, path, query, frag = utils.url.urlsplit(ret)
        return "%s://%s" % (scheme, netloc)

    def write(self, data):
        self._write(data)

    @property
    def headers_sent(self):
        return bool(self._write)

    def send_headers(self, headers=[], code=200, status_text=None):
        headers = list(headers) + [("X-responseURL", utils.iri2uri(self.get_uri()))]

        if self._output_cookie:
            headers += [("Set-Cookie", c.OutputString()) for c in self._output_cookie.values()]

        if not status_text:
            status_text = defined_status.get(code, "Unknown")

        self._write = self._start_response("%d %s" % (code, status_text.encode("ISO-8859-1")), headers)

    def get_cookie(self):
        return self._wsgi_get_str('HTTP_COOKIE', '')

    def get_remote_addr(self):
        return self._wsgi_get_unicode('REMOTE_ADDR')

    def get_remote_port(self):
        return int(self._environ.get('REMOTE_PORT', 0))

    def get_query_string(self):
        return self._wsgi_get_unicode('QUERY_STRING')

    def get_script_name(self):
        return self._wsgi_get_unicode("SCRIPT_NAME")

    def get_baseurl(self):
        return (env.config.general.reverse_path or self.get_script_name()) + "/"

    def get_uri(self):
        return self.get_script_name() + self.path

    def get_raw_uri(self, include_qs=False):
        return wsgiref.util.request_uri(self._environ, include_query=include_qs)

    @property
    def headers(self):
        if self._headers is not None:
            return self._headers

        self._headers = {}
        for key, value in self._environ.items():
            if key.find("HTTP_") == -1:
                continue

            self._headers[key[5:].replace("_", "-").lower()] = value

        return self._headers

    def add_cookie(self, param, value, expires=None, path="/", httponly=False):
        request.Request.add_cookie(self, param, value, expires, path, httponly)
        if self._environ.get("wsgi.url_scheme") == 'https':
            self._output_cookie[param]["Secure"] = True


def application(environ, start_response):
    core = main.Core.from_config(environ.get("PREWIKKA_CONFIG", None))
    core.process(WSGIRequest(environ, start_response))

    return []
