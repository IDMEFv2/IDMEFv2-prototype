# -*- coding: utf-8 -*-
# Copyright (C) 2015-2021 CS GROUP - France. All Rights Reserved.
# Author: Sélim Menouar <selim.menouar@c-s.fr>
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

import datetime
import dateutil.parser
import re
import requests
from collections import OrderedDict

from prewikka import dataprovider, error, hookmanager
from prewikka.dataprovider import CriterionOperator, utils
from prewikka.dataprovider.parsers import lucene
from prewikka.utils import json, AttrObj, CachingIterator
from prewikka.utils.timeutil import timezone, get_timestamp_from_datetime


_AGGREGATION_FUNC = ("count", "count_distinct", "min", "max", "avg", "sum")

_EXTRACT_MAP = {
    "year": "year",
    "month": "month",
    "mday": "day",
    "hour": "hour",
    "min": "minute",
    "sec": "second"
}

_TIME_GROUPBY = ("year", "quarter", "month", "week", "day", "hour", "minute", "second", "timestamp")


class ReconstructTransformer(lucene.ReconstructTransformer):
    def __init__(self, mapping, type=None):
        self._mapping = mapping
        self._type = type

    def field(self, f):
        if not f:
            return ""

        return self._mapping.to_es(f[0].replace(" ", "")[:-1]) + ":"

    # This is used to deanonymize the value
    def _value_string(self, s, field=None):
        # For a given value of "my value"
        # s[1] = "my value"
        # s[1].value = my value

        orig = s[1].value
        tpl = ["%s.%s" % (self._type, field[:-1]) if field else None, orig]
        list(hookmanager.trigger("HOOK_DATAPROVIDER_VALUE_WRITE", tpl))

        if tpl[1] != orig:
            return s[1].replace(s[1].value, tpl[1])

        return text_type(s[1])


class ElasticsearchPlugin(dataprovider.DataProviderBackend):
    def __init__(self):
        # Do not call the parent's __init__ here
        self._instances = {}

        for conf in env.config.elasticsearch:
            if conf.get("es_type") != self.type:
                continue

            name = conf.get_instance_name()
            if not name:
                raise error.PrewikkaUserError(N_("Invalid configuration"),
                                              N_("Elasticsearch instance must be named"))

            self._instances[name] = ElasticsearchInstance(name, conf)
            if not self._default_instance:
                self._default_instance = self._instances[name]

        if not self._instances:
            raise error.PrewikkaUserError(N_("Missing configuration"),
                                          N_("Could not find a valid configuration for Elasticsearch %s type.", self.type))


class ElasticsearchInstance(dataprovider.DataProviderInstance):
    TYPE_OPERATOR_MAPPING = {
        text_type: ("=", "=*", "!=", "!=*", "~", "~*", "!~", "!~*", "<>", "<>*", "!<>", "!<>*"),
        datetime.datetime: ("<", ">", "<=", ">="),
        None: ("=", "!=", "<", ">", "<=", ">=")
    }

    def __init__(self, name, config):
        self.type = config.es_type
        self._client = ElasticsearchClient(name, config)

    def get_values(self, paths, criteria, distinct, limit, offset, highlight=None):
        env.request.user.check("%s_VIEW" % self.type.upper())

        if limit < 0:
            # cannot be more than index.max_result_window, which default to 10000
            limit = 10000

        results = self._client.query(paths, criteria, limit, offset, highlight)

        return results.api_results

    def get(self, criteria, paths, limit, offset):
        return self.get_values([], criteria, False, limit, offset)


