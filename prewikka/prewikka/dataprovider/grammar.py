# coding: utf-8
# Copyright (C) 2019-2020 CS GROUP - France. All Rights Reserved.
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


GRAMMAR = r"""
    selection: (function | path) [extract] [commands]

    extract: ":" EXTRACT
    commands: "/" COMMAND ("," COMMAND)*

    ?function: FUNCTION "(" function_args ")"
    function_args: _function_arg ("," _function_arg)*
    _function_arg: path | function | const

    COMMAND: "group_by" | "order_desc" | "order_asc"
    EXTRACT: "year" | "month" | "yday" | "mday" | "wday" | "hour" | "min" | "sec" | "msec" | "usec" | "quarter"
    FUNCTION.2: "count" | "min" | "max" | "sum" | "avg" | "timezone" | "distinct"

    int_: DIGIT
    float_: NUMBER
    path: PATH
    const: DIGIT | NUMBER | string
    string: (dqstring | sqstring)

    SQSTRING.1: "'" ("\\'" | /[^']/)* "'"
    DQSTRING.1: "\"" ("\\\""|/[^"]/)* "\""
    !sqstring: SQSTRING
    !dqstring: DQSTRING

    PATH.1: (PATHELEM ".")* PATHELEM
    PATHELEM: WORD ("(" PATHINDEX ")")?
    PATHINDEX: ("-"? DIGIT+ | DQSTRING | SQSTRING)
    WORD: (LETTER | "_") (LETTER | DIGIT | "-" | "_")*
    DIGIT: /[0-9]/+
    LETTER: /[a-z]/

    %import common.NUMBER
    %import common.WS
    %ignore WS
"""
