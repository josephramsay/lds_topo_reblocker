# DATABASE SERVICE

## Description
PostgreSQL/PostGIS database server deployment with multiple PostgreSQL
extensions.

## Features
**System users**
* dba

**Database roles**
* dba              - database superuser

**Database templates**
* template_postgis - PostGIS (postgis, postgis topology) template

## Configuration
See [defaults/main.yml](defaults/main.yml).

## Monitoring
**List of queries:**
* check_database_running  - check if database is running
* check_database_backup   - check if database backup exists

## Data Directories
* /store/postgresql       - main PostgreSQL data directory
* /store/postgresql_xlog  - PostgreSQL WAL files directory

## Backup and Recovery
* /store/backup/base      - weekly binary base backup of running cluster
* /store/backup/pgarchive - point-in-time recovery using WAL files archive

## Vagrant
**Forwarded ports**
* PostgreSQL       - 5432 -> 15432