class ElasticsearchClient(object):
    def __init__(self, name, conf):
        self._type = conf.es_type
        self._url = conf.es_url.rstrip("/")
        self._host = self._url.rsplit("/", 1)[0]
        self._user = conf.get("es_user")
        self._password = conf.get("es_pass", "")
        self._cert = conf.get("es_cert")
        self._privkey = conf.get("es_privkey")
        self._cacert = conf.get("es_cacert")
        self._session = requests.Session()
        self._session.headers["content-type"] = "application/json"

        # Check if Elasticsearch instance is available
        req = self._request(self._host, method="GET").json()
        self._version = tuple(int(i) for i in req["version"]["number"].split("."))
        if self._version < (5,):
            raise error.PrewikkaUserError(N_("Invalid configuration"),
                                          N_("Elasticsearch version %s is not supported.", req["version"]["number"]))

        self._mapping = ElasticsearchMap(self._type, conf, self.get_mapping())

    def request(self, path, data="", method="POST", with_index=True, **kwargs):
        """ Make a request and return the result """
        return self._request((self._url if with_index else self._host) + path, data, method, **kwargs)

    def _request(self, url, data="", method="POST", **kwargs):
        try:
            if self._user:
                kwargs['auth'] = (self._user, self._password)
            if self._cacert:
                kwargs['verify'] = self._cacert
            if self._cert:
                if self._privkey:
                    kwargs['cert'] = (self._cert, self._privkey)
                else:
                    kwargs['cert'] = self._cert

            result = self._session.request(method, url, data=data, **kwargs)
        except requests.exceptions.RequestException as err:
            raise error.PrewikkaUserError(N_("Request error"), err)

        try:
            json_result = result.json()
        except ValueError as err:
            raise error.PrewikkaUserError(N_("Request error"), err)

        if result.status_code == 200:
            # When searching multiple indices, some can fail returning
            # results. We subtract the total number of shards by the
            # skipped and failed ones, and if this result is 0, then
            # we raise an error.
            # When the internal ticket #3842 will be answered and closed,
            # review the purpose of this code.
            if not url.endswith("/_search"):
                return result

            shards = json_result["_shards"]

            if shards["total"] - shards.get("skipped", 0) - shards["failed"] == 0:
                err = shards["failures"][0]["reason"]["reason"]

                # FIXME #3733 Remove when cursors are implemented?
                if "Result window is too large" in err:
                    err = N_("Cannot further browse results. Please use a more specific filter.")

                raise error.PrewikkaUserError(N_("Request error"), err)

            return result

        err = N_("Request error with HTTP code %d.", result.status_code)
        if result.status_code == 400:  # Bad ES request
            r = json_result.get("error", {})
            try:
                parse_except = r["failed_shards"][0]['reason']['caused_by']['type'] == "parse_exception"
            except KeyError:
                parse_except = False

            r = r.get("root_cause")
            if parse_except:
                err = N_("Malformed query.")
            elif r and "Result window is too large" in r[0]["reason"]:
                # FIXME #3733 Remove when cursors are implemented?
                err = N_("Cannot further browse results. Please use a more specific filter.")
            elif r:
                err = N_("Request error with HTTP code %d. Reason: %s", (result.status_code, r[0]["reason"]))
            else:
                err = N_("Request error with HTTP code %d. Unknown reason", result.status_code)

        raise error.PrewikkaUserError(N_("Request error"), err)

    def query(self, path, criteria, limit=50, offset=0, highlight=None):
        search = ElasticsearchQuery(self._type, self._version, self._mapping, path, criteria, limit, offset, highlight)
        results = self.request("/_search", search.get_json_query())

        return ElasticsearchResult(self._type, self._mapping, results.json(), search, limit)

    def get_mapping(self, root=None, mapping=None, prefix=""):
        if mapping is None:
            mapping = {}

        if root is None:
            try:
                req = next(iter(self.request('/', method="GET").json().values()))
                if self._version < (7,):
                    root = next(iter(req["mappings"].values()))["properties"]
                else:
                    root = req["mappings"]["properties"]
            except (IndexError, KeyError):
                raise error.PrewikkaUserError(N_("Invalid configuration"),
                                              N_("The specified Elasticsearch index does not exist"))

        if prefix:
            prefix += "."

        for key, value in root.items():
            mapping[prefix + key] = AttrObj(type=value.get("type"),
                                            keyword=value.get("type") == "keyword")

            if "fields" in value:
                self.get_mapping(value["fields"], mapping, prefix + key)
            elif "properties" in value:
                self.get_mapping(value["properties"], mapping, prefix + key)

        return mapping


