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
Tests for `prewikka.renderer`.
"""

import pytest

from prewikka.renderer import COLORS, RED_STD, GRAY_STD, \
    RendererNoDataException, RendererItem, RendererUtils, RendererPluginManager


def test_renderer_no_data_exception():
    """
    Test `prewikka.renderer.RendererNoDataException` exception.
    """
    exc = RendererNoDataException()

    with pytest.raises(RendererNoDataException):
        raise exc

    assert text_type(exc)


def test_renderer_item():
    """
    Test `prewikka.renderer.RendererItem` class.
    """
    renderer_item = RendererItem()

    assert not renderer_item[0]
    assert not renderer_item[1]
    assert not renderer_item[2]


def test_renderer_utils():
    """
    Test `prewikka.renderer.RendererUtils` class.
    """
    renderer_utils = RendererUtils({})

    assert renderer_utils.get_label(('foo',)) == 'foo'
    assert renderer_utils.get_color(('foo',)) == COLORS[0]
    assert renderer_utils.get_color(('bar',)) == COLORS[1]

    severity_color_map = {v.value: (v.label, v.color) for v in env.dataprovider.get_path_info("alert.assessment.impact.severity").value_accept}
    renderer_utils = RendererUtils({'names_and_colors': severity_color_map})

    assert renderer_utils.get_label(('high',)) == 'High'
    assert renderer_utils.get_label(('invalid',)) == 'n/a'
    assert renderer_utils.get_color(('high',)) == RED_STD
    assert renderer_utils.get_color(('invalid',)) == GRAY_STD


def test_renderer_plugin_manager():
    """
    Test `prewikka.renderer.RendererPluginManager` class.
    """
    all_plugins = env.all_plugins
    env.all_plugins = {}

    renderer = RendererPluginManager()
    renderer.load()

    assert set(renderer.get_types()) == set(["bar", "doughnut", "pie", "timebar", "timeline"])
    assert renderer.has_backend("chartjs")
    assert renderer.get_backends("bar")
    assert renderer.get_backends_instances("bar")
    assert renderer.get_default_backend("bar") == "chartjs"

    assert renderer.render("bar", [[(34, "foo", None), (11, "bar", None)]])["script"] is not None

    env.all_plugins = all_plugins
