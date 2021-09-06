# Copyright (C) 2018-2021 CS GROUP - France. All Rights Reserved.
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

"""
Test for `prewikka.hookmanager`.
"""

import pytest

from prewikka import hookmanager


def test_hookmanager_register():
    """
    Test `prewikka.hookmanager.HookManager.register()` method.
    """
    hook = 'hook_1'

    assert hook not in hookmanager.hookmgr

    hookmanager.register(hook, lambda x: 42)

    assert hook in hookmanager.hookmgr


def test_hookmanager_trigger():
    """
    Test `prewikka.hookmanager.HookManager.trigger()` method.
    """
    # Test method return value
    hook = 'hook_2'
    hookmanager.register(hook, lambda x: x + '42')

    assert list(hookmanager.trigger(hook, 'bar')) == ['bar42']

    with pytest.raises(TypeError):
        list(hookmanager.trigger(hook, 'foo', 'bar'))

    with pytest.raises(TypeError):
        list(hookmanager.trigger(hook, 'bar', type=int))

    # Test exception handling
    hook = 'hook_3'
    hookmanager.register(hook, lambda x: 1/x)

    with pytest.raises(ZeroDivisionError):
        list(hookmanager.trigger(hook, 0))

    assert list(hookmanager.trigger(hook, 0, _except=lambda e: None)) == []

    # Test constant value
    hook = 'hook_4'
    hookmanager.register(hook, 42)

    assert list(hookmanager.trigger(hook, type=int)) == [42]

    # Test return ordering
    hook = 'hook_5'
    hookmanager.register(hook, 'a', _order=2)
    hookmanager.register(hook, 'b', _order=1)
    hookmanager.register(hook, 'r', _order=3)

    assert ''.join(hookmanager.trigger(hook)) == 'bar'


def test_hookmanager_unregister():
    """
    Test `prewikka.hookmanager.HookManager.unregister()` method.
    """
    hook = 'hook_6'

    def method(x):
        return x

    hookmanager.register(hook, method)
    hookmanager.unregister(hook, method)

    assert list(hookmanager.trigger(hook, 'bar')) == []
