# Copyright (C) 2004-2020 CS GROUP - France. All Rights Reserved.
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

import binascii
import os
import struct
import time

from prewikka import database, hookmanager, log, pluginmanager, usergroup, utils
from prewikka.error import PrewikkaUserError, RedirectionError


class _SessionError(PrewikkaUserError):
    code = 401

    def __init__(self, login=None, **kwargs):
        PrewikkaUserError.__init__(self, log_user=login, **kwargs)


class SessionInvalid(_SessionError):
    name = N_("Invalid session")
    message = N_("The session cookie carried by your browser is invalid")


class SessionExpired(_SessionError):
    name = N_("Session expired")
    message = N_("Your session has expired: please sign in again to continue using Prelude")


class SessionUserInfo(object):
    def __init__(self, login, password=None):
        self.login = login
        self.password = password


class SessionDatabase(database.DatabaseHelper):
    def create_session(self, sessionid, user, time):
        self.query("INSERT INTO Prewikka_Session (sessionid, userid, login, time) VALUES(%s, %s, %s, %s)",
                   sessionid, user.id, user.name, self.datetime(time))

    def update_session(self, sessionid, time):
        self.query("UPDATE Prewikka_Session SET time=%s WHERE sessionid=%s", self.datetime(time), sessionid)

    def get_session(self, sessionid):
        rows = self.query("SELECT login, time FROM Prewikka_Session WHERE sessionid = %s", sessionid)
        if not rows:
            raise

        login, t = rows[0]
        return login, utils.timeutil.get_timestamp_from_string(t)

    def delete_session(self, sessionid=None, user=None):
        assert not (sessionid and user)

        if sessionid:
            self.query("DELETE FROM Prewikka_Session WHERE sessionid = %s", sessionid)
        elif user:
            self.query("DELETE FROM Prewikka_Session WHERE userid = %s", user.id)

    def delete_expired_sessions(self, time):
        self.query("DELETE FROM Prewikka_Session WHERE time < %s", self.datetime(time))


class Session(pluginmanager.PluginBase):
    template = None
    autologin = False
    plugin_mandatory = True

    def __init__(self, config):
        pluginmanager.PluginBase.__init__(self)

        self._db = SessionDatabase()
        self._expiration = config.get_int('expiration', 60) * 60

    def __set_session(self, request, sessionid):
        request.add_cookie("sessionid", sessionid, expires=self._expiration * 3, httponly=True)

    def __check_session(self, request):
        sessionid = request.input_cookie.get("sessionid")
        if not sessionid:
            # No session cookie sent by the browser
            if request.is_xhr:
                # In case of an AJAX request, we consider that
                # the session cookie expired and was not sent.
                raise SessionExpired(login=None, template=self.template)
            else:
                # Otherwise, we consider that the session cookie did not exist,
                # and we don't display any message on the login page.
                raise SessionInvalid(message="", template=self.template, log_priority=log.INFO)

        sessionid = sessionid.value

        try:
            login, t = self._db.get_session(sessionid)
        except:
            request.delete_cookie("sessionid")
            raise SessionInvalid(template=self.template)

        # Check that the session is still alive...
        now = int(time.time())
        if now - t > self._expiration:
            self.__delete_session(request)
            raise SessionExpired(login, template=self.template)

        # And that the user it carry still exist in the current authentication
        # backend (which might have changed)
        user = usergroup.User(login)
        if not env.auth.has_user(user):
            self.__delete_session(request)
            raise SessionInvalid(login, template=self.template)

        if (now - t) / 60 >= 5:
            self._db.update_session(sessionid, now)
            list(hookmanager.trigger("HOOK_SESSION_UPDATE", user))

        self.__set_session(request, sessionid)
        return login

    def __create_session(self, request, user):
        t = time.time()

        self._db.delete_expired_sessions(t - self._expiration)
        sessionid = binascii.hexlify(os.urandom(16) + struct.pack(b">d", t)).decode("utf8")

        self._db.create_session(sessionid, user, int(t))
        self.__set_session(request, sessionid)

    def __delete_session(self, request):
        self._db.delete_session(sessionid=request.input_cookie["sessionid"].value)
        request.delete_cookie("sessionid")

    def get_user(self, request):
        info = self.get_user_info(request)
        if not(info) or not(info.login) or self.autologin:
            try:
                login = self.__check_session(request)
            except (SessionInvalid, SessionExpired):
                if not self.autologin:
                    raise
            else:
                if not info or not info.login or login == info.login:
                    return usergroup.User(login)
                else:
                    self.__delete_session(request)

        user = self.authenticate(request, info)
        self.__create_session(request, user)

        list(hookmanager.trigger("HOOK_SESSION_CREATE", user))

        is_admin = set(user.permissions) == usergroup.ALL_PERMISSIONS
        env.log.info("User login with profile '%s'" % ("admin" if is_admin else "default"))

        if "login_prevent_redirect" in env.request.web.arguments:
            return user

        raise RedirectionError(env.request.web.get_raw_uri(True), 303)

    def authenticate(self, request, info):
        return env.auth.authenticate(info.login, info.password)

    def logout(self, request):
        login = self.__check_session(request)
        self.__delete_session(request)
        list(hookmanager.trigger("HOOK_SESSION_DELETE", usergroup.User(login)))
        env.log.info("Logged out")

        raise SessionInvalid(message=N_("Logged out"),
                             login=login,
                             log_priority=log.INFO,
                             template=self.template)

    def can_logout(self):
        return "logout" in self.__class__.__dict__

    def get_user_info(self, request):
        pass

    def get_default_auth(self):
        pass

    def init(self, config):
        pass
