# Copyright (C) 2007-2020 CS GROUP - France. All Rights Reserved.
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

from prewikka import auth, database, session, usergroup, version


class AnonymousSession(auth.Auth, session.Session, database.DatabaseHelper):
    plugin_name = "Anonymous authentication"
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_version = version.__version__
    plugin_copyright = version.__copyright__
    plugin_description = N_("Anonymous authentication")

    autologin = True

    def __init__(self, config):
        auth.Auth.__init__(self, config)
        session.Session.__init__(self, config)

    def init(self, config):
        user = usergroup.User("anonymous")
        if not auth.Auth.get_user_by_id(self, user.id):
            self.create_user(user)

    def get_user_permissions(self, user, ignore_group=False):
        return usergroup.ALL_PERMISSIONS

    def get_user_info(self, request):
        return session.SessionUserInfo("anonymous", None)

    def get_user_list(self, search=None):
        return [usergroup.User("anonymous")]

    def get_user_by_id(self, id_):
        return usergroup.User("anonymous")

    def has_user(self, other):
        return usergroup.User("anonymous")

    def authenticate(self, login, password="", no_password_check=False):
        return usergroup.User("anonymous")
