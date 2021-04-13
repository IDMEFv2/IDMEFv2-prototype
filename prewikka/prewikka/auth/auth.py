# Copyright (C) 2004-2021 CS GROUP - France. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
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

from __future__ import absolute_import, division, print_function, unicode_literals

import abc

from prewikka import database, log, pluginmanager, usergroup
from prewikka.error import NotImplementedError, PrewikkaUserError


class AuthError(PrewikkaUserError):
    def __init__(self, session, message=N_("Authentication failed"), log_priority=log.ERROR, log_user=None):
        PrewikkaUserError.__init__(self, None, message, log_priority=log_priority, log_user=log_user, template=session.template)


class _AuthUser(database.DatabaseHelper):
    def can_create_user(self):
        return False

    def can_delete_user(self):
        return False

    def can_set_password(self):
        return self.__class__.set_password != _AuthUser.set_password

    def can_manage_permissions(self):
        return self.__class__.set_user_permissions != _AuthUser.set_user_permissions

    def create_user(self, user):
        self.query("INSERT INTO Prewikka_User (name, userid) VALUES (%s, %s)", user.name, user.id)
        env.log.info("Created user \"%s\"" % user)

    def delete_user(self, user):
        name = user.name
        self.query("DELETE FROM Prewikka_User WHERE userid = %s", user.id)
        env.log.info("Deleted user \"%s\"" % name)

    @abc.abstractmethod
    def get_user_list(self, search=None):
        return []

    def get_user_by_id(self, id_):
        ret = self.query("SELECT name, userid FROM Prewikka_User WHERE userid = %s", id_)
        return usergroup.User(*ret[0]) if ret else None

    @abc.abstractmethod
    def has_user(self, user):
        raise NotImplementedError

    @abc.abstractmethod
    def get_user_permissions(self, user, ignore_group=False):
        return []

    @abc.abstractmethod
    def get_user_permissions_from_groups(self, user):
        return []

    @abc.abstractmethod
    def set_user_permissions(self, user, permissions):
        raise NotImplementedError

    @abc.abstractmethod
    def set_password(self, user, password):
        raise NotImplementedError


class _AuthGroup(object):
    def can_handle_groups(self):
        return False

    def can_create_group(self):
        return False

    def can_delete_group(self):
        return False

    def can_manage_group_members(self):
        return self.__class__.set_group_members != _AuthGroup.set_group_members

    def can_manage_group_permissions(self):
        return self.__class__.set_group_permissions != _AuthGroup.set_group_permissions

    def get_group_list(self, search=None):
        return []

    def get_group_by_id(self, id_):
        ret = self.query("SELECT name, groupid FROM Prewikka_Group WHERE groupid = %s", id_)
        return usergroup.Group(*ret[0]) if ret else None

    def create_group(self, group):
        self.query("INSERT INTO Prewikka_Group (name, groupid) VALUES (%s, %s)", group.name, group.id)
        env.log.info("Created group \"%s\"" % group)

    def delete_group(self, group):
        name = group.name
        self.query("DELETE FROM Prewikka_Group WHERE groupid = %s", group.id)
        env.log.info("Deleted group \"%s\"" % name)

    def set_group_permissions(self, group, permissions):
        raise NotImplementedError

    def get_group_permissions(self, group):
        return []

    def set_group_members(self, group, users):
        raise NotImplementedError

    def get_group_members(self, group):
        return []

    def set_member_of(self, user, groups):
        raise NotImplementedError

    def get_member_of(self, user):
        return []

    def is_member_of(self, group, user):
        raise NotImplementedError

    def has_group(self, group):
        raise NotImplementedError


class Auth(pluginmanager.PluginBase, _AuthUser, _AuthGroup):
    __metaclass__ = abc.ABCMeta
    plugin_mandatory = True

    def __init__(self, config):
        pluginmanager.PluginBase.__init__(self)
        _AuthUser.__init__(self)
        _AuthGroup.__init__(self)

    def init(self, config):
        pass

    def authenticate(self, login, password="", no_password_check=False):
        raise NotImplementedError

    def get_default_session(self):
        raise NotImplementedError
