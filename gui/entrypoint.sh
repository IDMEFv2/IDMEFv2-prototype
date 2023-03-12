#!/usr/bin/env bash

set -eu
set -o pipefail

echo "Running IHM"

PGPASSWORD=changeme psql -h postgres -U postgres -c "CREATE DATABASE prewikka;" || :
PGPASSWORD=changeme psql -h postgres -U postgres -c "CREATE USER prelude WITH ENCRYPTED PASSWORD 'prelude';" || :
PGPASSWORD=changeme psql -h postgres -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE prewikka TO prelude;" || :
PGPASSWORD=changeme psql -h postgres -U postgres -c "ALTER DATABASE prewikka OWNER TO prelude;" || :

/usr/local/bin/prewikka-cli -C 'sync plugin' || :

/usr/local/bin/prewikka-httpd -p 80
