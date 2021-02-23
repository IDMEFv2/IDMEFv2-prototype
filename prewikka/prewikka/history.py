# Copyright (C) 2017-2020 CS GROUP - France. All Rights Reserved.
# Author: Camille Gardet <camille.gardet@c-s.fr>
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

from hashlib import md5

from prewikka import crontab, database, log, utils

logger = log.get_logger(__name__)


class HistoryDatabase(database.DatabaseHelper):
    def init(self):
        # This should not be executed if env.db fails to initialize
        crontab.schedule("search_history", N_("Search history deletion"), "0 * * * *", _regfunc=history._history_cron, enabled=True)

    def create(self, user, form):
        return utils.AttrObj(
            content=self.get_queries(user, form),
            url={
                "save": url_for('BaseView.history_save', form=form),
                "delete": url_for('BaseView.history_delete', form=form),
                "get": url_for('BaseView.history_get', form=form)
            }
        )

    def _where(self, user=True, form=True, query_hash=True):
        where = []

        if user:
            where.append("userid = %(user)s")
        if form:
            where.append("formid = %(form)s")
        if query_hash:
            where.append("query_hash = %(query_hash)s")

        return "" if not where else " WHERE %s" % " AND ".join(where)

    def get_queries(self, user, form):
        query = ("SELECT query FROM Prewikka_History_Query %s ORDER BY timestamp DESC" %
                 self._where(query_hash=False))

        return [row[0] for row in self.query(query, user=user.id, form=form)]

    def save(self, user, form, query):
        query_hash = md5(query.encode("utf8")).hexdigest()
        rows = [(user.id, form, query, query_hash, utils.timeutil.utcnow())]
        self.upsert("Prewikka_History_Query", ("userid", "formid", "query", "query_hash", "timestamp"), rows, pkey=("userid", "formid", "query_hash"))

        logger.info("Query saved: %s by %s on form %s", query, user.name, form)

    def delete(self, user, form, query=False):
        query_hash = md5(query.encode("utf8")).hexdigest() if query else False
        self.query("DELETE FROM Prewikka_History_Query" + self._where(query_hash=query_hash), user=user.id, query_hash=query_hash, form=form)

        logger.info("Query deleted: %s by %s on form %s", query or "all queries", user.name, form)

    def _history_cron(self, job):
        config = env.config.cron.get_instance_by_name("search_history")
        if config is None:
            return

        size = int(config.get("size", 10))
        query = "SELECT userid, formid, COUNT(query) FROM Prewikka_History_Query GROUP BY userid, formid"
        for userid, formid, count in self.query(query):
            if int(count) <= size:
                continue

            rows = self.query("SELECT query FROM Prewikka_History_Query WHERE userid = %s AND formid = %s "
                              "ORDER BY timestamp DESC LIMIT %s", userid, formid, size)
            self.query("DELETE FROM Prewikka_History_Query WHERE userid = %s AND formid = %s AND query NOT IN %s",
                       userid, formid, [row[0] for row in rows])


history = HistoryDatabase()

init = history.init
create = history.create
delete = history.delete
get = history.get_queries
save = history.save
