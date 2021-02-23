# Copyright (C) 2018-2020 CS GROUP - France. All Rights Reserved.
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
Tests for `prewikka.menu`.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os

import pytest

from prewikka.error import PrewikkaUserError
from prewikka.menu import MenuManager
from tests.utils.vars import TEST_DATA_DIR


def test_menu_manager():
    """
    Test `prewikka.menu.MenuManager` class.
    """
    backup_interface = env.config.interface

    # default
    MenuManager()

    # invalid menu (empty)
    with pytest.raises(PrewikkaUserError):
        env.config.interface = {'menu_order': os.path.join(TEST_DATA_DIR, 'menu_empty.yml')}
        MenuManager()

    # invalid menu (no name AND no icon)
    with pytest.raises(PrewikkaUserError):
        env.config.interface = {'menu_order': os.path.join(TEST_DATA_DIR, 'menu_no_name_and_no_icon.yml')}
        MenuManager()

    # invalid menu (multiple default menu)
    with pytest.raises(PrewikkaUserError):
        env.config.interface = {'menu_order': os.path.join(TEST_DATA_DIR, 'menu_multiple_default.yml')}
        MenuManager()

    # valid menu (no default)
    env.config.interface = {'menu_order': os.path.join(TEST_DATA_DIR, 'menu_no_default.yml')}
    MenuManager()

    # invalid menu (section without name)
    with pytest.raises(PrewikkaUserError):
        env.config.interface = {'menu_order': os.path.join(TEST_DATA_DIR, 'menu_section_no_name.yml')}
        MenuManager()

    # invalid menu (section with multiple default tab)
    with pytest.raises(PrewikkaUserError):
        env.config.interface = {
            'menu_order': os.path.join(TEST_DATA_DIR, 'menu_section_multiple_default_tab.yml')
        }
        MenuManager()

    # clean
    env.config.interface = backup_interface


def test_menu_manager_methods():
    """
    Test `prewikka.menu.MenuManager` methods.
    """
    menu_manager = MenuManager()

    assert menu_manager.get_sections() == {}
    assert menu_manager.get_menus()
    assert menu_manager.get_declared_sections()

    menu_manager.add_section_info('section', 'tab', 'endpoint')
