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
Tests for `prewikka.database`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import pytest

from prewikka.database import DatabaseError, DatabaseSchemaError, DatabaseUpdateHelper
from tests.tests_database.utils import SQLScriptTest, SQLScriptTestWithBranch, SQLScriptTestWithoutVersion, \
    SQLScriptTestWithoutFromBranch, SQLScriptTestInstall


def test_database_error():
    """
    Test `prewikka.database.DatabaseError()` error.
    """
    with pytest.raises(DatabaseError) as e_info:
        raise DatabaseError('test message')

    assert 'test message' in str(e_info)


def test_database_schema_error():
    """
    Test `prewikka.database.DatabaseSchemaError()` error.
    """
    with pytest.raises(DatabaseSchemaError) as e_info:
        raise DatabaseSchemaError('test message')

    assert 'test message' in str(e_info)


def test_sql_script():
    """
    Test `prewikka.database.SQLScript()` class.
    """
    dbup = DatabaseUpdateHelper('test', 0)

    # default
    sql_script = SQLScriptTest(dbup)

    # type = 'branch'
    sql_script_with_branch = SQLScriptTestWithBranch(dbup)

    # type = 'install'
    sql_script_install = SQLScriptTestInstall(dbup)

    # version = None
    with pytest.raises(Exception):
        SQLScriptTestWithoutVersion(dbup)

    # branch != '' but branch_from == ''
    with pytest.raises(Exception):
        SQLScriptTestWithoutFromBranch(dbup)

    assert sql_script._mysql2sqlite('SELECT * FROM foo;') == 'SELECT * FROM foo;'
    assert sql_script._mysql2pgsql('SELECT * FROM foo;') == 'SELECT * FROM foo;'
    assert sql_script._mysqlhandler('input') == 'input'
    assert not sql_script.query('')

    # test apply() method running
    assert not sql_script.apply()
    assert not sql_script_with_branch.apply()
    assert not sql_script_install.apply()

    # test __eq__
    assert not sql_script == sql_script_install
