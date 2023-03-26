#!/usr/bin/env bash

set -u
set -o pipefail

state_file=/state/.done
if [[ -e "$state_file" ]]; then
    echo "Setup has already run successfully. Skipping"
    exit 0
fi

echo "Running setup"

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
echo "Creating users in database ..."

PGPASSWORD=changeme psql -h postgres -U postgres -c "CREATE DATABASE prewikka;" || :
PGPASSWORD=changeme psql -h postgres -U postgres -c "CREATE USER prelude WITH ENCRYPTED PASSWORD 'prelude';" || :
PGPASSWORD=changeme psql -h postgres -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE prewikka TO prelude;" || :
PGPASSWORD=changeme psql -h postgres -U postgres -c "ALTER DATABASE prewikka OWNER TO prelude;" || :
echo "Users created"

echo "Waiting for elasticsearch to be ready ..."
until curl --user elastic:elastic 'http://es01:9200/_cluster/health?wait_for_status=yellow&timeout=30s'; do
    sleep 2
done
echo "Elasticsearch is ready"

echo "Setup ended"

mkdir -p "${state_file%/*}"
touch "$state_file"
