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
Tests for `prewikka.auth.auth`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from prewikka.auth.auth import Auth, AuthError
from prewikka.config import ConfigSection
from prewikka.error import NotImplementedError
from prewikka.session.session import Session
from prewikka.usergroup import Group, User


def test_autherror():
    """
    Test `prewikka.auth.auth.AuthError` error.
    """
    session = Session(ConfigSection(None))
    error = AuthError(session)

    with pytest.raises(AuthError):
        raise error


def test_auth():
    """
    Test `prewikka.auth.auth.Auth` class.
    """
    auth = Auth(ConfigSection(None))
    user = User('john')
    group = Group('grp')

    # _AuthUser()
    assert not auth.can_create_user()
    assert not auth.can_delete_user()
    assert not auth.can_set_password()
    assert not auth.can_manage_permissions()
    assert not auth.get_user_list()
    assert not auth.get_user_list('foo')

    assert not auth.get_user_by_id(user.id)
    auth.create_user(user)
    assert auth.get_user_by_id(user.id)
    auth.delete_user(user)
    assert not auth.get_user_by_id(user.id)

    with pytest.raises(NotImplementedError):
        auth.has_user(user)

    assert not auth.get_user_permissions(user)
    assert not auth.get_user_permissions(user, True)
    assert not auth.get_user_permissions_from_groups(user)

    with pytest.raises(NotImplementedError):
        auth.set_user_permissions(user, ['FAKE_PERM'])

    # _AuthGroup
    assert not auth.can_create_group()
    assert not auth.can_delete_group()
    assert not auth.can_manage_group_members()
    assert not auth.can_manage_group_permissions()
    assert not auth.get_group_list()
    assert not auth.get_group_list('foo')

    assert not auth.get_group_by_id(group.id)
    auth.create_group(group)
    assert auth.get_group_by_id(group.id)
    auth.delete_group(group)
    assert not auth.get_group_by_id(group.id)

    with pytest.raises(NotImplementedError):
        auth.set_group_permissions(group, ['FAKE_PERM'])

    assert not auth.get_group_permissions(group)

    with pytest.raises(NotImplementedError):
        auth.set_group_members(group, [user])

    assert not auth.get_group_members(group)

    with pytest.raises(NotImplementedError):
        auth.set_member_of(user, [group])

    assert not auth.get_member_of(user)

    with pytest.raises(NotImplementedError):
        auth.is_member_of(group, user)

    with pytest.raises(NotImplementedError):
        auth.has_group(group)