class ElasticsearchQuery(object):
    # Case depends on Elasticsearch configuration, we can not handle this here for now
    # Default configuration is to lowercase
    OPERATOR_MAP = {
        CriterionOperator.EQUAL: ("must", "term"),
        CriterionOperator.EQUAL_NOCASE: ("must", "term"),
        CriterionOperator.NOT_EQUAL: ("must_not", "term"),
        CriterionOperator.NOT_EQUAL_NOCASE: ("must_not", "term"),
        CriterionOperator.SUBSTR: ("must", "contains"),
        CriterionOperator.SUBSTR_NOCASE: ("must", "contains"),
        CriterionOperator.NOT_SUBSTR: ("must_not", "contains"),
        CriterionOperator.NOT_SUBSTR_NOCASE: ("must_not", "contains"),
        CriterionOperator.REGEX: ("must", "regexp"),
        CriterionOperator.REGEX_NOCASE: ("must", "regexp"),
        CriterionOperator.NOT_REGEX: ("must_not", "regexp"),
        CriterionOperator.NOT_REGEX_NOCASE: ("must_not", "regexp"),
    }

    def __init__(self, type, version, mapping, path, criteria, limit=50, offset=0, highlight=None):
        self._type = type
        self._version = version
        self._mapping = mapping
        self.path = path
        self.criteria = criteria
        self.limit = limit
        self.offset = offset
        self._final_order = []
        self.highlight = highlight
        self._time_field = env.dataprovider.format_path("{time_field}", type=type)
        default_field = self._mapping.to_es("default_field")

        if default_field == 'default_field':
            default_field = 'message'

        self._query_string = {
            "query_string": {
                "default_field": default_field,
                "query": "",
                "default_operator": "AND",
                "analyze_wildcard": True
            }
        }

        self._query = {
            "size": limit,
            "from": offset,
            "sort": [],
            "query": self._init_query_criteria(),
            "aggs": {},
            "highlight": dict(self.highlight) if self.highlight else {},
            "track_total_hits": True,
        }

        self.extract_list = []
        self._set_paths(self.path)
        if self.criteria:
            self._set_criteria(self.criteria)

    def _init_query_criteria(self):
        return {
            "bool": {
                "must": [],
                "must_not": [],
                "filter": [],
                "should": []
            }
        }

    def get_query(self):
        return self._query

    def get_json_query(self):
        return json.dumps(self._query)

    def _is_groupby_query(self, paths):
        group_by = []
        for idx, p in enumerate(paths):
            path = p.get_path()
            field = AttrObj(field=path.path.split(".", 1)[-1] if path else None, order=None)

            if path and self.highlight and "fields" not in self.highlight:
                self._query['highlight'].setdefault('fields', {})[self._mapping.to_es(path.name)] = {}

            final_order = None
            for cmd in p.commands:
                if cmd == "group_by":
                    if p.extract:
                        field.field = _EXTRACT_MAP.get(p.extract)

                    if field in group_by:
                        index = group_by.index(field)
                    else:
                        index = len(group_by)
                        group_by.append(field)

                    final_order = (idx, index)

                elif cmd == "order_desc":
                    field.order = "desc"

                elif cmd == "order_asc":
                    field.order = "asc"

            if final_order:  # cmd : groupby
                self._final_order.append(AttrObj(idx=final_order[0], index=final_order[1], order=field.order))

            if field.field and field.order and (field.field not in _TIME_GROUPBY or field.field == self._time_field):
                self._add_order(field)

        return group_by

    def _set_paths_func(self, paths, group_by):
        query, index, nested = self._get_aggs_last_index()
        initial_index = index
        typ_last_agg = next(iter(query.keys()))

        for idx, p in enumerate(paths):
            path = p.get_path()
            field = path.name if path else None
            if not (p.object.is_function and p.object.name in _AGGREGATION_FUNC):
                continue

            self._query["size"] = 0
            if not field:
                if not group_by:
                    continue

                field = group_by[-1].field

            order = None
            for cmd in p.commands:
                if cmd == "order_desc":
                    order = "desc"

                elif cmd == "order_asc":
                    order = "asc"

            if field in _TIME_GROUPBY:
                self._final_order.append(AttrObj(idx=idx, index=-1, order=order))
                continue

            if getattr(p.object.args[0], "name", None) == "distinct":
                name = "count_distinct"
            else:
                name = p.object.name

            aggs = self._format_aggregate(field, name, index, nested=nested)

            item = list(filter(lambda x: x[1] == aggs["internal_%d" % index]["aggs"], query.setdefault("aggs", {}).items()))
            if item:
                self._final_order.append(AttrObj(idx=idx, index=int(item[0][0][9:]) - 1, order=order))
                continue

            self._final_order.append(AttrObj(idx=idx, index=index - 1, order=order))
            query.setdefault("aggs", {})["internal_%d" % index] = aggs["internal_%d" % index]
            if initial_index != 1:
                query[typ_last_agg].setdefault("order", {})["internal_%d" % index] = order or "desc"
            index = index + 1

    def _set_paths(self, paths):
        group_by = self._is_groupby_query(paths)
        if group_by:
            # WARNING: Elasticsearch can't ensure exact results when using multiple
            # aggregations (i.e. sub-buckets) and sorting by count.
            # We might want to increase the limit here (like x10) to reduce
            # the imprecision.
            self._query["size"] = 0
            for g in group_by:
                self._add_aggregate(g)

        self._set_paths_func(paths, group_by)
        self._final_order = sorted(self._final_order, key=lambda x: x.idx)

        if group_by and self.offset:
            self._add_offset()

    def _set_criteria_op(self, typ, criteria, query):
        for term in (criteria.left, criteria.right):
            if not term:
                continue

            ret = self._set_criteria(term, self._init_query_criteria())
            if ret:
                query["bool"][typ].append(ret)

        return query

    def _set_criteria(self, criteria, query=None):
        if query is None:
            query = self._query["query"]

        if criteria.operator == CriterionOperator.NOT:
            return self._set_criteria_op("must_not", criteria, query)

        if criteria.operator == CriterionOperator.AND:
            return self._set_criteria_op("must", criteria, query)

        if criteria.operator == CriterionOperator.OR:
            return self._set_criteria_op("should", criteria, query)

        field = criteria.left.split(".", 1)[-1]
        if field == "_raw_query":
            self._add_raw_query(criteria.right)

        elif field == self._time_field:
            self._add_time_to_query(criteria.right, criteria.operator)

        else:
            op = self.OPERATOR_MAP.get(criteria.operator, None)
            if op is None:
                raise error.PrewikkaUserError(N_("Elasticsearch database operator error"),
                                              N_("The operator '%s' that you try to use is not supported by Prelude for the field '%s'." % (criteria.operator, field)))

            ci = criteria.operator.case_insensitive
            right = criteria.right.lower() if ci and self._version < (7, 10) else criteria.right
            if right is None:
                op = ("must" if criteria.operator.negated else "must_not", "exists")

            query["bool"][op[0]].append(getattr(self, "_%s_filter" % op[1])(field, right, ci=ci))
            nested_query = self._add_nested(field)

            if not nested_query:
                return query

            nested_query["nested"]["query"] = query
            return nested_query

    def _add_nested(self, field):
        es_field_name = self._mapping.to_es(field, nested=True)
        elem = es_field_name.split("(*).")
        if len(elem) == 1:
            return {}

        return {
            "nested": {
                "path": ".".join(elem[:-1]),
            }
        }

    def _add_raw_query(self, query):
        if self._query_string["query_string"]["query"]:
            raise error.PrewikkaError(N_("Only one _raw_query path can be specified for the selection"), N_("Elasticsearch database path selection error"))

        self._query_string["query_string"]["query"] = lucene.parse(query, transformer=ReconstructTransformer(self._mapping, type=self._type))
        self._query["query"]["bool"]["must"].append(self._query_string)

    # Don't search with a timestamp, Elasticsearch does not apply
    # the timezone conversion on a timestamp, resulting in incorrect return values
    def _add_time_to_query(self, date, operator):
        if not isinstance(date, datetime.datetime):
            # This can happen when the criterion is parsed from a string (e.g. webservice),
            # or JSON-deserialized (e.g. replay by criteria)
            date = dateutil.parser.parse(date)

        if not date.tzinfo:
            date = env.request.user.timezone.localize(date)

        utc_time = self._mapping.format_datetime(date.astimezone(dateutil.tz.tzutc()))
        operator = self._mapping.to_operator(operator.name)
        self._query["query"]["bool"]["filter"].append(self._range_filter(self._time_field, operator, utc_time))

    def _add_order(self, field):
        if self._mapping.to_es_keyword(field.field) and field.field != 'raw_message':
            order_filter = {"order": field.order}
            order_filter.update(self._add_nested(field.field))
            if order_filter not in self._query["sort"]:
                self._query["sort"].append({self._mapping.to_es_keyword(field.field): order_filter})

    def _add_aggregate(self, field):
        query, index, nested = self._get_aggs_last_index()
        query["aggs"] = self._format_aggregate(field.field, "terms", index, field.order, nested)

    def _add_offset(self):
        self._query["aggs"]["internal_1"]["aggs"]["bucket_truncate"] = {
            "bucket_sort": {
                "from": self.offset,
                "size": self.limit
            }
        }

    def _format_aggregate(self, field, func, index=1, order=None, nested=None):
        if field in _TIME_GROUPBY:
            func = "time"

        # FIXME: we should handle nesting in nesting
        if not nested:
            nested_agg = self._add_nested(field)
            if nested_agg:
                ret = {"internal_%d" % index: {"aggs": {"internal_nested_%d" % index: getattr(self, "_aggs_%s" % func)(field, order)}}}
            else:
                ret = {"internal_%d" % index: getattr(self, "_aggs_%s" % func)(field, order)}

            ret["internal_%d" % index].update(nested_agg)
        else:
            ret = {"internal_%d" % index: getattr(self, "_aggs_%s" % func)(field, order)}

        return ret

    def _get_aggs_last_index(self, query=None, index=1, nested=None):
        if not query:
            query = self._query

        aggs_k = query.get("aggs", {}).keys()
        if aggs_k:
            q = query["aggs"][next(iter(aggs_k))]
            if "nested" in query:
                return self._get_aggs_last_index(q, index, query["nested"]["path"])
            else:
                return self._get_aggs_last_index(q, index + 1, nested)
        else:
            return [query, index, nested]

    def _range_filter(self, field, operator, value, ci=False):
        return {
            "range": {
                self._mapping.to_es(field): {
                    operator: value
                }
            }
        }

    def _match_filter(self, field, value, ci=False):
        return {
            "match": {self._mapping.to_es(field): value}
        }

    def _exists_filter(self, field, value=None, ci=False):
        return {
            "exists": {"field": self._mapping.to_es(field)}
        }

    def _term_filter(self, field, value, ci=False):
        return {
            "term": {self._mapping.to_es_keyword(field): value}
        }

    def _contains_filter(self, field, value, ci=False):
        crit = {"value": "*%s*" % value}
        if ci and self._version >= (7, 10):
            crit["case_insensitive"] = True

        return {
            "wildcard": {self._mapping.to_es_keyword(field): crit}
        }

    def _regexp_filter(self, field, value, ci=False):
        crit = {"value": value}
        if ci and self._version >= (7, 10):
            crit["case_insensitive"] = True

        return {
            "regexp": {self._mapping.to_es_keyword(field): crit}
        }

    def _aggs_terms(self, field, order):
        return {
            "terms": {
                "field": self._mapping.to_es_keyword(field),
                "size": 10000,
                "order": {
                    "_count": order or "desc"
                }
            }
        }

    def _aggs_time(self, field, order):
        if field == self._time_field:
            field = "1s"

        m = {
            'year': 'yyyy',
            'month': 'MM',
            'day': 'dd',
            'hour': 'HH',
            'minute': 'mm',
            'second': 'ss',
            '1s': 'yyyy-MM-dd HH:mm:ss'
        }

        return self._aggs_histogram(self._mapping.to_es(self._time_field), field, m[field], order)

    def _aggs_histogram(self, field, interval, form, order):
        return {
            "date_histogram": {
                "field": field,
                "interval": interval,
                "format": form,
                "time_zone": env.request.user.timezone.zone,
                "order": {"_key": order or "asc"},
                "min_doc_count": 0
            }
        }

    def _aggs_count(self, field, order):
        return {
            "value_count": {
                "field": self._mapping.to_es_keyword(field)
            }
        }

    def _aggs_count_distinct(self, field, order):
        return {
            "cardinality": {
                "field": self._mapping.to_es_keyword(field)
            }
        }

    def _aggs_max(self, field, order):
        return {
            "max": {
                "field": self._mapping.to_es_keyword(field)
            }
        }

    def _aggs_min(self, field, order):
        return {
            "min": {
                "field": self._mapping.to_es_keyword(field)
            }
        }

    def _aggs_avg(self, field, order):
        return {
            "avg": {
                "field": self._mapping.to_es_keyword(field)
            }
        }

    def _aggs_sum(self, field, order):
        return {
            "sum": {
                "field": self._mapping.to_es_keyword(field)
            }
        }


