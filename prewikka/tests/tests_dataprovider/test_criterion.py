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
Tests for `prewikka.dataprovider.Criterion()`.
"""

import copy

from prewikka.dataprovider import Criterion, CriterionOperator


def test_criterion_to_string():
    """
    Test `prewikka.dataprovider.Criterion.to_string()` method.
    """
    # empty criterion
    criterion = Criterion()

    assert criterion.to_string() == ''

    # simple criterion
    criterion = Criterion('alert.messageid', '=', 'fakemessageid')

    assert criterion.to_string() == "alert.messageid = 'fakemessageid'"

    criterion = Criterion('alert.messageid', '==', 'fakemessageid')

    assert criterion.to_string() == "alert.messageid = 'fakemessageid'"

    criterion = Criterion('alert.messageid', '!=', 'fakemessageid')

    assert criterion.to_string() == "alert.messageid != 'fakemessageid'"

    criterion = Criterion('alert.messageid', '>', 'fakemessageid')

    assert criterion.to_string() == "alert.messageid > 'fakemessageid'"

    criterion = Criterion('alert.messageid', '>=', 'fakemessageid')

    assert criterion.to_string() == "alert.messageid >= 'fakemessageid'"

    criterion = Criterion('alert.messageid', '<', 'fakemessageid')

    assert criterion.to_string() == "alert.messageid < 'fakemessageid'"

    criterion = Criterion('alert.messageid', '<=', 'fakemessageid')

    assert criterion.to_string() == "alert.messageid <= 'fakemessageid'"

    criterion = Criterion('alert.messageid', '<>*', 'fakemessageid')

    assert criterion.to_string() == "alert.messageid <>* 'fakemessageid'"

    # combined criterion
    criterion_1 = Criterion('alert.messageid', '=', 'fakemessageid1')
    criterion_2 = Criterion('alert.messageid', '=', 'fakemessageid2')
    criterion = Criterion(criterion_1, '||', criterion_2)

    assert criterion.to_string() == "alert.messageid = 'fakemessageid1' || alert.messageid = 'fakemessageid2'"

    criterion = Criterion(criterion_1, '&&', criterion_2)

    assert criterion.to_string() == "alert.messageid = 'fakemessageid1' && alert.messageid = 'fakemessageid2'"


def test_criterion_get_path():
    """
    Test `prewikka.dataprovider.Criterion.get_path()` method.
    """
    # empty criterion
    criterion = Criterion()
    results = set()

    assert criterion.get_paths() == results

    # simple criterion
    criterion = Criterion('alert.messageid', '=', 'fakemessageid')
    results = set()
    results.add('alert.messageid')

    assert criterion.get_paths() == results

    # combined criterion (with || operator)
    criterion_1 = Criterion('alert.messageid', '=', 'fakemessageid1')
    criterion_2 = Criterion('heartbeat.messageid', '=', 'fakemessageid2')
    criterion = Criterion(criterion_1, '||', criterion_2)
    results = set()
    results.add('alert.messageid')
    results.add('heartbeat.messageid')

    assert criterion.get_paths() == results

    # combined criterion (with && operator)
    criterion_1 = Criterion('alert.messageid', '=', 'fakemessageid1')
    criterion_2 = Criterion('heartbeat.messageid', '=', 'fakemessageid2')
    criterion = Criterion(criterion_1, '&&', criterion_2)
    results = set()
    results.add('alert.messageid')
    results.add('heartbeat.messageid')

    assert criterion.get_paths() == results


def test_criterion_flatten():
    """
    Test `prewikka.dataprovider.Criterion.flatten()` method.
    """
    criterion_1 = Criterion('alert.messageid', '=', 'fakemessageid1')
    criterion_2 = Criterion('alert.messageid', '=', 'fakemessageid2')
    criterion_3 = Criterion('alert.messageid', '=', 'fakemessageid3')
    criterion_4 = Criterion('alert.messageid', '=', 'fakemessageid4')
    criterion = ((criterion_1 & criterion_2) & criterion_3) | criterion_4
    flattened = criterion.flatten()

    assert flattened.operator == CriterionOperator.OR
    assert len(flattened.operands) == 2
    assert flattened.operands[0].operator == CriterionOperator.AND
    assert flattened.operands[0].operands == [criterion_1, criterion_2, criterion_3]
    assert flattened.operands[1] == criterion_4

    criterion = Criterion(None, '!', Criterion(None, '!', Criterion(None, '!', criterion_1)))
    flattened = criterion.flatten()

    assert flattened.operator == CriterionOperator.NOT
    assert len(flattened.operands) == 1
    assert flattened.operands[0] == criterion_1


def test_criterion_operations():
    """
    Test `prewikka.dataprovider.Criterion` operations.
    """
    criterion_0 = Criterion()
    criterion_1 = Criterion('alert.messageid', '=', 'fakemessageid1')
    criterion_2 = Criterion('heartbeat.messageid', '=', 'fakemessageid2')

    # __str__()
    assert str(criterion_1) == criterion_1.to_string()

    # __bool__() / __nonzero__()
    assert not criterion_0
    assert criterion_1

    # __copy__()
    criterion_copy = copy.copy(criterion_1)

    assert criterion_copy != criterion_1
    assert criterion_copy.to_string() == criterion_1.to_string()

    # __json__()
    assert criterion_1.__json__() == {'left': 'alert.messageid', 'operator': CriterionOperator.EQUAL, 'right': 'fakemessageid1'}

    # __iadd__()
    criterion_iadd = copy.copy(criterion_1)
    criterion_iadd += criterion_2

    assert criterion_iadd.to_string() == Criterion(criterion_1, '&&', criterion_2).to_string()

    # __ior__()
    criterion_ior = copy.copy(criterion_1)
    criterion_ior |= criterion_2

    assert criterion_ior.to_string() == Criterion(criterion_1, '||', criterion_2).to_string()

    # __iand__()
    criterion_iand = copy.copy(criterion_1)
    criterion_iand &= criterion_2

    assert criterion_iand.to_string() == Criterion(criterion_1, '&&', criterion_2).to_string()

    # __add__()
    criterion_add = criterion_1 + criterion_2

    assert criterion_add.to_string() == Criterion(criterion_1, '&&', criterion_2).to_string()

    # __or__()
    criterion_or = criterion_1 | criterion_2

    assert criterion_or.to_string() == Criterion(criterion_1, '||', criterion_2).to_string()

    # __and__()
    criterion_and = criterion_1 & criterion_2

    assert criterion_and.to_string() == Criterion(criterion_1, '&&', criterion_2).to_string()
