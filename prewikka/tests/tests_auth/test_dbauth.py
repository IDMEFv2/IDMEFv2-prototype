# Copyright (C) 2020-2021 CS GROUP - France. All Rights Reserved.
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
Tests for `prewikka.auth.dbauth`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from prewikka.auth.dbauth import DBAuth
from prewikka.config import ConfigSection
from prewikka.usergroup import Group, User


def test_dbauth():
    """
    Test `prewikka.auth.dbauth.DBAuth` class.
    """
    auth = DBAuth(ConfigSection(None))
    user = User('john')
    group = Group('grp')

    assert auth.can_create_user()
    assert auth.can_delete_user()
    assert auth.can_set_password()
    assert auth.can_manage_permissions()

    assert not auth.get_user_by_id(user.id)
    auth.create_user(user)
    assert auth.has_user(user)
    assert auth.get_user_by_id(user.id)
    assert user in auth.get_user_list()
    assert user in auth.get_user_list('jo')

    auth.set_user_permissions(user, ['FAKE_PERM1'])
    assert 'FAKE_PERM1' in auth.get_user_permissions(user)
    assert 'FAKE_PERM1' in auth.get_user_permissions(user, True)

    assert auth.can_create_group()
    assert auth.can_delete_group()
    assert auth.can_manage_group_members()
    assert auth.can_manage_group_permissions()

    assert not auth.get_group_by_id(group.id)
    auth.create_group(group)
    assert auth.has_group(group)
    assert auth.get_group_by_id(group.id)
    assert group in auth.get_group_list()
    assert group in auth.get_group_list('gr')

    auth.set_group_members(group, [user])
    assert user in auth.get_group_members(group)

    auth.set_member_of(user, [group])
    assert group in auth.get_member_of(user)

    assert auth.is_member_of(group, user)

    auth.set_group_permissions(group, ['FAKE_PERM2'])
    assert 'FAKE_PERM2' in auth.get_group_permissions(group)
    assert 'FAKE_PERM2' in auth.get_user_permissions(user)
    assert 'FAKE_PERM2' not in auth.get_user_permissions(user, True)
    assert 'FAKE_PERM2' in auth.get_user_permissions_from_groups(user)

    auth.delete_user(user)
    assert not auth.get_user_by_id(user.id)

    auth.delete_group(group)
    assert not auth.get_group_by_id(group.id)
