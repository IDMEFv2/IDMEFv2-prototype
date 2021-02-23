# Copyright (C) 2004-2020 CS GROUP - France. All Rights Reserved.
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

import collections
import mimetypes
import os
import time
import datetime
import dateutil.parser
import stat
import string
import unicodedata

from prewikka import compat, utils
from prewikka.utils import json


_sentinel = object()

_ADDITIONAL_MIME_TYPES = [("application/vnd.oasis.opendocument.formula-template", ".otf"),
                          ("application/vnd.ms-fontobject", ".eot"),
                          ("image/vnd.microsoft.icon", ".ico"),
                          ("application/font-woff", ".woff"),
                          ("application/font-sfnt", ".ttf"),
                          ("application/json", ".map"),
                          ("font/woff2", ".woff2")]


for mtype, extension in _ADDITIONAL_MIME_TYPES:
    mimetypes.add_type(mtype, extension)


class PrewikkaResponse(object):
    """
        HTML response

        Use this class to render HTML in your view.

        :param data: Data of the response
        :param int code: HTTP response code
        :param str status_text: HTTP response status text

        If the type of data is a dict, it will be cast in a JSON string
    """

    def __init__(self, data=None, headers=_sentinel, code=None, status_text=None):
        self.data = data
        self.code = code
        self.status_text = status_text
        self.ext_content = {}

        if headers is not _sentinel:
            self.headers = headers
        else:
            self.headers = collections.OrderedDict(
                (
                    ("Content-Type", "text/html"),
                    ("Last-Modified", time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())),
                    ("Expires", "Fri, 01 Jan 1999 00:00:00 GMT"),
                    ("Cache-control", "no-store, no-cache, must-revalidate"),
                    ("Cache-control", "post-check=0, pre-check=0"),
                    ("Pragma", "no-cache"),
                )
            )

    def add_ext_content(self, key, value):
        """Add an extra content to the response (add in XHR request)."""

        self.ext_content[key] = value
        return self

    def add_html_content(self, elem, target=None):
        self.ext_content.setdefault("html_content", []).append({"target": target, "html": elem})
        return self

    def add_notification(self, message, classname="success", name=None, icon=None, duration=None):
        """Add notification to the return value."""

        self.ext_content.setdefault("notifications", []).append({
            "message": message,
            "classname": classname,
            "name": name,
            "icon": icon,
            "duration": duration
        })

        return self

    def content(self):
        if self.data is None:
            if not self.ext_content:
                return None

            self.data = {}

        if isinstance(self.data, compat.STRING_TYPES):
            return self.data

        self.headers["Content-Type"] = "application/json"
        if isinstance(self.data, dict):
            self.data["_extensions"] = self.ext_content

        return json.dumps(self.data)

    def _encode_response(self, res):
        return res.encode(env.config.general.get("encoding", "utf8"), "xmlcharrefreplace")

    def write(self, request):
        content = self.content()
        if content is None and self.code is None:
            self.code = 204

        request.send_headers(self.headers.items(), self.code or 200, self.status_text)
        if content is not None:
            request.write(self._encode_response(content))


class PrewikkaDownloadResponse(PrewikkaResponse):
    """
        File Download Response

        Use this class for download response (pdf, csv, ...).

        :param str data: The inner content of the file, or a file object
        :param str filename: Name for the file to be downloaded
        :param str type: Type of the file as mime type (will try to guess if None)
        :param int size: Size of the data (will be computed automatically if None)
        :param bool inline: Whether to display the downloaded file inline
    """
    @staticmethod
    def _filename_to_ascii(filename):
        filename = unicodedata.normalize('NFKC', filename)
        return ''.join((i if i in string.printable else '-' for i in filename))

    def __init__(self, data, filename=None, type=None, size=None, inline=False):
        PrewikkaResponse.__init__(self, data)

        if filename and not type:
            type = mimetypes.guess_type(filename)[0]

        if not type:
            type = "application/octet-stream"

        disposition = "inline" if inline else "attachment"
        if filename:
            # As specified in RFC 6266
            disposition += "; filename=\"%s\"; filename*=utf-8''%s" % (
                self._filename_to_ascii(filename),
                utils.url.quote(filename.encode("utf8"))
            )

        self._is_file = not(isinstance(self.data, text_type))
        if not size:
            if self._is_file:
                size = os.fstat(self.data.fileno()).st_size
            else:
                size = len(data)

        self.headers.update((
            ("Content-Type", type),
            ("Content-Length", str(size)),
            ("Content-Disposition", disposition),
            ("Pragma", "public"),
            ("Cache-Control", "max-age=0")
        ))

    def write(self, request):
        request.send_headers(self.headers.items(), self.code or 200, self.status_text)

        if not self._is_file:
            request.write(self.data)
        else:
            for i in iter(lambda: self.data.read(8192), b''):
                request.write(i)


class PrewikkaFileResponse(PrewikkaResponse):
    """
        Static File response
    """
    def __init__(self, path):
        PrewikkaResponse.__init__(self)
        self._path = path

        fst = os.stat(path)
        if not stat.S_ISREG(fst.st_mode):
            raise Exception("Attempt to send an invalid file")

        content_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
        mtime = datetime.datetime.utcfromtimestamp(fst.st_mtime).replace(tzinfo=utils.timeutil.tzutc())

        ims = env.request.web.headers.get("if-modified-since")
        if ims is not None:
            ims = dateutil.parser.parse(ims.split(";")[0])  # Edge includes the length in this header
            if mtime <= ims:
                self.code = 304

        self.headers = collections.OrderedDict((('Content-Type', content_type),))

        if self.code != 304:
            self.headers["Content-Length"] = str(fst.st_size)
            self.headers["Expires"] = (mtime + datetime.timedelta(days=30)).strftime("%a, %d %b %Y %H:%M:%S GMT")
            self.headers["Last-Modified"] = mtime.strftime("%a, %d %b %Y %H:%M:%S GMT")

    def write(self, request):
        request.send_headers(self.headers.items(), self.code or 200, self.status_text)
        if self.code == 304:
            return

        with open(self._path, 'rb') as fd:
            for i in iter(lambda: fd.read(8192), b''):
                request.write(i)


class PrewikkaRedirectResponse(PrewikkaResponse):
    """
        Redirect response
    """
    def __init__(self, location, code=302, status_text=None):
        PrewikkaResponse.__init__(self, code=code, status_text=status_text)
        self.headers = collections.OrderedDict((('Location', location),))
