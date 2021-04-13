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

from __future__ import absolute_import, division, print_function, unicode_literals

import logging
import logging.handlers
import os
import stat
import sys

DEBUG = logging.DEBUG
INFO = logging.INFO
ERROR = logging.ERROR
WARNING = logging.WARNING
CRITICAL = logging.CRITICAL


class Log(object):
    def __init__(self, conf):
        self._logger = None

        for instance in conf:
            self._logger = logging.getLogger()
            self._logger.setLevel(logging.NOTSET)
            self._logger.addHandler(self._get_handler(instance))

    def _get_syslog_handler_address(self):
        for f in ("/dev/log", "/var/run/log", "/var/run/syslog"):
            try:
                if stat.S_ISSOCK(os.stat(f).st_mode):
                    return str(f)
            except:
                pass

        return "localhost", 514

    def _get_handler(self, config):
        logtype = (config.get_instance_name() or "syslog").lower()
        level = config.get("level", "")

        if logtype == 'file':
            hdlr = logging.FileHandler(config.file)

        elif logtype == 'nteventlog':
            hdlr = logging.handlers.NTEventLogHandler("Prewikka", logtype='Application')

        elif logtype in ('syslog', 'unix'):
            hdlr = logging.handlers.SysLogHandler(self._get_syslog_handler_address(), facility=logging.handlers.SysLogHandler.LOG_DAEMON)

        elif logtype == 'smtp':
            hdlr = logging.handlers.SMTPHandler(config.host, getattr(config, "from"), config.to.split(", "), config.subject)

        elif logtype == 'stderr':
            hdlr = logging.StreamHandler(sys.stderr)

        else:
            raise ValueError("Unknown logtype specified: '%s'" % logtype)

        format = 'prewikka (pid:%(process)d) %(name)s %(levelname)s: %(message)s'
        if logtype in ['file', 'stderr']:
            format = '%(asctime)s ' + format

        datefmt = ''
        if logtype == 'stderr':
            datefmt = '%X'

        level = level.upper()
        if level in ['DEBUG', 'ALL']:
            hdlr.setLevel(logging.DEBUG)
        elif level == 'INFO':
            hdlr.setLevel(logging.INFO)
        elif level == 'ERROR':
            hdlr.setLevel(logging.ERROR)
        elif level == 'CRITICAL':
            hdlr.setLevel(logging.CRITICAL)
        else:
            hdlr.setLevel(logging.WARNING)

        formatter = logging.Formatter(format, datefmt)
        hdlr.setFormatter(formatter)

        return hdlr

    def _format_header(self):
        if not env.request.web:
            return ""

        hdr = "".join(("[", env.request.web.get_remote_addr()))

        port = env.request.web.get_remote_port()
        if port:
            hdr = ":".join((hdr, text_type(port)))

        hdr = " ".join((hdr, "%s@" % (env.request.user) if env.request.user else ""))

        flags = ""
        if env.request.web.is_xhr:
            flags = " (xhr)"
        elif env.request.web.is_stream:
            flags = " (sse)"

        return "".join((hdr, env.request.web.path, flags, "]"))

    def _get_log(self, details):
        hdr = self._format_header()
        hdr = [hdr] if hdr else []

        if isinstance(details, Exception):
            details = " ".join([text_type(getattr(details, "code", 500)), text_type(details)])

        return " ".join(hdr + [text_type(details)])

    def debug(self, message):
        if self._logger:
            self._logger.debug(self._get_log(message))

    def info(self, message):
        if self._logger:
            self._logger.info(self._get_log(message))

    def warning(self, message):
        if self._logger:
            self._logger.warning(self._get_log(message))

    def error(self, message):
        if self._logger:
            self._logger.error(self._get_log(message))

    def critical(self, message):
        if self._logger:
            self._logger.critical(self._get_log(message))

    def log(self, priority, message):
        return {
            DEBUG: self.debug,
            INFO: self.info,
            WARNING: self.warning,
            ERROR: self.error,
            CRITICAL: self.critical
        }[priority](message)


def get_logger(name=__name__):
    return logging.getLogger(name)
