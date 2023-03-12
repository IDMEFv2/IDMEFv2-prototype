# Copyright (C) 2018-2021 CS GROUP - France. All Rights Reserved.
# Author: Yoann Vandoorselaere <yoannvg@gmail.com>
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

from lark import Lark, Transformer, v_args
from lark.exceptions import LarkError

from prewikka.dataprovider import Criterion, ParserError

from . import grammar


_grammar = Lark(grammar.GRAMMAR, start="criteria", parser="lalr")


class CommonTransformer(Transformer):
    @staticmethod
    def _unescape(input, escaped):
        return input.replace('\\%s' % escaped, escaped)

    @v_args(inline=True)
    def dqstring(self, s):
        s.value = self._unescape(s.value[1:-1], '"')
        return s.value

    @v_args(inline=True)
    def sqstring(self, s):
        s.value = self._unescape(s.value[1:-1], "'")
        return s.value

    uqstring = v_args(inline=True)(text_type)
    path = string = operator = v_args(inline=True)(text_type)


class CriteriaTransformer(CommonTransformer):
    def __init__(self, compile=Criterion):
        self._compile = compile

    parenthesis = v_args(inline=True)(lambda self, criterion: criterion)
    or_ = v_args(inline=True)(lambda self, left, right: Criterion(left, "||", right))
    and_ = v_args(inline=True)(lambda self, left, right: Criterion(left, "&&", right))
    not_ = v_args(inline=True)(lambda self, right: Criterion(operator="!", right=right))
    criterion = v_args(inline=True)(lambda self, left, op, right: self._compile(left, op, right))
    not_null = v_args(inline=True)(lambda self, path: self._compile(path, "!=", None))


def parse(input, transformer=CriteriaTransformer()):
    """Convert a Criterion string to a Criterion object."""
    try:
        tree = _grammar.parse(input)
    except LarkError as e:
        raise ParserError(details=e)

    if transformer:
        return transformer.transform(tree)

    return tree
