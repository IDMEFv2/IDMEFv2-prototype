#!/usr/bin/env bash

set -u
set -o pipefail

echo "Waiting for database to be ready ..."
while true; do
    pg_isready -U postgres -h postgres
    if [ $? -eq 0 ]; then
        break
    else
        sleep 2
    fi
done
echo "Database is ready"

echo "Waiting for elasticsearch to be ready ..."
until curl --user elastic:elastic 'http://es01:9200/_cluster/health?wait_for_status=yellow&timeout=30s'; do
    sleep 2
done
echo "Elasticsearch is ready"

echo "Running GUI"
sleep 20
/usr/local/bin/prewikka-cli -C 'sync plugin'

/usr/local/bin/prewikka-httpd -p 80
