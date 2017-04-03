# DATABASE DEVELOPMENT SUPPORT

## Description
PostgreSQL/PostGIS development and profiling tools. Use only for development !

## Features
**Extensions**
* pldebugger         - PostgreSQL debugger
* plprofiler         - PostgreSQL profiler

**User accounts**
* vagrant            - PostgreSQL superuser, password: vagrant

## Usage

### pldebugger
Create pldebugger extension in database
```
CREATE EXTENSION pldbgapi;
```

* create function
```
CREATE FUNCTION pgmax (a INTEGER, b INTEGER)
  RETURNS INTEGER
AS $$
BEGIN
  IF  a > b THEN
    RETURN a;
  END IF;
  RETURN b;
END;
$$ LANGUAGE plpgsql;
```

* in PgAdmin, under _Database > Schemas > Functions_, right-click on function
  you want to debug. _Debugging_ menu with _Debug_ and _Set breakpoint_ will
  appear.

### plprofiler
_pldebugger_ and the _plprofiler_ extensions are using the same internal
PostgreSQL hooks, which means, that they **CAN NOT** be used at the same time.
_pldebugger_ extension is enabled by default.

In order to enable _plprofiler_, _pldebugger_ must be disabled first. This can
be done by setting "shared_preload_libraries" variable in
_/etc/postgresql/conf.d/100-postgresql-develop.conf_ to "$libdir/plprofiler"
value, followed by PostgreSQL service restart.


* create plprofiler extension in database
```
CREATE EXTENSION plprofiler;
```

* enable profiling
```
SELECT pl_profiler_enable(true);
```

* create function
```
CREATE FUNCTION pgmax (a INTEGER, b INTEGER)
  RETURNS INTEGER
AS $$
BEGIN
  IF  a > b THEN
    RETURN a;
  END IF;
  RETURN b;
END;
$$ LANGUAGE plpgsql;
```

* execute function
```
SELECT pgmax(4,8);
SELECT pgmax(6,5);
```

* retrieve code performance information
```
SELECT * FROM pl_profiler_linestats_current;

 func_oid | line_number |       line       | exec_count | total_time | longest_time
----------+-------------+------------------+------------+------------+--------------
    30591 |           0 |                  |          4 |         50 |           13
    30591 |           1 |                  |          0 |          0 |            0
    30591 |           2 | BEGIN            |          0 |          0 |            0
    30591 |           3 |   IF  a > b THEN |          4 |         37 |           10
    30591 |           4 |     RETURN a;    |          4 |          6 |            2
    30591 |           5 |   END IF;        |          0 |          0 |            0
    30591 |           6 |   RETURN b;      |          0 |          0 |            0
    30591 |           7 | END;             |          0 |          0 |            0
    30591 |           8 |                  |          0 |          0 |            0
    30591 |           9 |                  |          0 |          0 |            0
(10 rows)
```
```
SELECT * FROM pl_profiler_callgraph_current;

    pl_profiler_get_stack     | call_count | us_total | us_children | us_self
------------------------------+------------+----------+-------------+---------
 {"public.pgmax() oid=30591"} |          4 |       50 |           0 |      50
(1 row)
```

* disable profiling
```
SELECT pl_profiler_enable(false);
```

For more details see [plprofiler doc]
(https://bitbucket.org/openscg/plprofiler).


### Other notes
There is now a new python [script]
(https://bitbucket.org/openscg/plprofiler/src/6bf070fc8ef14dfedd8462835b8a9baa98a90afd/tools/python-tool/plprofiler_tool/plprofiler_tool.py?fileviewer=file-view-default)
to report function profiling.
