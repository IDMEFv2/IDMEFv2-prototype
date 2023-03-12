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

from collections import defaultdict
import datetime
import re
import itertools
import operator
import pkg_resources
import uuid

from preludecorrelator import utils


VERSION = pkg_resources.get_distribution('prelude-correlator').version
_RegexType = type(re.compile(""))


class IDMEF(object):
    def __init__(self, obj=None, ruleid=None):
        self.obj = obj or {}

        if ruleid:
            self.set("alert.Ref(>>)", "urn:correl:%s" % ruleid)

    def __str__(self):
        return str(self.obj)

    def __setstate__(self, dict):
        self.__dict__.update(dict)

    def _get(self, elem, index, depth):
        if depth == 0:
            return elem[index]
        else:
            return [self._get(i, index, depth - 1) for i in elem]

    def get(self, path, flatten=True, replacement=None):
        ret = self.obj
        depth = 0
        try:
            for elem in path.split("."):
                if "(" in elem:
                    elem, index = elem[:-1].split("(")
                    if index == "*":
                        ret = self._get(ret, elem, depth)
                        depth += 1
                    else:
                        ret = self._get(ret, elem, depth)[int(index)]
                else:
                    ret = self._get(ret, elem, depth)
        except (KeyError, TypeError):
            ret = [] if depth else None

        if ret is None:
            return replacement

        if flatten and depth:
            return utils.flatten(ret)

        return ret

    def set(self, path, value):
        obj = self.obj
        for elem in path.split(".")[:-1]:
            if "(" in elem:
                elem, index = elem[:-1].split("(")
                obj = obj.setdefault(elem, [])
                if index == ">>" or int(index) == len(obj):
                    obj.append({})
                    obj = obj[-1]
                else:
                    obj = obj[int(index)]
            else:
                obj = obj.setdefault(elem, {})

        elem = path.split(".")[-1]
        if "(" in elem:
            elem, index = elem[:-1].split("(")
            obj = obj.setdefault(elem, [])
            if index == ">>" or int(index) == len(obj):
                obj.append(value)
            else:
                obj[int(index)] = value
        else:
            obj[elem] = value

    def getTime(self):
        itime = self.get("alert.StartTime")
        if not itime:
            itime = self.get("alert.CreateTime")

        return itime

    def _match(self, path, needle):
        value = self.get(path)

        if not isinstance(needle, _RegexType):
            ret = value == needle
        else:
            m = needle.search(value or "")
            if not m:
                return False

            ret = m.groups()

        return ret

    def match(self, *args):
        if (len(args) % 2) != 0:
            raise Exception("Invalid number of arguments.")

        ret = []

        i = 0
        while i < len(args):
            r = self._match(args[i], args[i + 1])
            if r is False:
                return None

            elif isinstance(r, tuple):
                ret.extend(r)

            i += 2

        if ret:
            return ret

        return True

    def alert(self):
        global prelude_client

        self.set("alert.ID", str(uuid.uuid4()))
        self.set("alert.CreateTime", str(datetime.datetime.now()).replace(" ", "T"))
        self.set("alert.Analyzer.Name", "Correlator")
        self.set("alert.Analyzer.Type", "Combined")
        self.set("alert.Analyzer.Model", "prelude-correlator %s" % VERSION)

        prelude_client.correlationAlert(self)

    def _getMergeList(self, path, idmef):
        newset = []
        sharedset = []

        curvalues = self.get(path) or ()
        for newidx, newval in enumerate(idmef.get(path) or ()):
            have_match = False
            for curidx, curval in enumerate(curvalues):
                if curval == newval:
                    sharedset.append((curidx, newidx))
                    have_match = True

            if not have_match:
                newset.append((newidx, newval))

        unmodified_set = set(range(len(curvalues)))
        unmodified_set -= set([curidx for curidx, newidx in sharedset])

        return list(unmodified_set), sharedset, newset

    def _mergePort(self, fpath, value):
        strl = []
        has_range = False
        for k, g in itertools.groupby(enumerate(sorted(set(value))), lambda i_x: i_x[0] - i_x[1]):
            ilist = list(map(operator.itemgetter(1), g))
            if len(ilist) > 1:
                has_range = True
                strl.append('%d-%d' % (ilist[0], ilist[-1]))
            else:
                strl.append('%d' % ilist[0])

        if has_range or len(strl) > 1:
            return "service.portlist", ",".join(strl)
        else:
            return "service.port", value[0]

    def _parsePortlist(self, portlist):
        ranges = (x.split("-") for x in portlist.split(","))
        plist = [i for r in ranges for i in range(int(r[0].strip()), int(r[-1].strip()) + 1)]
        return "service.port", plist

    def _defaultMerge(self, fpath, value):
        return fpath, value[0]

    def _getFilteredValue(self, basepath, fpath, reqval, idmef, preproc_func, filtered):
        for idx, value in enumerate(idmef.get(basepath + "." + fpath) or ()):
            if value:
                if value == reqval or reqval is None:
                    idmef.set(basepath + "(%d)." % idx + fpath, None)

            fpath2 = fpath
            if value and preproc_func:
                fpath2, value = preproc_func(value)

            if idx not in filtered:
                filtered[idx] = {}

            if fpath2 not in filtered[idx]:
                filtered[idx][fpath2] = []

            if value:
                filtered[idx][fpath2] += value if isinstance(value, list) else [value]

        return fpath

    def _mergeSet(self, path, idmef, filtered_path=()):
        filtered_new = {}
        filtered_cur = {}
        postproc = {}

        for (fpath, reqval), preproc_func, postproc_func in filtered_path:
            r1 = self._getFilteredValue(path, fpath, reqval, self, preproc_func, filtered_cur)
            r2 = self._getFilteredValue(path, fpath, reqval, idmef, preproc_func, filtered_new)

            postproc[r1 or r2] = postproc_func if postproc_func else self._defaultMerge

        unmodified_set, sharedset, newset = self._getMergeList(path, idmef)
        for idx, value in newset:
            self.set(path + "(>>)", value)
            for fpath, value in filtered_new.get(idx, {}).items():
                if value and fpath in postproc:
                    fpath, value = postproc[fpath](fpath, value)

                if value:
                    self.set(path + "(-1)." + fpath, value)

        for idx in unmodified_set:
            for fpath, value in filtered_cur.get(idx, {}).items():
                if value and fpath in postproc:
                    fpath, value = postproc[fpath](fpath, value)

                if value:
                    self.set(path + "(%d)." % idx + fpath, value)

        for idx, nidx in sharedset:
            common = defaultdict(list)
            for a, b in list(filtered_new.get(nidx, {}).items()) + list(filtered_cur.get(idx, {}).items()):
                common[a] += b

            for fpath, value in common.items():
                if value and fpath in postproc:
                    fpath, value = postproc[fpath](fpath, value)

                if value:
                    self.set(path + "(%d)." % idx + fpath, value)

        for idx, values in filtered_new.items():
            for fpath, value in values.items():
                if value and fpath in postproc:
                    fpath, value = postproc[fpath](fpath, value)

                if value:
                    self.set(path + "(%d)." % (idx) + fpath, value)

    def addAlertReference(self, idmef, auto_set_detect_time=True):
        if auto_set_detect_time is True:
            intime = idmef.getTime()
            curtime = self.getTime()
            if not curtime or intime < curtime:
                self.set("alert.StartTime", intime)

        self._mergeSet("alert.Source", idmef)
        self._mergeSet("alert.Target", idmef)

        self.set("alert.CorrelID(>>)", idmef.get("alert.ID"))

        path, value = env.prelude_client.get_grouping(idmef)
        if path:
            self.set(path, value)


def set_prelude_client(client):
    global prelude_client
    prelude_client = client
