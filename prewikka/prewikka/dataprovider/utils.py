# -*- coding: utf-8 -*-
# Copyright (C) 2016-2021 CS GROUP - France. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>
# Author: François POIROTTE <francois.poirotte@c-s.fr>
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

from datetime import datetime

from prewikka import error, utils


def _get_yday(date):
    return date.timetuple().tm_yday


_EXTRACT_TO_DATETIME = {
    "year": "year",
    "month": "month",
    "yday": _get_yday,
    "mday": "day",
    "wday": datetime.weekday,
    "hour": "hour",
    "min": "minute",
    "sec": "second"
}


def extract_from_date(date, extract):
    """Extracts and returns the value of a specified datetime field
       from a datetime.
    """
    if not isinstance(date, datetime):
        raise error.PrewikkaUserError(N_("Invalid operation"),
                                      N_("Extraction is supported only for date fields"))

    attr = _EXTRACT_TO_DATETIME[extract]
    return attr(date) if callable(attr) else getattr(date, attr)


def apply_timezone(date, tz):
    """Returns a datetime object which is equivalent to the given
       datetime converted to the given timezone.
    """
    if not date.tzinfo or (date.tzinfo and date.tzinfo.utcoffset(date) is None):
        # date is a naive datetime
        date = date.replace(tzinfo=utils.timeutil.tzutc())

    return date.astimezone(tz)
