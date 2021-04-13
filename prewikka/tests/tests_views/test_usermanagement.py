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
Tests for `prewikka.views.usermanagement`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from copy import deepcopy

import pytest

from prewikka import localization
from prewikka.error import PrewikkaUserError
from tests.utils.fixtures import load_view_for_fixtures


def test_my_account():
    """
    Test `prewikka.views.usermanagement.my_account` view.
    """
    view = load_view_for_fixtures("usersettings.my_account")
    view.render()


def test_save():
    """
    Test `prewikka.views.usermanagement.save` view.
    """
    view = load_view_for_fixtures("usersettings.save")
    backup_parameters = deepcopy(env.request.parameters)

    # valid
    params = {
        'language': next(iter(localization.get_languages().keys())),
        'timezone': localization.get_timezones()[0],
    }
    env.request.parameters = params

    view.render(name=env.request.user.name)

    # FIXME
    # valid with new email
    # params_email = deepcopy(params)
    # params_email['email'] = 'foo@bar.tld'
    # env.request.parameters = params_email

    # view.render()

    # valid with new theme (reload page)
    params_email = deepcopy(params)
    params_email['theme'] = 'dark'
    env.request.parameters = params_email

    view.render(name=env.request.user.name)

    # FIXME
    # valid with different user
    # params_user = deepcopy(params)
    # params_user['name'] = 'test_different'
    # env.request.parameters = params_user

    # view.modify()

    # invalid language
    with pytest.raises(PrewikkaUserError):
        params_invalid = deepcopy(params)
        params_invalid['language'] = None
        env.request.parameters = params_invalid

        view.render(name=env.request.user.name)

    # invalid timezone
    with pytest.raises(PrewikkaUserError):
        params_invalid = deepcopy(params)
        params_invalid['timezone'] = None
        env.request.parameters = params_invalid

        view.render(name=env.request.user.name)

    # clean
    env.request.parameters = backup_parameters
