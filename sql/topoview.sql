--create extension dblink;
--create extension postgis;

CREATE OR REPLACE FUNCTION link_topo_layers() RETURNS void AS
-- creates views in topo_rdb from reblock.new_ tables
$BODY$
DECLARE 
	src_db text := 'reblock';
	filter text := 'new_%';
	q1 text;	
	q2 text;
	q3 text;
	q4 text;
	table_name text;
	new_name text;
	name_type character varying[];
	columns text;
	coltypes text;
	real_type text;
	res text;

BEGIN
	q1 = 'select table_name'
	|| ' from dblink('
	|| ' 	''dbname='||quote_ident(src_db)||''','
	|| ' 	''select table_name from information_schema.tables where table_name like '''||quote_literal(filter)||''''''
	|| ' ) as t1(table_name character varying)';
	
	--raise notice '>L1> %',q1;
	
	for table_name in execute q1
	loop
		-- i want to return a list of columns and their datatypes eg {id, int},{name text},{desc text}
		q2 = 'select name_type'
		|| ' from dblink('
		|| '	''dbname='||quote_ident(src_db)||''','
		|| '	''select array[column_name,data_type] from information_schema.columns where table_name = '''||quote_literal(table_name)||''''''
		|| ' ) as t1(name_type character varying[])';

		--raise notice '>L2> %',q2;
		columns  = '';
		coltypes = '';
		--iterating through column/type pairs because we cant return arrays-of-arrays from dblink query above
		for name_type in execute q2
		loop
			if name_type[2] = 'USER-DEFINED' and name_type[1] = 'wkb_geometry' then 
				real_type = 'geometry';
			else
				real_type = name_type[2];
			end if;
			columns  = columns||','||name_type[1];
			coltypes = coltypes||','||name_type[1]||' '||real_type;
			--raise notice '>L3> % - % - %',name_type, columns, coltypes;
			
		end loop;
		new_name = 'reblock_view_'||right(table_name, -length(filter)+1);
		q3 = 'drop view if exists '||new_name;
		q4 = 'create view '||new_name||' as'
		|| ' select *'
		|| ' from dblink('
		|| ' 	''dbname='||src_db||''', '
		|| ' 	''select '||trim(leading ',' from columns)||' from '||table_name||'''' 
		|| ') as t1('||trim(leading ',' from coltypes)||')';
		--raise notice '>L4> % / %',q3,q4;
		
		execute q3 as res;		
		execute q4 as res;

	end loop;
	
return;
END
$BODY$
LANGUAGE plpgsql VOLATILE;


CREATE OR REPLACE FUNCTION release_topo_layers() RETURNS void AS
-- creates views in topo_rdb from reblock.new_ tables
$BODY$
DECLARE 
	src_db text := 'reblock';
	filter text := 'reblock_view_%';
	q1 text;	
	q2 text;
	q3 text;
	table_name text;
	new_table text;
	name_type character varying[];
	res text;

BEGIN
	q1 = 'select table_name from information_schema.views where table_name like '||quote_literal(filter);
	
	--raise notice '>R1> %',q1;
	
	for table_name in execute q1
	loop
		new_table = right(table_name, -length(filter)+1);
		q2 = 'drop table if exists '||new_table;
		q3 = 'create table '||right(table_name, -length(filter)+1)||' as select * from '||table_name;
		--raise notice '>R2> % / %',q2,q3;
		
		execute q2 as res;
		execute q3 as res;

	end loop;
	
return;
END
$BODY$
LANGUAGE plpgsql VOLATILE;


--select link_topo_layers();
--select release_topo_layers();