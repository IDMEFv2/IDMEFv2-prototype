# Copyright (C) 2016-2021 CS GROUP - France. All Rights Reserved.
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

from __future__ import absolute_import, division, print_function, unicode_literals

import collections
import datetime
import json

from prewikka.compat import with_metaclass

_TYPES = {}


class _JSONMetaClass(type):
    def __new__(cls, clsname, bases, attrs):
        nclass = super(_JSONMetaClass, cls).__new__(cls, clsname, bases, attrs)

        _TYPES[nclass.__name__] = nclass

        return nclass


class _JSONObject(object):
    @classmethod
    def from_json(cls, data):
        return cls(**data)

    def __jsonobj__(self):
        return {"__prewikka_class__": (self.__class__.__name__, self.__json__())}


class JSONObject(with_metaclass(_JSONMetaClass, _JSONObject)):
    pass


class PrewikkaJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "__jsonobj__"):
            return obj.__jsonobj__()

        elif hasattr(obj, "__json__"):
            return obj.__json__()

        elif isinstance(obj, datetime.datetime):
            return text_type(obj)

        elif isinstance(obj, collections.Iterable):
            return list(obj)

        return json.JSONEncoder.default(self, obj)


# The following class has been adapted from simplejson
#
class PrewikkaHTMLJSONEncoder(PrewikkaJSONEncoder):
    """An encoder that produces JSON safe to embed in HTML.
    To embed JSON content in, say, a script tag on a web page, the
    characters &, < and > should be escaped. They cannot be escaped
    with the usual entities (e.g. &amp;) because they are not expanded
    within <script> tags.
    """

    def encode(self, o):
        # Override JSONEncoder.encode because it has hacks for
        # performance that make things more complicated.
        chunks = self.iterencode(o, True)
        if self.ensure_ascii:
            return ''.join(chunks)
        else:
            return u''.join(chunks)

    def iterencode(self, o, _one_shot=False):
        chunks = super(PrewikkaHTMLJSONEncoder, self).iterencode(o, _one_shot)
        for chunk in chunks:
            chunk = chunk.replace('&', '\\u0026')
            chunk = chunk.replace('<', '\\u003c')
            chunk = chunk.replace('>', '\\u003e')
            yield chunk


def _object_hook(obj):
    cls = obj.get("__prewikka_class__")
    if cls:
        return _TYPES[cls[0]].from_json(cls[1])

    return obj


def load(*args, **kwargs):
    return json.load(*args, object_hook=_object_hook, **kwargs)


def loads(*args, **kwargs):
    return json.loads(*args, object_hook=_object_hook, **kwargs)


def dump(*args, **kwargs):
    if "cls" not in kwargs:
        kwargs["cls"] = PrewikkaJSONEncoder

    return json.dump(*args, **kwargs)


def dumps(*args, **kwargs):
    if "cls" not in kwargs:
        kwargs["cls"] = PrewikkaJSONEncoder

    return json.dumps(*args, **kwargs)
