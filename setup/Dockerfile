ARG ELASTIC_VERSION

FROM docker.elastic.co/elasticsearch/elasticsearch:${ELASTIC_VERSION}

USER root

RUN set -eux; \
	mkdir /state; \
	chmod 0775 /state; \
	chown elasticsearch:root /state

RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

USER elasticsearch:root

ENTRYPOINT ["/entrypoint.sh"]
