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

from passlib.context import CryptContext

from prewikka import auth, database, error, usergroup, version


class DBAuth(auth.Auth, database.DatabaseHelper):
    plugin_name = "Local authentication"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Authentication management with local user / group database")
    plugin_database_branch = version.__branch__
    plugin_database_version = "0"

    def __init__(self, config):
        auth.Auth.__init__(self, config)
        database.DatabaseHelper.__init__(self)

    def init(self, config):
        adminuser = usergroup.User(config.get("initial_admin_user", usergroup.ADMIN_LOGIN))
        adminpass = config.get("initial_admin_pass", usergroup.ADMIN_LOGIN)
        deprecated_schemes = config.get("deprecated_password_schemes", "").split()
        schemes = config.get("password_schemes", "sha256_crypt").split() + deprecated_schemes

        try:
            self._context = CryptContext(schemes=schemes, deprecated=deprecated_schemes)
        except (KeyError, ValueError) as e:
            raise error.PrewikkaUserError(N_("DBAuth initialization error"), e)

        # If there are no accessible users other than ADMIN_LOGIN
        # with administrative rights, we grant all permissions to ADMIN_LOGIN.
        has_user_manager = any("USER_MANAGEMENT" in user.permissions and user != adminuser for user in self.get_user_list())
        if not has_user_manager:
            if not self.has_user(adminuser):
                adminuser.create()

            if not adminuser.has_property("password"):
                self.set_password(adminuser, adminpass)

            self.set_user_permissions(adminuser, usergroup.ALL_PERMISSIONS)

    def _verify(self, password, hashed):
        try:
            return self._context.verify_and_update(password, hashed)
        except (TypeError, ValueError):
            return False, None

    def can_handle_groups(self):
        return True

    def can_create_user(self):
        return True

    def can_create_group(self):
        return True

    def can_delete_user(self):
        return True

    def can_delete_group(self):
        return True

    def get_user_list(self, search=None):
        query = "SELECT name, userid FROM Prewikka_User"
        if search:
            query += " WHERE name LIKE %s" % self.escape("%%%s%%" % search)
        return [usergroup.User(*r) for r in self.query(query)]

    def get_group_list(self, search=None):
        query = "SELECT name, groupid FROM Prewikka_Group"
        if search:
            query += " WHERE name LIKE %s" % self.escape("%%%s%%" % search)
        return [usergroup.Group(*r) for r in self.query(query)]

    def has_user(self, user):
        return self.get_user_by_id(user.id)

    def has_group(self, grp):
        return self.get_group_by_id(grp.id)

    def get_user_permissions(self, user, ignore_group=False):
        uid = self.escape(user.id)

        qstr = ""
        if not ignore_group:
            qstr = " UNION \
                     SELECT pgp.permission FROM Prewikka_User_Group pug \
                     JOIN Prewikka_Group_Permission pgp USING (groupid) \
                     WHERE pug.userid = %s" % (uid)

        return set(r[0] for r in self.query("SELECT pp.permission FROM Prewikka_User_Permission pp where pp.userid = %s%s" % (uid, qstr)))

    def get_group_permissions(self, group):
        return set(r[0] for r in self.query("SELECT permission FROM Prewikka_Group_Permission WHERE groupid = %s", group.id))

    def _set_permissions(self, table, field, obj, permissions):
        permissions = sorted(set(permissions))  # sorting avoids potential deadlock
        self.upsert(table, (field, "permission"), ((obj.id, perm) for perm in permissions), merge={field: obj.id})

    def set_user_permissions(self, user, permissions):
        self._set_permissions("Prewikka_User_Permission", "userid", user, permissions)

    def set_group_permissions(self, group, permissions):
        self._set_permissions("Prewikka_Group_Permission", "groupid", group, permissions)

    # Group specific
    def set_group_members(self, group, users):
        rows = ((group.id, user.id) for user in users)
        self.upsert("Prewikka_User_Group", ("groupid", "userid"), rows, merge={"groupid": group.id})

    def get_group_members(self, group):
        return [usergroup.User(*r) for r in self.query("SELECT PU.name, PUG.userid FROM Prewikka_User_Group PUG "
                                                       "JOIN Prewikka_User PU USING (userid) WHERE groupid = %s", group.id)]

    def set_member_of(self, user, groups):
        rows = ((group.id, user.id) for group in set(groups))
        self.upsert("Prewikka_User_Group", ("groupid", "userid"), rows, merge={"userid": user.id})

    def get_member_of(self, user):
        return [usergroup.Group(*r) for r in self.query("SELECT PG.name, PUG.groupid FROM Prewikka_User_Group PUG "
                                                        "JOIN Prewikka_Group PG USING (groupid) WHERE userid = %s", user.id)]

    def is_member_of(self, group, user):
        return bool(self.query("SELECT groupid from Prewikka_User_Group where groupid = %s and userid = %s", group.id, user.id))

    def get_user_permissions_from_groups(self, user):
        return set(r[0] for r in self.query("SELECT pgp.permission FROM Prewikka_User_Group pug \
                                             JOIN Prewikka_Group_Permission pgp USING (groupid) \
                                             WHERE pug.userid = %s ", user.id))

    def authenticate(self, login, password="", no_password_check=False):
        if login is None:
            raise auth.AuthError(env.session, _("No login name provided"))

        user = usergroup.User(login)
        if not self.has_user(user):
            raise auth.AuthError(env.session, log_user=login)

        if not no_password_check:
            try:
                real_password = user.get_property_fail("password")
            except Exception:
                raise auth.AuthError(env.session, log_user=user)

            valid, new_hash = self._verify(password, real_password)
            if not valid:
                raise auth.AuthError(env.session, log_user=user)

            if new_hash:
                # Make sure the password uses the proper hashing algorithm
                user.set_property("password", new_hash)
                user.sync_properties()

        return user

    def set_password(self, user, password):
        user.set_property("password", self._context.hash(password))
        user.sync_properties()

    def get_default_session(self):
        return "loginform"
