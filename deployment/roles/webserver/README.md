# LINZ BDE PROCESSOR

## Description
LINZ processor of LandOnLine BDE (bulk data extract) data.

## Features
**System users**
* bde

**Database roles**
* bde_admin        - BDE admin group (hardcoded in BDE tools)
* bde_dba          - BDE database administrator group (hardcoded in BDE tools)
* bde_user         - BDE user group (hardcoded in BDE tools)
* bde              - BDE user account

**Database templates**
* template_bde     - PostGIS template with BDE support

## Configuration
See [defaults/main.yml](defaults/main.yml).

## Sample data
* BDE sample       - http://linz-dl.s3.amazonaws.com/bde_sample_data.tar.gz
* BDE small sample - http://linz-dl.s3.amazonaws.com/bde_sample_data_small.tar.gz
* BDE WCC sample   - http://linz-dl.s3.amazonaws.com/bde_sample_data_wcc.tar.gz
* TA boundaries    - http://linz-dl.s3.amazonaws.com/ta_bdys_sample_data.dump

## Vagrant
**Forwarded ports**
* PostgreSQL       - 5432 -> 15432
