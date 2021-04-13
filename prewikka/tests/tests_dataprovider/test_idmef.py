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
Tests for `prewikka.dataprovider.idmef`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import prelude

from prewikka.dataprovider import Criterion
from prewikka.dataprovider.idmef import _IDMEFProvider, IDMEFAlertProvider, IDMEFHeartbeatProvider


def test_idmef_provider():
    """
    Test `prewikka.dataprovider.idmef._IDMEFProvider()` class.
    """
    provider = _IDMEFProvider()

    assert provider.get_path_type('alert.classification.text') is text_type
    assert provider._get_paths(prelude.IDMEFClass('alert.classification'))


def test_idmef_alert_provider():
    """
    Test `prewikka.dataprovider.idmef.IDMEFAlertProvider` class.
    """
    alert_provider = IDMEFAlertProvider()

    assert alert_provider.get_path_type('alert.classification.text')
    assert alert_provider.get_paths()
    assert alert_provider.get_common_paths()
    assert alert_provider.compile_criterion(Criterion('alert.classification.text', '<>', 'foo'))
    assert alert_provider.compile_criterion(Criterion('alert.classification.text', '<>', '*'))
    assert alert_provider.compile_criterion(Criterion('alert.classification.text', '=', None))


def test_idemf_heartbeat_provider():
    """
    Test `prewikka.dataprovider.idmef.IDMEFHeartbeatProvider` class.
    """
    heartbeat_provider = IDMEFHeartbeatProvider()

    assert heartbeat_provider.get_path_type('alert.classification.text')
    assert heartbeat_provider.get_paths()
