# Copyright (C) 2009-2021 CS GROUP - France. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoann.v@prelude-ids.com>
#
# This file is part of the Prelude-Correlator program.
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

import glob
import io
import os

try:
    import configparser
except:
    import ConfigParser as configparser


class Config(configparser.ConfigParser):
    def __init__(self, filename):
        configparser.ConfigParser.__init__(self, allow_no_value=True)
        self.read(filename)

        # Allow inclusion of additional configuration files in
        # prelude-correlator.conf.
        # These additional configuration files can be used by plugins.
        if self.has_section('include'):
            dataset = []
            includes = self.items('include')
            confdir = os.path.dirname(os.path.abspath(filename))

            for fpattern, _dummy in includes:
                fpattern = os.path.join(confdir, fpattern)

                # Files are loaded in alphabetical order
                for fname in sorted(glob.glob(fpattern)):
                    dataset.append(fname)

            self.read(dataset)

    def get(self, section, option, raw=None, vars=None, fallback=None, type=str):
        try:
            return type(configparser.ConfigParser.get(self, section, option, raw=raw, vars=vars))

        except configparser.NoSectionError:
            return fallback

        except configparser.NoOptionError:
            return fallback

    def getAsBool(self, section, option, raw=None, vars=None, fallback=None):
        b = self.get(section, option, raw, vars, fallback)
        if type(b) is bool:
            return b

        b = b.strip().lower()
        if b == "true" or b == "yes":
            return True

        return False

    def read(self, filename):
        if not isinstance(filename, list):
            filename = [filename]

        for fname in filename:
            try:
                with io.open(fname, 'r') as f:
                    self.readfp(io.StringIO('[prelude]\n' + f.read()))
            except IOError:
                continue
