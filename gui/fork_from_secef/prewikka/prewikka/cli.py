# Copyright (C) 2019-2021 CS GROUP - France. All Rights Reserved.
# Author: Antoine Luong <antoine.luong@c-s.fr>
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

from prewikka import registrar, usergroup


class CLIManager(object):
    def __init__(self):
        self._commands = {}

    def _register(self, command, category, method, permissions, help, **options):
        d = self._commands.setdefault(command, {})
        if category not in d:
            # Avoid replacing methods by the ones from children classes
            d[category] = (method, permissions, help, options)

    def register(self, command, category, method=None, permissions=[], help=None, **options):
        usergroup.ALL_PERMISSIONS.declare(permissions)

        if method:
            self._register(command, category, method, permissions, help, **options)
        else:
            return registrar.DelayedRegistrar.make_decorator("cli", self._register, command, category, permissions=permissions, help=help, **options)

    def unregister(self, command=None, category=None):
        if command and category:
            self._commands[command].pop(category)
        elif command:
            self._commands.pop(command)
        else:
            self._commands = {}

    def get(self, command):
        return self._commands.get(command, {})


cli = CLIManager()
get = cli.get
register = cli.register
unregister = cli.unregister
