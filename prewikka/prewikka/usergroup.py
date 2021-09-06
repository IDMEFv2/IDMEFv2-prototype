# Copyright (C) 2004-2021 CS GROUP - France. All Rights Reserved.
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

import abc
import copy
import hashlib

from prewikka import error, hookmanager, localization, log, utils
from prewikka.utils import cache, json

ADMIN_LOGIN = "admin"
_NAMEID_TBL = {}


class UnknownNameIDError(KeyError):
    pass


class PermissionDeniedError(error.PrewikkaUserError):
    def __init__(self, permissions, view=None):
        if isinstance(permissions, str):
            permissions = [permissions]

        if view and permissions:
            msg = N_("Access to view '%(view)s' forbidden. Required permissions: %(permissions)s",
                     {"view": view, "permissions": ", ".join(permissions)})

        elif view:
            msg = N_("Access to view '%s' forbidden", view)

        else:
            msg = N_("Required permissions: %s", ", ".join(permissions))

        error.PrewikkaUserError.__init__(self, N_("Permission Denied"), msg, log_priority=log.WARNING)


def permissions_required(permissions):
    ALL_PERMISSIONS.declare(permissions)

    def has_permissions(func):
        def wrapper(*args, **kwargs):
            if env.request.user:
                env.request.user.check(permissions)
            return func(*args, **kwargs)
        return wrapper
    return has_permissions


class Permissions(set):
    """ List of all the permissions available """

    def declare(self, permission):
        """Add the permission to the set if it is not already declared"""
        if isinstance(permission, str):
            self.add(permission)
        else:
            self.update(permission)


ALL_PERMISSIONS = Permissions()
ACTIVE_PERMISSIONS = Permissions()


class NameID(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name=None, nameid=None):
        assert(name or nameid)

        self._id = nameid
        self._name = name

    @property
    def id(self):
        if self._id is None:
            self._id = self._name2id(self._name)

        return self._id

    @property
    def name(self):
        if self._name is None:
            self._name = self._id2name(self._id)

        return self._name

    @abc.abstractmethod
    def _id2name(self, id):
        pass

    def _name2id(self, name):
        md5 = _NAMEID_TBL.get(name)
        if md5:
            return md5

        md5 = _NAMEID_TBL[name] = hashlib.md5(name.encode("utf8")).hexdigest()
        return md5

    def __eq__(self, other):
        if not other:
            return False

        return self.id == other.id

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return int(self.id, 16)

    def __str__(self):
        return self.name

    def __repr__(self):
        try:
            name = self.name
        except UnknownNameIDError:
            return "%s(id=%s)" % (self.__class__.__name__, self.id)

        return "%s(name=%s, id=%s)" % (self.__class__.__name__, name, self.id)


class Group(NameID):
    def __init__(self, name=None, groupid=None):
        NameID.__init__(self, name, groupid)

    def _id2name(self, id):
        group = env.auth.get_group_by_id(id)
        if not group:
            raise UnknownNameIDError(id)

        return group.name

    def create(self):
        env.auth.create_group(self)
        list(hookmanager.trigger("HOOK_GROUP_CREATE", self))

    def delete(self):
        list(hookmanager.trigger("HOOK_GROUP_DELETE", self))
        env.auth.delete_group(self)


class User(NameID):
    __sentinel = object()

    def __init__(self, login=None, userid=None):
        self._orig_configuration = None
        NameID.__init__(self, login, userid)

    def _id2name(self, id):
        user = env.auth.get_user_by_id(id)
        if not user:
            raise UnknownNameIDError(id)

        return user.name

    @cache.request_memoize_property("user_permissions")
    def permissions(self):
        return set(env.auth.get_user_permissions(self))

    @permissions.setter
    def permissions(self, permissions):
        env.auth.set_user_permissions(self, permissions)

    def _permissions(self, permissions):
        self.permissions  # make sure the cache has been created
        env.request.cache.user_permissions._set(((self,), ()), set(permissions))

    # Support access to _permissions to modify object permission without backend modification.
    _permissions = property(permissions, _permissions)

    @property
    def configuration(self):
        ret = self._configuration()
        if self._orig_configuration is None:
            self._orig_configuration = copy.deepcopy(ret)

        return ret

    @cache.request_memoize("user_configuration")
    def _configuration(self):
        rows = env.db.query("SELECT config FROM Prewikka_User_Configuration WHERE userid = %s", self.id)
        if rows:
            return json.loads(rows[0][0])
        else:
            return {}

    @configuration.setter
    def configuration(self, conf):
        env.request.cache.user_configuration._set(((self,), ()), conf)

    @cache.request_memoize_property("user_timezone")
    def timezone(self):
        return utils.timeutil.timezone(self.get_property("timezone", default=env.config.general.default_timezone))

    def set_locale(self):
        lang = self.get_property("language", default=env.config.general.default_locale)
        if lang:
            localization.set_locale(lang)

    def del_property(self, key, view=None):
        view = view or ""

        if not key:
            self.configuration.pop(view, None)
        else:
            self.configuration.get(view, {}).pop(key, None)

    def del_properties(self, view):
        self.configuration.pop(view, None)

    def del_property_match(self, key, view=None):
        view = view or ""
        viewlist = [view] if view else self.configuration.keys()

        for v in viewlist:
            if v not in self.configuration:
                continue

            for k in list(self.configuration[v]):
                if k.find(key) != -1:
                    self.del_property(k, view=v)

    def get_property_fail(self, key, view=None, default=__sentinel):
        view = self.configuration.get(view or "", {})

        if default is not self.__sentinel:
            return view.get(key, default)

        return view[key]

    def has_property(self, key, view=None):
        return key in self.configuration.get(view or "", {})

    def get_property(self, key, view=None, default=None):
        return self.get_property_fail(key, view or "", default)

    def set_property(self, key, value, view=None):
        self.configuration.setdefault(view or "", {})[key] = value

    def sync_properties(self):
        if self._orig_configuration is not None and self._orig_configuration != self.configuration:
            self._orig_configuration = copy.deepcopy(self.configuration)
            env.db.upsert("Prewikka_User_Configuration", ["userid", "config"], [[self.id, json.dumps(self.configuration)]], pkey=("userid",))

        if env.request.user == self:
            env.request.user = self

    def has(self, perm):
        if type(perm) in (list, tuple, set):
            return self.permissions.issuperset(perm)

        return perm in self.permissions

    def check(self, perm, view=None):
        if not self.has(perm):
            raise PermissionDeniedError(perm, view)

    def create(self):
        env.auth.create_user(self)
        list(hookmanager.trigger("HOOK_USER_CREATE", self))

    def delete(self):
        list(hookmanager.trigger("HOOK_USER_DELETE", self))
        env.db.query("DELETE FROM Prewikka_User_Configuration WHERE userid = %s", self.id)
        env.auth.delete_user(self)
