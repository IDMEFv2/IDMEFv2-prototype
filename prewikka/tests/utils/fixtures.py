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
Fixture utils for prewikka tests suite.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import os
import shutil
import sys

from prewikka.utils import json
from prewikka.web.request import Request as InitialRequest


class FakeInitialRequest(InitialRequest):
    """
    Fake InitialRequest to load Prewikka out of browser.

    We just fake some methods to prevent exceptions during tests.
    """
    script_name = 'test_script'
    method = 'GET'
    headers = {}
    port = None

    def __init__(self, path):
        super(FakeInitialRequest, self).__init__(path)

    def get_script_name(self):
        """
        Fake script name.

        :return: script name
        :rtype: str
        """
        return self.script_name

    def get_remote_addr(self):
        return '127.0.0.1'

    def get_baseurl(self):
        return ''

    def get_cookie(self):
        return

    def get_raw_uri(self, include_qs=False):
        return

    def get_remote_port(self):
        return self.port

    def send_headers(self, headers=None, code=200, status_text=None):
        return

    def write(self, data):
        return

    @staticmethod
    def get_uri():
        """
        Fake get_uri() for test suite.
        """
        return ''

    def send_stream(self, data, event=None, evid=None, retry=None, sync=False):
        """
        Used to print message in stdout.
        """
        if len(data) == 0:
            return

        sys.stdout.write('env.web.request.send_stream():\n')

        try:
            for key, value in json.loads(data).iteritems():
                sys.stdout.write('    %s: %s\n' % (key, value))
        except ValueError:
            sys.stdout.write('    %s\n' % data)


def clean_directory(path):
    """
    Delete all content in a directory.

    :param str path: the path of directory to delete
    """
    shutil.rmtree(path)
    os.makedirs(path)


def load_view_for_fixtures(name):
    """
    Function used in fixtures to load a view.

    :param name: name of the view.
    :return: The view object.
    :rtype: prewikka.view.View
    """
    view = env.viewmanager.get_view(name)

    assert view

    view.__init__()  # init view to load hooks
    env.request.parameters = view.view_parameters(view)
    env.request.view = view

    return view
