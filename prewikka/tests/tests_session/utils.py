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
Utils for `prewikka.session` tests.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import binascii
import os
import struct
import time

from prewikka.session.anonymous.anonymous import AnonymousSession
from prewikka.session.session import SessionDatabase


class FakeAuthBackend(AnonymousSession):
    """
    Fake Auth backend for test suite.
    """
    def has_user(self, other):
        return False

    def get_user_permissions_from_groups(self, user):
        pass

    def set_user_permissions(self, user, permissions):
        pass

    def get_default_session(self):
        pass

    def get_group_by_id(self, id_):
        pass

    def has_group(self, group):
        pass

    def is_member_of(self, group, user):
        pass

    def set_group_members(self, group, users):
        pass

    def set_group_permissions(self, group, permissions):
        pass

    def set_member_of(self, user, groups):
        pass


def create_session(user, time_=None, session_id=None):
    """
    Create a session and save it in database.

    :param prewikka.usergroup.User user: User for the session creation.
    :param float time_: optional time.time() object.
    :param str session_id: optional session ID
    :return: the ID of the session.
    :rtype: str
    """
    if not time_:
        time_ = time.time()

    if not session_id:
        session_id = binascii.hexlify(os.urandom(16) + struct.pack(b'>d', time_))

    session_database = SessionDatabase()
    session_database.create_session(session_id, user, int(time_))

    return session_id


def clean_sessions():
    """
    Delete all sessions in `prewikka_session` table.

    :return: None
    :rtype: None
    """
    env.db.query('DELETE FROM Prewikka_Session;')
