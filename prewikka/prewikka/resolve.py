# Copyright (C) 2008-2020 CS GROUP - France. All Rights Reserved.
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

import socket
import time

from prewikka import compat

resolver = None
import_fail = None

try:
    from twisted.internet import reactor
    from twisted.names import client, dns, cache, resolve
except Exception as err:
    import_fail = err

try:
    from threading import Lock
except ImportError:
    from dummy_threading import Lock


class DNSResolver(object):
    def __init__(self):
        self._query = 0
        self._lock = Lock()

        self._cache = cache.CacheResolver()
        rlist = [self._cache, client.Resolver('/etc/resolv.conf')]
        self._resolve = resolve.ResolverChain(rlist)

    def _error_cb(self, failure):
        self._query -= 1

        if failure.check(dns.DomainError, dns.AuthoritativeDomainError):
            return

    def _resolve_cb(self, tpl, ptr, resolve_cb):
        ans, auth, add = tpl

        self._query -= 1
        name = str(ans[0].payload.name)

        resolve_cb(name)

        q = dns.Query(name, ans[0].type, ans[0].cls)
        self._cache.cacheResult(q, (ans, auth, add))

    def _ip_reverse(self, addr):
        try:
            parts = list(socket.inet_pton(socket.AF_INET6, addr).encode('hex_codec'))
            origin = ".ip6.arpa"
        except:
            parts = ["%d" % ord(byte) for byte in socket.inet_aton(addr)]
            origin = ".in-addr.arpa"

        parts.reverse()
        return '.'.join(parts) + origin

    def process(self, timeout=0):
        end = now = time.time()
        final = now + timeout

        while True:
            self._lock.acquire()

            if self._query == 0:
                self._lock.release()
                break

            reactor.runUntilCurrent()
            reactor.doIteration(timeout)

            self._lock.release()

            end = time.time()
            if end >= final:
                break

        # print "max=%f elapsed:%f" % (timeout, end-now)

    def do_query(self, addr, resolve_cb):
        self._lock.acquire()

        self._query += 1
        self._resolve.lookupPointer(addr).addCallback(self._resolve_cb, addr, resolve_cb).addErrback(self._error_cb)

        self._lock.release()
        self.process()

    def resolve(self, addr, resolve_cb):
        try:
            addr = self._ip_reverse(addr)
        except:
            return

        self.do_query(addr, resolve_cb)
        self.process()


class AddressResolve(object):
    def _resolve_cb(self, value):
        if self._formater:
            value = self._formater(self._addr, value)

        self._name = value

    def __init__(self, addr, format=None):
        global resolver

        if not isinstance(addr, compat.STRING_TYPES):
            raise TypeError('AddressResolve expects a valid IP address to resolve')

        self._addr = addr
        self._name = None
        self._formater = format

        if resolver:
            resolver.resolve(addr, self._resolve_cb)

    def __len__(self):
        return len(str(self))

    def resolve_succeed(self):
        if self._name:
            return True
        else:
            return False

    def __str__(self):
        if resolver:
            resolver.process()

        return self._name or self._addr


def process(timeout=0):
    global resolver

    if resolver:
        resolver.process(timeout)


def init():
    global resolver

    if env.dns_max_delay == -1:
        return

    if import_fail:
        env.log.warning(_("Asynchronous DNS resolution disabled: twisted.names and twisted.internet required: %s") % import_fail)
        return

    resolver = DNSResolver()
