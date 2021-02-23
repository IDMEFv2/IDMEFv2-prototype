# Copyright (C) 2018-2020 CS GROUP - France. All Rights Reserved.
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
Tests for `prewikka.resolve`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from prewikka.resolve import AddressResolve, process, init


@pytest.mark.xfail(reason='Issue #2544')
def test_address_resolve_ipv4():
    """
    Test `prewikka.resolve.AddressResolve` for IPv4.

    NOTE: values could change if provider change IP/domain name.
    NOTE: Test skipped if Twisted is not installed.
    """
    # Skip test if Twisted is not installed
    pytest.importorskip('twisted')

    init()

    fail_ipv4 = '127.0.13.37'
    success_ipv4 = '208.67.222.222'
    success_domain_ipv4 = 'resolver1.opendns.com'

    res = AddressResolve(fail_ipv4)

    assert str(res) == fail_ipv4
    assert not res.resolve_succeed()

    res = AddressResolve(success_ipv4)

    assert str(res) == success_domain_ipv4
    assert str(len(res)) != 0  # exact value could change function of server used, we check if no null only
    assert res.resolve_succeed()

    # invalid IP

    with pytest.raises(TypeError):
        AddressResolve(42)


@pytest.mark.xfail(reason='Issue #2544')
def test_address_resolve_ipv6():
    """
    Test `prewikka.resolve.AddressResolve` for IPv6.

    NOTE: values could change if provider change IP/domain name.
    NOTE: Test skipped if Twisted is not installed.
    """
    # Skip test if Twisted is not installed
    pytest.importorskip('twisted')

    init()

    success_ipv6 = '2620:0:ccc::2'
    success_ipv6_full = '2620:0000:0ccc:0000:0000:0000:0000:0002'
    success_domain_ipv6 = 'resolver1.ipv6-sandbox.opendns.com'

    assert str(AddressResolve(success_ipv6)) == success_domain_ipv6
    assert str(AddressResolve(success_ipv6_full)) == success_domain_ipv6


def test_address_resolve():
    """
    Test `prewikka.resolve.AddressResolve` class.

    Test methods of the class AddressResolve (resolve() method is tested in dedicated tests).
    NOTE: Test skipped if Twisted is not installed.
    """
    # Skip test if Twisted is not installed
    pytest.importorskip('twisted')

    init()

    process()

    # change env.dns_max_delay
    backup_env_max_delay = env.dns_max_delay

    env.dns_max_delay = -1

    assert not init()

    # clean
    env.dns_max_delay = backup_env_max_delay
