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

GRAMMAR = r"""
    ?input: WS* input2
    ?input2: criteria WS*
    ?criteria: operator_
        | criteria WS+ operator_ -> or_
        | criteria BOOL_OR operator_ -> or_
        | criteria BOOL_AND operator_ -> and_

    ?operator_: (optional | excluded | required)

    excluded: EXCLUDED _criterion?
    required: REQUIRED _criterion?
    optional: _criterion

    parenthesis: LPAR criteria RPAR
    _criterion: field (value | parenthesis)

    value: (inclusive_range | exclusive_range | value_string)

    inclusive_range: "[" WS* _string WS "TO" WS _string WS* "]"
    exclusive_range: "{" WS* _string WS "TO" WS _string WS* "}"
    value_string: _string (string_modifier)?

    _string: (dqstring | sqstring | regstr | uqstring)
    string_modifier: BOOST_MODIFIER | FUZZY_MODIFIER

    BOOST_MODIFIER: "^" /[0-9]+/
    FUZZY_MODIFIER: "~" /[0-9]*/

    SQSTRING.3: "'" ("\\'" | /[^']/)* "'"
    DQSTRING.3: "\"" ("\\\""|/[^"]/)* "\""
    RESTRING.3: "/" ("\\/"|/[^\/]/)* "/"
    !sqstring: SQSTRING
    !dqstring: DQSTRING
    !regstr: RESTRING
    !uqstring: UNQUOTED_STRING

    SPECIAL_CHARACTERS: "+" | "-" | "!" | "(" | ")" | "{" | "}" | "[" | "]" | "^" | "\"" | "~" | "*" | "?" | ":" | "\\" | "&" | "|"
    ESCAPED_SPECIAL_CHARACTERS: "\\" SPECIAL_CHARACTERS
    UNQUOTED_STRING.2: (ESCAPED_SPECIAL_CHARACTERS | /[^+!(){}\[\]^\"\~:\s]/)+

    field: (FIELD)? -> field
    FIELD.2: PATH WS* ":" WS*
    PATH.0: (PATHELEM ".")* PATHELEM
    PATHELEM.0: WORD ("(" PATHINDEX ")")?
    PATHINDEX.0: "-"? (DIGIT+ | UNQUOTED_STRING)
    WORD: LETTER (LETTER | DIGIT | "-" | "_")+
    DIGIT: /[0-9]/
    LETTER: /[a-z]/

    BOOL_AND.1: WS+ ("&&" | "AND") WS+
    BOOL_OR.1: WS+ ("||" | "OR") WS+

    NOT_STR: "NOT" WS+
    EXCLUDED.3: WS* ("-" | "!" | NOT_STR)
    REQUIRED.1: WS* "+"

    LPAR: "(" WS*
    RPAR: WS* ")"

    WS: /[ \t\f\r\n]/+
"""
