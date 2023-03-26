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
Pytest fixtures.
"""

import pytest

from prewikka import config, main, usergroup, Request
from prewikka.web.request import cookies
from tests.utils.database import init_idmef_database, clean_database
from tests.utils.fixtures import FakeInitialRequest, clean_directory
from tests.utils.vars import TEST_CONFIG_FILE, TEST_DOWNLOAD_DIR, TEST_SESSION_ID


@pytest.fixture(scope='session', autouse=True)
def initialization_fixtures(request):
    """
    Main fixture for all tests: load Prewikka out of browser by setup
    configuration.

    Configuration and databases information are loaded through default testing file
    or specific configuration file.

    @pytest.fixture:
        scope=session   caching lifecycle of fixture, available during all tests of
                        the run
        autouse=True    activated for all tests that can see it
    """
    # init IDMEF database
    init_idmef_database(config.Config(TEST_CONFIG_FILE))

    # init prewikka core with config file
    main.Core.from_config(TEST_CONFIG_FILE, autoupdate=True)

    def tear_down():
        """
        TearDown

        - clean IDMEF database
        - clean Prewikka database
        - clean "downloads" directory
        """
        clean_database(env.config.idmef_database)
        clean_database(env.config.database)
        clean_directory(TEST_DOWNLOAD_DIR)

    request.addfinalizer(tear_down)


@pytest.fixture(scope='function', autouse=True)
def prewikka_fixtures(request):
    """
    Fixture used on each test (automatically used).
    """
    env.request = Request()
    env.request.user = usergroup.User('anonymous')
    env.request.web = FakeInitialRequest('/')
    env.request.dataset = {}

    cookie = cookies.SimpleCookie()
    cookie['sessionid'] = TEST_SESSION_ID
    env.request.web.input_cookie = dict(cookie.items())