class ElasticsearchResult(object):
    def __init__(self, type, mapping, result, query, limit):
        self._type = type
        self._mapping = mapping
        self._result = result
        self._query = query
        self._limit = limit

        self.total_result = result.get("hits", {}).get("total", 0)
        if isinstance(self.total_result, dict):
            # For Elasticsearch >= 7
            self.total_result = self.total_result["value"]

        if query.path:
            self.api_results = dataprovider.QueryResults(self._get_rows())
        else:
            self.api_results = CachingIterator([dataprovider.ResultObject({self._type: row}) for row in self._get_rows()])

        self.api_results.total = self.total_result

    def _get_rows(self):
        rows = []
        if self._query._query["size"] == 0:
            rows = self._aggregations_to_rows(self._manage_aggregations())
            for obj in reversed(self._query._final_order):
                if obj.order:
                    # Multiple sorts work here because sorting is stable
                    rows.sort(key=lambda x: x[obj.idx], reverse=obj.order == "desc")

            # Truncate the results since Elasticsearch limits are per bucket
            rows = rows[:self._limit]

            # When aggregating, Elasticsearch set ["hits"]["total"] to the sum of all
            # values and not the number of aggregations
            self.total_result = 0
        else:
            for hit in self._result.get("hits", {}).get("hits", []):
                # Concat all the data in the root section and the _source section
                hit.update(hit.pop("_source", {}))
                rows.append(self._get_row(hit))

        return rows

    def _ordered_row(self, keys):
        ret = []
        if not self._query._final_order:
            return keys

        for obj in self._query._final_order:
            if obj.index < len(keys):
                ret.append(keys[obj.index])
            else:
                ret.append('0')

        return ret

    @staticmethod
    def _is_internal(x):
        return isinstance(x, text_type) and x.startswith('internal_')

    def _aggregations_to_rows(self, result, rows=None, keys=None, depth=1):
        if result is None:
            return []

        if rows is None:
            rows = []

        if keys is None:
            keys = []

        values = []
        last_level = False
        if isinstance(result, dict):
            last_level = not bool([x for x in result if not self._is_internal(x)])
            values = result.values()
        else:
            last_level = True
            values = [result]

        if last_level:
            rows.append(self._ordered_row(keys + values))
            return rows

        for key in result:
            if not self._is_internal(key):
                self._aggregations_to_rows(result[key], rows, keys + [key], depth+1)

        return rows

    def _manage_aggregations(self, aggs=None, index=1):
        # If the query is just "count(1)"
        if aggs is None and "aggregations" not in self._result:
            return self.total_result

        if aggs is None:
            aggs = self._result["aggregations"]

        if "buckets" in aggs.get("internal_%d" % index, {}).get("internal_nested_%d" % index, {}):
            return self._manage_aggregations_buckets(aggs["internal_%d" % index]["internal_nested_%d" % index]["buckets"], index + 1)

        if "buckets" in aggs.get("internal_%d" % index, {}):
            return self._manage_aggregations_buckets(aggs["internal_%d" % index]["buckets"], index + 1)

        if aggs.get("internal_%d" % (index+1)) is None:
            return aggs["internal_%d" % index]["value"]

        result = OrderedDict()
        while True:
            agg = aggs.get("internal_%d" % index)
            if not agg:
                break

            if "value" in agg:
                result["internal_%d" % index] = agg["value"]

            index = index + 1

        return result or None

    def _manage_aggregations_buckets(self, buckets, index):
        result = OrderedDict()
        for bucket in buckets:
            key = bucket.get("key_as_string") or bucket.get("key", "")
            next_agg_idx = "internal_%d" % index
            if bucket.get(next_agg_idx):
                result[key] = self._manage_aggregations(bucket, index)
            else:
                result[key] = result.get(key, 0) + bucket.get("doc_count", 0)

        return result or None

    def _get_groupby_from_path(self, path):
        if "group_by" not in path.commands:
            return None

        if path.extract:
            return _EXTRACT_MAP.get(path.extract)

        return path.object.name

    def _get_subfield_value(self, fullpath, result):
        # result can be like
        # { 'key1' : { 'key2' : { 'key3' : value }}} # Standard case
        # or
        # { 'key1.key2.key3' : value } # Highlight case
        # and fullpath is like
        # key1.key2.key3

        res = result
        for i, path in enumerate(fullpath.split('.')):
            if not path:
                break

            # FIXME: handle all possible indices
            value = res.get(path.replace('(*)', '').replace('(0)', ''))

            if path.endswith('(0)') and isinstance(value, list):
                res = value[0]
            elif isinstance(value, list):
                return [self._get_subfield_value('.'.join(fullpath.split('.')[i+1:]), r) for r in value]
            elif value is None:
                return result.get(fullpath)
            else:
                res = value

        return res

    def _get_field_value(self, selection, result):
        if selection.object.is_function and selection.object.name == "count":
            return result["count"]

        field_name = selection.object.path.split(".", 1)[-1]
        if field_name not in _TIME_GROUPBY:
            es_field_name = self._mapping.to_es(field_name)
            ret = self._get_subfield_value(es_field_name, result)

            if ret and self._query.highlight and es_field_name in result.get('highlight', {}):
                ret = self._get_subfield_value(es_field_name, result.get("highlight", {}))[0]

            if field_name == "raw_message" and ret is None:
                es_field_name = self._mapping.to_es("timestamp")
                ret = self._get_subfield_value(es_field_name, result)
                if not ret:
                    return None

                time_log = dateutil.parser.parse(ret)

                return "%s %s %s %s" % (
                    time_log.strftime('%b %d %H:%M:%S'),
                    result.get(self._mapping.to_es("host")),
                    result.get(self._mapping.to_es("program")),
                    result.get(self._mapping.to_es("message"))
                )

            return ret

        groupby = self._get_groupby_from_path(selection)
        if groupby:
            value = dateutil.parser.parse(result[groupby])
        else:
            es_field_name = self._mapping.to_es("timestamp")
            ret = self._get_subfield_value(es_field_name, result)
            if not ret:
                return None

            value = dateutil.parser.parse(ret)

        if selection.object.is_function and selection.object.name == "timezone":
            value = utils.apply_timezone(value, timezone(selection.object.args[0]))

        if selection.extract:
            value = utils.extract_from_date(value, selection.extract)

        return value

    def _get_row(self, result):
        if not self._query.path:
            return self._apply_mapping(result)

        return [self._get_field_value(i, result) for i in self._query.path]

    def _apply_mapping(self, result, root=""):
        if isinstance(result, list):
            return [self._apply_mapping(r, root) for r in result]

        if not isinstance(result, dict):
            return result

        ret = {}
        for k, v in result.items():
            field = self._mapping.from_es(root + k)
            if field:
                ret[field.split(".")[-1]] = self._apply_mapping(v, root + k + ".")

        return ret


