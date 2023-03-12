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
import sys

from prewikka import log, response, template, utils
from prewikka.localization import _DeferredGettext


class PrewikkaException(Exception):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def respond(self):
        pass


class RedirectionError(PrewikkaException):
    def __init__(self, location, code):
        self.location = location
        self.code = code

    def respond(self):
        return response.PrewikkaRedirectResponse(self.location, code=self.code)


class PrewikkaError(PrewikkaException):
    template = template.PrewikkaTemplate(__name__, 'templates/error.mak')
    name = N_("An unexpected condition happened")
    message = ""
    details = ""
    output = ""
    code = 500
    log_priority = log.ERROR
    display_traceback = True
    errno = None

    def __init__(self, message, name=None, details=None, log_priority=None, log_user=None, template=None, code=None, output=None):
        if name is not None:
            self.name = name

        if message is not None:
            self.message = message

        if details is not None:
            self.details = details

        if template:
            self.template = template

        if code:
            self.code = code

        if log_priority:
            self.log_priority = log_priority

        if output:
            self.output = output

        self.traceback = self._get_traceback()
        self.log_user = log_user

    def _setup_template(self, template, ajax_error):
        dataset = template.dataset()

        for i in ("name", "message", "details", "code", "traceback", "errno", "output"):
            dataset[i] = getattr(self, i)

        dataset["is_ajax_error"] = ajax_error
        dataset["is_error_template"] = True

        return dataset

    def _html_respond(self):
        return env.viewmanager.get_baseview().respond(self._setup_template(self.template, False), self.code)

    def _get_traceback(self):
        if self.display_traceback and env.config.general.get_bool("enable_error_traceback", True):
            return sys.exc_info()

    def respond(self):
        if self.message:
            env.log.log(self.log_priority, self)

        if not self.traceback:
            self.traceback = self._get_traceback()

        if not (env.request.web.is_stream or env.request.web.is_xhr):
            # This case should only occur in case of auth error (and viewmgr might not exist at this time)
            return self._html_respond()

        return response.PrewikkaResponse(self, code=self.code)

    @staticmethod
    def _format_error(message, details):
        if details:
            return "%s: %s" % (message, details)

        # message might be an exception class
        return text_type(message)

    def __str__(self):
        return self._format_error(self.message, self.details)

    def __json__(self):
        dset = self._setup_template(PrewikkaError.template, True)
        return {"content": dset.render(), "error": True}


class PrewikkaUserError(PrewikkaError):
    display_traceback = False

    def __init__(self, name=None, message=None, **kwargs):
        PrewikkaError.__init__(self, message, name=name, **kwargs)
        self.errno = self._get_errno(name, message)

    def _get_errno(self, name, message):
        msg = []
        for s in (name, message):
            if isinstance(s, _DeferredGettext):
                s = s.origin

            msg.extend(text_type(s).split())

        return hash("".join(utils.soundex(x) for x in msg)) & 65535


class NotImplementedError(PrewikkaError):
    name = N_("Not implemented")

    def __init__(self, message=N_("Backend does not implement this operation")):
        PrewikkaError.__init__(self, message, log_priority=log.ERROR)


def make(exc):
    if not isinstance(exc, PrewikkaError):
        return PrewikkaError(exc)

    return exc
