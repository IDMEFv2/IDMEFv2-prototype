# Copyright (C) 2018-2021 CS GROUP - France. All Rights Reserved.
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

"""
Database utils for prewikka tests suite.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os

import prelude
import preludedb

# FIXME: remove this with pytest 3+, it is used to prevent some encoding (latin-1 for example)
# errors in database messages
prelude.python2_return_unicode(False)

_LIBPRELUDEDB_DEFAULT_SQL_PATH = '/usr/share/libpreludedb/classic/'


def init_idmef_database(config):
    """
    Create IDMEF database.

    :return: prelude SQL object
    :rtype: preludedb.SQL
    """
    sql = preludedb.SQL(dict(config.idmef_database))
    libpreludedb_sql_path = config.libpreludedb.get('sql_path', _LIBPRELUDEDB_DEFAULT_SQL_PATH)

    # create database structure
    sql_file_path = os.path.join(libpreludedb_sql_path, '%s.sql' % config.idmef_database.type)
    with open(sql_file_path, 'r') as sql_file:
        sql.query(sql_file.read())


def clean_database(database):
    """
    Remove all tables in a database.

    :param database: database information from config
    """
    db_type = database.type
    sql = preludedb.SQL(dict(database))

    if db_type == 'pgsql':
        # https://stackoverflow.com/a/36023359
        sql_query = """
DO $$ DECLARE
    r RECORD;
BEGIN
    FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = current_schema()) LOOP
        EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
    END LOOP;
END $$;"""
    elif db_type == 'mysql':
        # http://stackoverflow.com/a/18625545
        sql_query = """
SET FOREIGN_KEY_CHECKS = 0;
SET GROUP_CONCAT_MAX_LEN=32768;
SET @tables = NULL;
SELECT GROUP_CONCAT('`', table_name, '`')
    INTO @tables
    FROM information_schema.tables
    WHERE table_schema = (SELECT DATABASE());
SELECT IFNULL(@tables,'dummy') INTO @tables;
SET @tables = CONCAT('DROP TABLE IF EXISTS ', @tables);
PREPARE stmt FROM @tables;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
SET FOREIGN_KEY_CHECKS = 1;"""

    else:
        raise AttributeError('%s is not a valid database type for test suite' % db_type)

    sql.query(sql_query)
