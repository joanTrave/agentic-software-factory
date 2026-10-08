#!/bin/sh
# Mounted into the `db` service's /docker-entrypoint-initdb.d/ so the `*_test` database exists
# on first boot, letting the `test` compose service run against a database separate from dev
# data without a manual setup step.
set -eu

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE "${POSTGRES_DB}_test";
EOSQL
