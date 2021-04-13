# -*- coding: utf-8 -*-
# Copyright (C) 2016-2021 CS GROUP - France. All Rights Reserved.
# Author: Antoine Luong <antoine.luong@c-s.fr>
#
# Inspired by the tw2.core package of ToscaWidgets2 which is Copyright (c)
# 2006-2013, Paul Johnston, Christopher Perkins, Alberto Valverde González
# and contributors.
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

import functools
from prewikka.utils import html, json


class Link(html.Markup):
    """
    A link to an external resource, like a JS or CSS file.
    """
    pass


class CSSLink(Link):
    """
    A link to an external CSS file.
    """
    def __new__(cls, link):
        return Link.__new__(cls, html.Markup('<link rel="stylesheet" type="text/css" href="%s" />') % link)


class JSLink(Link):
    """
    A link to an external JS file.
    """
    def __new__(cls, link):
        return Link.__new__(cls, html.Markup('<script type="text/javascript" src="%s"></script>') % link)


class HTMLSource(html.Markup):
    pass


class CSSSource(HTMLSource):
    """
    An inlined chunk of CSS source code.
    """
    def __new__(cls, src):
        return HTMLSource.__new__(cls, html.Markup('<style type="text/css">%s</style>' % src))


class JSSource(HTMLSource):
    """
    An inlined chunk of JS source code.
    """
    def __new__(cls, src):
        return HTMLSource.__new__(cls, html.Markup('<script type="text/javascript">%s</script>' % src))


@functools.total_ordering
class HTMLNode(json.JSONObject):
    _HTML5_VOID_TAGS = frozenset(["area", "base", "br", "col", "embed", "hr", "img", "input", "keygen", "link", "meta", "param", "source", "track", "wbr"])

    def __init__(self, tag, *childs, **attrs):
        self.tag = tag
        self.childs = childs

        icon = attrs.pop("_icon", None)
        if icon:
            self.childs = (HTMLNode("i", _class="fa %s" % icon), " ") + self.childs

        self._sortkey = attrs.pop("_sortkey", "")
        self._extra = attrs.pop("_extra", None)

        tmp = attrs.pop("_class", None)
        if tmp:
            attrs["class"] = tmp

        self.attrs = attrs

    def to_string(self, _class=""):
        attr_s = HTMLSource()
        for k, v in self.attrs.items():
            if k == "class":
                _class += " %s" % v
                continue

            if v is True:
                attr_s += HTMLSource(" %s" % k)
            elif v not in (False, None):
                attr_s += HTMLSource(" %s=\"%s\"") % (k, v)

        if _class:
            attr_s = HTMLSource(" class=\"%s\"") % (_class) + attr_s

        childs = HTMLSource()
        for x in self.childs:
            childs += text_type(x)

        if not self.tag:
            return HTMLSource("%s" % childs)

        if self.tag in self._HTML5_VOID_TAGS:
            if self.childs:
                raise Exception("HTMLNode with void tag '%s' contains children" % self.tag)

            return HTMLSource("<%s%s />" % (self.tag, attr_s))

        return HTMLSource("<%s%s>%s</%s>" % (self.tag, attr_s, childs, self.tag))

    def join(self, l):
        children = []

        for i, elem in enumerate(l):
            if i > 0:
                children.append(self)

            children.append(elem)

        return HTMLNode(None, *children)

    def format(self, *args, **kwargs):
        return self.to_string().format(*args, **kwargs)

    def __json__(self):
        return {"tag": self.tag, "childs": self.childs, "attrs": self.attrs, "extra": self._extra}

    def __html__(self):
        return self.to_string()

    def __str__(self):
        return self.to_string()

    def __mod__(self, other):
        return self.to_string() % other

    def __add__(self, other):
        children = []

        for obj in (self, other):
            if obj.tag:
                children.append(obj)
            else:
                children += obj.childs

        return HTMLNode(None, *children)

    def __eq__(self, other):
        return (self._sortkey, self.childs) == (other._sortkey, other.childs)

    def __lt__(self, other):
        return (self._sortkey, self.childs) < (other._sortkey, other.childs)
