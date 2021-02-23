# Copyright (C) 2016-2020 CS GROUP - France. All Rights Reserved.
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

from prewikka import csrf, resource


POPOVER_HTML = '<div class="popover popover-menu" role="tooltip"><div class="arrow"></div><div class="popover-content"></div></div>'


def csrftoken():
    return resource.HTMLSource('<input type="hidden" name="%s" value="%s" />' % (csrf.CSRF_POST_KEY, csrf.get_token(env.request.web)))


def selected(condition):
    return "selected" if condition else ""


def checked(condition):
    return "checked" if condition else ""


def disabled(condition):
    return "disabled" if condition else ""


class HTMLProgressBar(resource.HTMLNode):
    def __init__(self, color, progress, text):
        txtspan = resource.HTMLNode('span', text)

        pgdiv = resource.HTMLNode('div', txtspan, **{
            'class': "progress-bar progress-bar-%s progress-bar-striped" % color,
            'aria-valuenow': progress,
            'aria-valuemin': 0,
            'aria-valuemax': 100,
            'style': "width: %s%%" % progress
        })

        resource.HTMLNode.__init__(self, 'div', pgdiv, _class='progress')

    def __jsonobj__(self):
        return {"__prewikka_class__": ("HTMLNode", self.__json__())}
