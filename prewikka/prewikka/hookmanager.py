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

import operator
from prewikka import registrar

_sentinel = object()


class HookManager(object):
    def __init__(self):
        self._hooks = {}

    def __contains__(self, hook):
        return hook in self._hooks

    def unregister(self, hook=None, method=None, exclude=[]):
        if hook and method:
            self._hooks[hook] = [(order, func) for order, func in self._hooks[hook] if func != method]
        elif hook:
            self._hooks[hook] = []
        else:
            for i in set(self._hooks) - set(exclude):
                self._hooks[i] = []

    def register(self, hook, _regfunc=_sentinel, _order=2**16):
        if _regfunc is not _sentinel:
            self._hooks.setdefault(hook, []).append((_order, _regfunc))
        else:
            return registrar.DelayedRegistrar.make_decorator("hook", self.register, hook, _order=_order)

    def trigger(self, hook, *args, **kwargs):
        wtype = kwargs.pop("type", None)
        _except = kwargs.pop("_except", None)

        for order, cb in sorted(self._hooks.setdefault(hook, []), key=operator.itemgetter(0)):
            if not callable(cb):
                result = cb
            else:
                try:
                    result = cb(*args, **kwargs)
                except Exception as e:
                    if _except:
                        _except(e)
                        continue
                    else:
                        raise

            if result and wtype and not isinstance(result, wtype):
                raise TypeError("Hook '%s' expect return type of '%s' but got '%s'" % (hook, wtype, type(result)))

            yield result


hookmgr = HookManager()
trigger = hookmgr.trigger
register = hookmgr.register
unregister = hookmgr.unregister
