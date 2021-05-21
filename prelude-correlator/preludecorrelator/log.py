# Copyright (C) 2009-2021 CS GROUP - France. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>
#
# This file is part of the Prelude-Correlator program.
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

import prelude
import logging
import logging.config
import logging.handlers
import sys
import os
import stat


debug_level = 0


def _debug(self, msg, *args, **kwargs):
    level = kwargs.pop("level", 0)

    if debug_level and level <= debug_level:
        self.log(logging.DEBUG, msg, *args, **kwargs)


logging.Logger.debug = _debug


def __C_log_callback(level, log):
    log = log.rstrip('\n')
    logger = getLogger("libprelude")

    if level == prelude.PreludeLog.DEBUG:
        logger.debug(log)

    elif level == prelude.PreludeLog.INFO:
        logger.info(log)

    elif level == prelude.PreludeLog.WARNING:
        logger.warning(log)

    elif level == prelude.PreludeLog.ERROR:
        logger.error(log)

    elif level == prelude.PreludeLog.CRITICAL:
        logger.critical(log)

    else:
        logger.warning(("[unknown:%d] " % level) + log)


def getSyslogHandlerAddress():
    for f in ("/dev/log", "/var/run/log", "/var/run/syslog"):
        try:
            if stat.S_ISSOCK(os.stat(f).st_mode):
                return f
        except:
            pass

    return "localhost", 514


def initLogger(options):
    global debug_level

    debug_level = options.debug

    try:
        prelude.PreludeLog.setCallback(__C_log_callback)
    except:
        # PreludeLog is available in recent libprelude version, we do not want to fail if it's not.
        pass

    try:
        logging.config.fileConfig(options.config)
    except Exception:
        DATEFMT = "%d %b %H:%M:%S"
        FORMAT = "%(asctime)s %(name)s (pid:%(process)d) %(levelname)s: %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=FORMAT, datefmt=DATEFMT, stream=sys.stderr)

    if options.daemon is True:
        hdlr = logging.handlers.SysLogHandler(getSyslogHandlerAddress(),
                                              facility=logging.handlers.SysLogHandler.LOG_DAEMON)
        hdlr.setFormatter(logging.Formatter('%(name)s: %(levelname)s: %(message)s'))
        logging.getLogger().addHandler(hdlr)


def getLogger(name=__name__):
    return logging.getLogger(name)
