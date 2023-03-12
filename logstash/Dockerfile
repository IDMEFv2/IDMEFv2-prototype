ARG LOGSTASH_VERSION

FROM docker.elastic.co/logstash/logstash:${LOGSTASH_VERSION}

RUN logstash-plugin install \
        logstash-codec-cef \
        logstash-filter-json_encode \
        logstash-filter-schema_check \
        logstash-output-snmptrap
