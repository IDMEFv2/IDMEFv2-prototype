# Copyright (C) 2016-2020 CS GROUP - France. All Rights Reserved.
# Author: Abdel ELMILI <abdel.elmili@c-s.fr>
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

import prelude
from prelude import IDMEFTime, IDMEFValue
from prewikka import error, idmefdatabase, usergroup, utils, version
from prewikka.dataprovider import DataProviderBackend, QueryResults, QueryResultsRow, ResultObject


class IDMEFResultObject(ResultObject, utils.json.JSONObject):
    def preprocess_value(self, value):
        if isinstance(value, IDMEFTime):
            return datetime.fromtimestamp(value, utils.timeutil.tzoffset(None, value.getGmtOffset()))

        return ResultObject.preprocess_value(self, value)

    @classmethod
    def from_json(cls, data):
        return cls(prelude.IDMEF(data["idmef_json"]))

    def __json__(self):
        return {"idmef_json": self._obj.toJSON()}


class IDMEFQueryResultsRow(QueryResultsRow):
    __slots__ = ()

    def preprocess_value(self, value):
        if isinstance(value, IDMEFTime):
            return datetime.fromtimestamp(value, utils.timeutil.tzoffset(None, value.getGmtOffset()))

        return QueryResultsRow.preprocess_value(self, value)


class IDMEFQueryResults(QueryResults):
    __slots__ = ()

    def preprocess_value(self, value):
        return IDMEFQueryResultsRow(self, value)


class _IDMEFPlugin(DataProviderBackend):
    plugin_version = version.__version__
    plugin_author = version.__author__
    plugin_license = version.__license__
    plugin_copyright = version.__copyright__

    def __init__(self):
        DataProviderBackend.__init__(self)
        try:
            self._db = idmefdatabase.IDMEFDatabase(env.config.idmef_database)
        except Exception as e:
            raise error.PrewikkaUserError(N_("Initialization error"), e)

    def get_properties(self):
        return utils.AttrObj(format=self._db.getFormatName())

    def _iterate_object(self, results):
        for ident in results:
            res = IDMEFResultObject(self._get_object(ident))
            res.ident = ident

            yield res

    def update(self, data, criteria):
        paths, values = zip(*data)
        self._db.update(list(paths), [IDMEFValue(v) for v in values], criteria)

    def get(self, criteria, order_by, limit, offset):
        results = self._get_idents(criteria, limit, offset, order_by)
        return utils.CachingIterator(self._iterate_object(results))

    @usergroup.permissions_required(["IDMEF_VIEW"])
    def get_values(self, paths, criteria, distinct, limit, offset):

        # FIXME: update libpreludedb to perform this automatically?
        #
        # This allow get_values() without explicit path or criteria, like
        # env.dataprovider.query(["count(1)"], type="alert"), to work:
        if not criteria and not env.dataprovider.guess_datatype(paths, default=None):
            criteria = "%s.messageid" % self.type

        return IDMEFQueryResults(self._db.getValues(paths, criteria, distinct, limit, offset))

    @usergroup.permissions_required(["IDMEF_ALTER"])
    def delete(self, criteria, paths):
        self._db.remove(criteria)


class IDMEFAlertPlugin(_IDMEFPlugin):
    type = "alert"
    plugin_name = "IDMEF Alert Plugin"
    plugin_description = N_("Plugin for fetching IDMEF alerts from the Prelude database")

    @property
    def _get_object(self):
        return self._db.getAlert

    @property
    def _get_idents(self):
        return self._db.getAlertIdents


class IDMEFHeartbeatPlugin(_IDMEFPlugin):
    type = "heartbeat"
    plugin_name = "IDMEF Heartbeat Plugin"
    plugin_description = N_("Plugin for fetching IDMEF heartbeats from the Prelude database")

    @property
    def _get_object(self):
        return self._db.getHeartbeat

    @property
    def _get_idents(self):
        return self._db.getHeartbeatIdents
