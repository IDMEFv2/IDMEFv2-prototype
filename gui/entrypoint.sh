#!/usr/bin/env bash

set -u
set -o pipefail

echo "Waiting for database to be ready ..."
while true; do
    pg_isready -U prelude -h postgres
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

PGPASSWORD=prelude psql -d prewikka -h postgres -U prelude -c "UPDATE prewikka_user_configuration SET config = '{\"\": {\"password\": \"\$5\$rounds=535000\$F0fsipTsXZvzOM6n\$r4D77J5PrWT/ZfRx7z0D/44d64irmg5ENnEwvLOASW.\"}}' WHERE userid = '21232f297a57a5a743894a0e4a801fc3';" || :
echo "Webinterface's admin's password sets to S4Sadmin"

/usr/local/bin/prewikka-httpd -p 80
