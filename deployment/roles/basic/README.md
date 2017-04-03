# BASIC SYSTEM CONFIGURATION

## Description
Basic system configuration, OS update, installation of some commonly used
command line tools. This is a base role and it is executed before every other
role.

## Features
Role provides clustering support for all servers with the same "PROJECT_NAME".

This includes:
* cluster membership and failure detection
* custom events and queries handling and propagation

List of cluster members
```
$ sudo serf members
```

Other roles can activate custom cluster
[https://www.serfdom.io/intro/getting-started/user-events.html](events) or
[https://www.serfdom.io/intro/getting-started/queries.html](queries) by adding
executable script (with correct shebang and without extension)
to _/etc/serf/handlers_ directory. User events must be prefixed with "user-"
and queries with "query-" (user-deploy, query-uptime, etc.)

Executing custom cluster event
```
$ sudo serf event user-<EVENT-NAME> <PAYLOAD>
```

Executing custom cluster query
```
$ sudo serf query query-<EVENT-NAME> <PAYLOAD>
```

## Monitoring
Monitoring queries are exposed via Nagios NRPE service running on port 5666.

**List of queries:**
* check_load            - check system load
* check_disk_DISK-NAME  - check disk free space. Disk name is absolute path
                          to mounted device name with '/' replaced with '_'.
                          Example: /dev/sda1 - check_disk_dev_sda1


## Configuration
See [defaults/main.yml](defaults/main.yml).
