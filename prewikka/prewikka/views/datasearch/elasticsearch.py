# -*- coding: utf-8 -*-
# Copyright (C) 2018-2021 CS GROUP - France. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannv@gmail.com>
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

import re

from prewikka import resource
from prewikka.views.datasearch.datasearch import HighLighter, QueryParser


_HIGHLIGHT_PRE_TAG = "❤I💘PRELUDE❤"
_HIGHLIGHT_POST_TAG = "❥I💘PRELUDE❥"


class ElasticsearchHighLighter(HighLighter):
    _highlight_regex = re.compile(r"(%s.*?%s)" % (_HIGHLIGHT_PRE_TAG, _HIGHLIGHT_POST_TAG))

    @staticmethod
    def get_clean_value(value):
        return value.replace(_HIGHLIGHT_PRE_TAG, "").replace(_HIGHLIGHT_POST_TAG, "")

    @staticmethod
    def _highlighted(word):
        return (_HIGHLIGHT_PRE_TAG in word) and (_HIGHLIGHT_POST_TAG in word)

    @classmethod
    def split_phrase(self, phrase):
        return filter(None, self._highlight_regex.split(phrase))

    @classmethod
    def word_prepare(cls, word):
        if not cls._highlighted(word):
            return resource.HTMLNode("span", word)

        return resource.HTMLNode("span", cls.get_clean_value(word), _class="hl")


class ElasticsearchQueryParser(QueryParser):
    def _query(self):
        hl = {"pre_tags": [_HIGHLIGHT_PRE_TAG], "post_tags": [_HIGHLIGHT_POST_TAG], "number_of_fragments": 0}

        if env.request.user and env.request.user.get_property("anonymize"):
            hl = {}

        return env.dataprovider.query(self.get_paths(), self.all_criteria, limit=self.limit, offset=self.offset, type=self.type, highlight=hl)