class ElasticsearchMap(object):
    _OPERATOR = {"<=": "lte", ">=": "gte", "<": "lt", ">": "gt"}
    _TYPES = {
        datetime.datetime: ("date",),
        float: ("double", "float", "half_float", "scaled_float"),
        int: ("byte", "integer", "short", "long"),
        text_type: ("keyword", "text"),
    }
    _REVERSED_TYPES = {value: key for key, values in _TYPES.items() for value in values}

    def __init__(self, name, conf, fields):
        self.name = name
        self.time_format = conf.get("es_timeformat")

        if self.time_format:
            try:
                self.format_datetime(datetime.datetime.utcnow())
            except ValueError as err:
                raise error.PrewikkaUserError(N_("Invalid configuration"), err)

        self._mapping, self._group_mapping = self._get_mapping(conf)
        self._reverse_mapping = {}
        paths = env.dataprovider.get_paths(name)

        for field, es_field in self._mapping.items():
            elem = es_field.replace("(*)", "").split(".")
            for i, _ in enumerate(elem, 1):
                self._reverse_mapping[".".join(elem[:i])] = ".".join(field.split(".")[:i])

            if field in paths or field == "default_field":
                continue

            es_type = fields[es_field].type if es_field in fields else None
            type_ = self._REVERSED_TYPES.get(es_type, text_type)
            env.dataprovider.register_path("%s.%s" % (name, field), type_)

    def format_datetime(self, dt):
        if not self.time_format:
            return dt.isoformat()

        if self.time_format == '@':
            return get_timestamp_from_datetime(dt)

        return dt.strftime(self.time_format)

    def _get_mapping(self, conf):
        mapping = {}
        group_mapping = {}
        key_regex = re.compile(r'\w[\w\-]*')
        for key, value in conf.items():
            if not key_regex.match(key):
                raise error.PrewikkaUserError(N_("Configuration error"),
                                              N_("In your Elasticsearch instance, fields mapping is not well configured."))

            key = key.lower()

            if key.startswith('es_'):
                continue

            value = value.split(", ", 1)
            if len(value) > 1:
                group_mapping[key] = value[1].strip()

            mapping[key] = value[0].strip()

        return mapping, group_mapping

    def to_es(self, field, nested=False):
        if field.endswith(".exact"):
            return self.to_es_keyword(field[:-6], nested=nested)

        ret = self._mapping.get(field, field)
        return ret if nested else ret.replace("(*)", "")

    def to_es_keyword(self, field, nested=False):
        ret = self._group_mapping.get(field, self.to_es(field))
        return ret if nested else ret.replace("(*)", "")

    def to_operator(self, field):
        return self._OPERATOR.get(field, field)

    def from_es(self, field):
        return self._reverse_mapping.get(field)
