--select reblockall()
CREATE OR REPLACE FUNCTION reblockall() RETURNS boolean AS
$BODY$
BEGIN
RETURN reblockall('unknown','{}',False);
END
$BODY$
LANGUAGE plpgsql VOLATILE;

--select reblockall('unknown',array['railway_cl','airport_poly','lake_poly','native_poly'],True)
--select reblockall('t50_fid',array['airport_poly'],True)

CREATE OR REPLACE FUNCTION rbl_init(atab text,rtab text) RETURNS void AS
--Initialise the report/assoc tables. TODO pass atab/rtab names as args to calling funcs
$BODY$
BEGIN
	raise notice 'Initialising % & %.',atab,rtab;
	execute 'create table if not exists '||rtab||' (ref int, msg text, ts timestamp)';
	execute 'create table if not exists '||atab||' (ts timestamp, layer varchar,ufid int, ufid_components int[])';
END
$BODY$
LANGUAGE plpgsql VOLATILE;

--select reblockall('ufid',True)

CREATE OR REPLACE FUNCTION reblockall(pkey text, filter text[], overwrite boolean) RETURNS boolean AS
--Main reblocking function calling all tables in schema filtered by filter list
$BODY$
DECLARE
	res boolean;
	q1 TEXT;
	rc int;
	layer character varying;
	gtype character varying;
	schma character varying := 'public';
	xtabl character varying := 'spatial_ref_sys';
	defsrid int := 2193;
	smsg text;
	prefix text := 'new';
	boundary text := 'cropregions';
	atab text := 'rbl_associations';
	rtab text := 'rbl_report';
	join_func_poly text := 'st_union';
	join_func_line text := 'st_linemerge(st_union';
	qs text := '';
	usepkey text;
	
	changeset text[];
BEGIN
	
	execute 'select rbl_init('||quote_literal(atab)||','||quote_literal(rtab)||')';
	------------------------------------------------------------------------
	
	if array_length(filter,1)>0 then
		qs = ' and tablename = any('||quote_literal(filter)||')';
	end if;
	
	q1 = 'select tablename'
	|| ' from pg_tables'
	|| ' where schemaname = '||quote_literal(schma)
	|| ' and tablename != '||quote_literal(xtabl)
	|| ' and tablename != '||quote_literal(boundary)
	|| ' and tablename != '||quote_literal(atab)
	|| ' and tablename != '||quote_literal(rtab)
	--|| ' and tablename like '||quote_literal('%_poly')
	|| qs
	|| ' order by tablename';
	--raise notice 'qs=%',qs;
	--raise notice 'q1=%',q1;
	--return True;
	for layer in execute q1
	loop
		if pkey = 'unknown' then
			execute 'select ufid_column_identifier('||quote_literal(layer)||')' into usepkey;
		else
			usepkey = pkey;
		end if;
		
		raise notice 'Reblocking Layer %/%. %',layer,usepkey,clock_timestamp();
		execute 'select GeometryType(wkb_geometry::geometry) from '||quote_ident(layer) into gtype;
		
		if gtype in ('POLYGON','MULTIPOLYGON') then
			res = reblocksplitter(layer, prefix, usepkey, boundary, join_func_poly,True);
		elsif gtype in ('LINESTRING','MULTILINESTRING') then
			res = reblocksplitter(layer, prefix, usepkey, boundary, join_func_line,False);
		end if;
	end loop;
	raise notice 'Reblocking Complete. %',clock_timestamp();
RETURN True;
END
$BODY$
LANGUAGE plpgsql VOLATILE;

-- ----------------------------------------------------------------------------
--select ufid_column_identifier('new_lake_poly')
CREATE OR REPLACE FUNCTION ufid_column_identifier(qtab text) RETURNS text AS
$BODY$
DECLARE 
	colname text;
	q1 text;
	res text;
BEGIN
	q1 = 'select column_name'
	|| ' from information_schema.columns'
	|| ' where table_name='||quote_literal(qtab)
	|| ' and not column_name = any(array[''ogc_fid'',''wkb_geometry''])';

	for colname in execute q1
	loop
		q1 = 'select max(count) from (select count(*),'||colname||' from '||qtab||' group by '||colname||') a';
		
		execute q1 into res;
		if res='1' then
			raise notice'UFID DETECT %',colname;
			return colname;
		end if;
	end loop;
	
return 'ufid';
END
$BODY$
LANGUAGE plpgsql VOLATILE;

-- ----------------------------------------------------------------------------
--select reblockclean();
CREATE OR REPLACE FUNCTION reblockclean() RETURNS boolean AS
--Temporary function to delete test tables. *Remove for production
$BODY$
DECLARE
	res boolean;
	q1 TEXT;
	rc int;
	layer character varying;
	gtype character varying;
	schma character varying := 'public';
	xtabl character varying := 'spatial_ref_sys';
	threshold int := 150000;
	boundary text := 'cropregions';
BEGIN
	q1 = 'select tablename'
	|| ' from pg_tables'
	|| ' where schemaname = '||quote_literal(schma)
	--|| ' and tablename like '||quote_literal('%_poly')
	--|| ' and not tablename like '||quote_literal('new_%')||' and not tablename like '||quote_literal('northisland%')|| ' and not tablename like '||quote_literal('southisland%')|| ' and not tablename like '||quote_literal('reblocklist%')|| ' and not tablename like '||quote_literal('aggregatedreblocklist%')
	|| ' and not tablename like ''spatial_ref_sys'' and not tablename like ''cropregions'''
	|| ' order by tablename';
	for layer in execute q1
	loop
		--execute 'select GeometryType(wkb_geometry::geometry) from '||quote_ident(layer) into gtype;
		--if gtype in ('POLYGON','MULTIPOLYGON') then
		raise notice 'Removing Temporary tables for Layer %. %',layer,clock_timestamp();

		execute 'drop table if exists reblocklist_northisland_northsouth_'||quote_ident(layer);
		execute 'drop table if exists reblocklist_northisland_eastwest_'||quote_ident(layer);
		execute 'drop table if exists reblocklist_southisland_northsouth_'||quote_ident(layer);
		execute 'drop table if exists reblocklist_southisland_eastwest_'||quote_ident(layer);

		execute 'drop table if exists aggregatedreblocklist_northisland_northsouth_'||quote_ident(layer);
		execute 'drop table if exists aggregatedreblocklist_northisland_eastwest_'||quote_ident(layer);
		execute 'drop table if exists aggregatedreblocklist_southisland_northsouth_'||quote_ident(layer);
		execute 'drop table if exists aggregatedreblocklist_southisland_eastwest_'||quote_ident(layer);

		execute 'drop table if exists northisland_northsouth_'||quote_ident(layer);
		execute 'drop table if exists northisland_eastwest_'||quote_ident(layer);
		execute 'drop table if exists southisland_northsouth_'||quote_ident(layer);
		execute 'drop table if exists southisland_eastwest_'||quote_ident(layer);

		execute 'drop table if exists new_'||quote_ident(layer);
		--execute 'drop table if exists '||quote_ident(layer);
		--execute 'truncate table rbl_associations';

		--end if;
	end loop;
	raise notice 'Reblock Cleaning Complete. %',clock_timestamp();
RETURN True;
END
$BODY$
LANGUAGE plpgsql VOLATILE;
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ufid_generator(flist int[],wkb_geometry geometry) RETURNS int AS
$BODY$
BEGIN
return ufid_hash_generator(flist,wkb_geometry);
END
$BODY$
LANGUAGE plpgsql VOLATILE;

CREATE OR REPLACE FUNCTION ufid_generator(flist int[],seq_table text) RETURNS int AS
$BODY$
BEGIN
return ufid_sequence_generator(flist,seq_table);
END
$BODY$
LANGUAGE plpgsql VOLATILE;
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION ufid_sequence_generator(flist int[],ctab text) RETURNS int AS
$BODY$
declare
q1 text;
res int;
atab text := 'rbl_associations';
BEGIN
--NB Common column name for PK in assoc table, not necessarily actual PK name. Using 'ufid'
q1 = 'with latest as ('
|| ' 	select max(ts) mts from '||atab||' where ufid_components::int[]='||quote_literal(flist)||'::int[] and layer='''||quote_ident(ctab)||''''
|| ' ) select ufid from '||atab||' ta join latest l on l.mts = ta.ts where ufid_components::int[]='||quote_literal(flist)||'::int[] and layer='''||quote_ident(ctab)||'''';
--raise notice 'seq %',q1;
execute q1 into res;
if res is NULL then
	execute 'select ufid_sequence('''||ctab||''')' into res;
	--res = ufid_sequence();
end if;

return res;

END
$BODY$
LANGUAGE plpgsql VOLATILE;
--drop table if exists new_snow_poly;select reblocksplitter('snow_poly','new','ufid','cropregions','st_union',False)
--drop table if exists new_river_cl;select reblocksplitter('river_cl','new','ufid','cropregions','st_linemerge(st_union',False)
-- -----------------------------------------------------------------------------------------------------------------------


-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION ufid_sequence(layername text) RETURNS int AS
$BODY$
declare
res int;

--seqname text := layername||'_ufid_seq';
seqname text := 'topo_rbl_ufid_seq';
--consider rewriting this to avoid using exceptions
BEGIN
--contours hack 2->1
if layername like '%contour%' then
	seqname := 'contour_ufid_seq';
end if;

begin
	execute 'select nextval('''||seqname||''')' into res;
exception when others then
	execute 'select ufid_seqinit('''||seqname||''')';
	execute 'select nextval('''||seqname||''')' into res;
end;
return res;
END
$BODY$
LANGUAGE plpgsql VOLATILE;
-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
CREATE OR REPLACE FUNCTION ufid_seqinit(seqname text) returns void as
$BODY$
declare
cs text;
startval int := 100000000;

BEGIN
if not exists (select 0 from pg_class where relname = seqname) then 
	execute 'create sequence '||seqname||' start '||startval; 
end if;

END
$BODY$
LANGUAGE plpgsql VOLATILE;

-- ----------------------------------------------------------------------------------------------------------------------
--returns wheteher a particular feature has changed or not
--TODO evaluate md5 to geo compare speeds 
CREATE OR REPLACE FUNCTION ufid_changedetect(ufid int,layer1 text, layer2 text,pkey text) RETURNS boolean AS
$BODY$
DECLARe
	q0 text;
	res boolean;

BEGIN

q0 = 'select l1.g != l2.g from'
|| ' (select md5(wkb_geometry::text) md5g, wkb_geometry::text g from '||layer1||' where '||pkey||'='||ufid||') l1,'
|| ' (select md5(wkb_geometry::text) md5g, wkb_geometry::text g from '||layer2||' where '||pkey||'='||ufid||') l2';
--raise notice 'cd %',q0;
execute q0 into res;

RETURN res;
END
$BODY$
LANGUAGE plpgsql VOLATILE;
--select compare_ufid('snow_poly')

-- ---------------------------------------------------------------------------
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION reblocksplitter(original text,prefix text,pkey text, boundary text, op text,touch boolean) RETURNS boolean AS
$BODY$
DECLARE
region character varying;
q0 character varying;
q1 character varying;
res character varying;
newtable1 TEXT;
newtable2 TEXT;
endtable TEXT;
inttable TEXT;
delim TEXT;
fstr TEXT := '';
qstr TEXT := '';
dstr TEXT := '';
BEGIN

endtable = prefix||'_'||quote_ident(original);
inttable = prefix||'0_'||quote_ident(original);
delim = 'create table '||quote_ident(inttable)||' as';
q1 = 'select region from '||boundary;--cropregions';-- order by id asc limit 1';
for region in execute q1
loop
	--raise notice 'PKEY=%',pkey;
	newtable1 = quote_ident(region)||'_northsouth_'||quote_ident(original);
	execute 'drop table if exists '||newtable1 as res;
	raise notice '### Merge NorthSouth borders for region=% on layer=%',region,original;
	res = reblockfaster(original,original,pkey,op,touch,boundary,region,newtable1,True);

	newtable2 = quote_ident(region)||'_eastwest_'||quote_ident(original);
	execute 'drop table if exists '||newtable2 as res;
	raise notice '### Merge EastWest borders for region=% on layer=%',region,newtable1;
	res = reblockfaster(original,newtable1,pkey,op,touch,boundary,region,newtable2,False);

	fstr = fstr || delim ||' select * from '||quote_ident(newtable2); 
	dstr = dstr || 'drop table '||quote_ident(newtable1)||';drop table '||quote_ident(newtable2)||';'; 
	delim = ' union ';
end loop;

qstr = 'drop table if exists '||quote_ident(inttable);
raise notice 'DROP=%',qstr;
execute qstr as res;
raise notice 'CREATE=%',fstr;
execute fstr as res;
raise notice 'DROP-REG=%',dstr;
execute dstr as res;

perform rbl_disassociate_ufid_components(inttable, endtable, pkey);
--collision detect shouldnt be needed with seq ufids. Run as a check on source id dups
perform rbl_collision_detect(endtable, pkey);

execute 'grant all on table '||endtable||' to public' as res;

RETURN True;
END
$BODY$
LANGUAGE plpgsql VOLATILE;

-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION columntext(layer text, prefix text, delim text, omissions text[],torl text) RETURNS character varying AS
$BODY$
DECLARE 
cstr TEXT;
BEGIN
--TODO filter on schema else duplicate table names in diff schems cause multiple dup cols
cstr = array_to_string(array(select ' '||prefix||c.column_name||' '
        from information_schema.columns as c
            where table_name = layer 
            and not c.column_name = any (omissions)
            order by c.ordinal_position
	),delim);

if torl='T' and not cstr='' then return cstr||delim;
elsif torl='L' and not cstr='' then return delim||cstr;
else return cstr;
end if;
END
$BODY$
LANGUAGE plpgsql VOLATILE;



-- ---------------------------------------------------------------------------
-- SQL Funcs to manipulate geometries as TEXT
-- triple bypass runs too slowly to be useful
CREATE OR REPLACE FUNCTION loop_removal(geometry) RETURNS geometry AS
--Removes loops in multilinestrings by finding and deleting instances of ML((...),(A,b,c,d,A),(...))
'select ST_LineMerge(ST_GeomFromText(regexp_replace(regexp_replace(ST_AsText($1),''\((\d+\.*\d*\s\d+\.*\d*),[\s\d,.]*\1\),*'',''''),'',\)'','''')));'
LANGUAGE sql VOLATILE;

-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION triple_bypass(geometry) RETURNS geometry AS
-- Strips one of 3x duplicate coordinates from MLS. This is VERY slow 
'select ST_LineMerge(ST_GeomFromText(regexp_replace(regexp_replace(ST_AsText($1),(regexp_matches(ST_AsText($1),''(\d+\.*\d*\s\d+\.*\d*).+\1.+\1'',''g''))[1]||'','',''''),'',\)'','')'')));'
LANGUAGE sql VOLATILE;


--select regexp_replace('FUNC((1.0 2.0, 1.0 3.0, 1.0 4.0), (1.0 2.0, 1.0 5.0), (2.0 3.0, 3.0 4.0, 1.0 2.0))','(\d+\.\d+\s\d+\.\d+)(?=.+\1.+\1)','XXX');
--select regexp_matches('FUNC((1.0 2.0, 1.0 3.0, 1.0 4.0), (1.0 2.0, 1.0 5.0), (2.0 3.0, 3.0 4.0, 1.0 2.0))','(\d+\.\d+\s\d+\.\d+).+\1.+\1','g');
-- ---------------------------------------------------------------------------

-- select assemble_ufid_components(array[10724173.0000000,10724195.000000]::int[],'new_snow_poly','ufid')
CREATE OR REPLACE FUNCTION assemble_ufid_components(flist int[],layer character varying,pkey text) RETURNS int[] AS
$BODY$
DECLARE 
ufid int;
composite int[] := array[]::int[];
res int[];
q text; 
BEGIN
foreach ufid in array flist
loop
	execute 'select ufid_components::int[] from '||layer||' where '||pkey||'='||ufid into res;
	composite = array_cat(composite,res); 
	--raise notice 'compo %',composite;
end loop;

return composite;
END
$BODY$
LANGUAGE plpgsql VOLATILE;

-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION trail(arg_str text, dchar text) RETURNS text AS
$BODY$
BEGIN
if (arg_str = '') then return '';
else return arg_str||dchar;
end if;
END
$BODY$
LANGUAGE plpgsql VOLATILE;

-- ---------------------------------------------------------------------------
-- CUSTOM AGG

create or replace function array_rbl_compress(anyarray) returns anyarray as
'select distinct array(select distinct unnest($1) order by 1)'
LANGUAGE SQL IMMUTABLE;

create or replace function array_rbl_concat(anyarray,anyarray) returns anyarray as
--'select array_cat($1,$2) where $1&&$2 or array_length($1,1)=0 or array_length($2,1)=0' 
'select array_cat($1,$2)' 
LANGUAGE SQL IMMUTABLE;

drop aggregate if exists array_rbl_agg(anyarray);
create aggregate array_rbl_agg(anyarray)
(
SFUNC=array_rbl_concat,
STYPE=anyarray,
FINALFUNC=array_rbl_compress,
INITCOND=$${}$$
);
-- ---------------------------------------------------------------------------
-- BOUNDARY CHECKER
-- NB Written for Topo50 maps and though not tested with, should also work on Topo250 maps since they use a subset of the Topo50 mapsheet boundaries

--select northsouth(4794000) = select northsouth(5334000) = T
--select northsouth(4793000) = select northsouth(366000) = select northsouth(6234000) = select northsouth(5334001) = F
CREATE OR REPLACE FUNCTION northsouth(ns numeric) RETURNS boolean AS
$BODY$
DECLARE
minx int := 131;
maxx int := 172;
cnst numeric = 6000;
step numeric := 36000;
d numeric;
m numeric;
BEGIN
d = div(ns::numeric - cnst, step);
m = mod(ns::numeric - cnst, step);
return m=0 and d>minx and d<maxx; 
END
$BODY$
LANGUAGE plpgsql VOLATILE;

-- ---------------------------------------------------------------------------
--select eastwest(4794000) = T
--select eastwest(4793000) = F
CREATE OR REPLACE FUNCTION eastwest(ew numeric) RETURNS boolean AS
$BODY$
DECLARE
minx int := 45;
maxx int := 87;
cnst numeric = 4000;
step numeric := 24000;
d numeric;
m numeric;
BEGIN
d = div(ew::numeric - cnst, step);
m = mod(ew::numeric - cnst, step);
return m=0 and d>minx and d<maxx; 
END
$BODY$
LANGUAGE plpgsql VOLATILE;

-- ---------------------------------------------------------------------------

-- select generate_rbl('exotic_poly','northisland','ufid','((t1.N and t2.S) or (t1.S and t2.N))','ogc_fid , ufid , species,','((t1.species is null and t2.species is null) or t1.species = t2.species)')
-- select generate_rbl('exotic_poly','northisland','ufid','((t1.N and t2.S) or (t1.S and t2.N))',trail('ogc_fid , ufid , species',','),trail('((t1.species is null and t2.species is null) or t1.species = t2.species)','and'))

CREATE OR REPLACE FUNCTION generate_rbl(rbl text,layer text,pkey text,bndry text,touch boolean,region text,firstpass boolean,coltext text,noidgeo text,snap_grid_size double precision) RETURNS text AS
$BODY$
DECLARE
qstr text;
gtype text;
res text;
map_sheet_ident integer := 1000;

nsewbound character varying;
nsewfilter character varying;
nsbound character varying := '((t1.N and t2.S and t1.Nv=t2.Sv) or (t1.S and t2.N and t1.Sv=t2.Nv))';
nsfilter character varying := '(N and northsouth(Nv)) or (S and northsouth(Sv))';
ewbound character varying := '((t1.E and t2.W and t1.Ev=t2.Wv) or (t1.W and t2.E and t1.Wv=t2.Ev))';
ewfilter character varying := '(E and eastwest(Ev)) or (W and eastwest(Wv))'; 

snapgrid text;
snapgridon text := 'st_snaptogrid(p.wkb_geometry::geometry,'||quote_literal(snap_grid_size)||')';
snapgridoff text := 'p.wkb_geometry';

msbndry text;
map_sheet_bndry_poly text := 'FF2F11212';
map_sheet_bndry_line text := 'FF1F00102';

roundval int;

BEGIN

if firstpass then 
	nsewbound = nsbound;
	nsewfilter = nsfilter;
else 
	nsewbound = ewbound;
	nsewfilter = ewfilter;
end if;

if touch then
	--snap for polys
	snapgrid = snapgridon;
	msbndry = map_sheet_bndry_poly;
	roundval = 0;
else
	--snap off for lines
	snapgrid = snapgridoff;
	msbndry = map_sheet_bndry_line;
	roundval = 2;
end if;


--select reblocksplitter('native_poly','st_union')
execute 'drop table if exists '||rbl as res;
qstr = 'create temporary table '||rbl||' as'
|| ' with bound as ('
|| ' 	select  '||coltext||snapgrid||' as stg_geometry,'
|| '    st_extent('||snapgrid||') as ex'	
|| ' 	from '||quote_ident(layer)||' p'
|| ' 	join '||quote_ident(bndry)||' cr '
|| ' 	on cr.region='||quote_literal(region) 	
|| ' 	and st_intersects(p.wkb_geometry,cr.wkb_geometry::geometry)'
|| ' 	group by '||coltext||'stg_geometry' 
|| ' ), exvals as ('
|| ' 	select  '||coltext
|| ' 	p.stg_geometry,'
|| ' 	round(st_ymax(p.stg_geometry)::numeric,'||roundval||') as Nv,'
|| ' 	round(st_ymin(p.stg_geometry)::numeric,'||roundval||') as Sv,' 	
|| ' 	round(st_xmax(p.stg_geometry)::numeric,'||roundval||') as Ev,'
|| ' 	round(st_xmin(p.stg_geometry)::numeric,'||roundval||') as Wv'
|| ' 	from bound p '
|| ' ), msfilter as (' 	
|| ' 	select '||coltext||'p.stg_geometry,p.Nv,p.Sv,p.Ev,p.Wv,' 
|| ' 	mod(p.Nv::numeric,'||quote_literal(map_sheet_ident)||')=0 as N,' 
|| ' 	mod(p.Sv::numeric,'||quote_literal(map_sheet_ident)||')=0 as S,'	
|| ' 	mod(p.Ev::numeric,'||quote_literal(map_sheet_ident)||')=0 as E,' 
|| ' 	mod(p.Wv::numeric,'||quote_literal(map_sheet_ident)||')=0 as W'
|| ' 	from exvals p'
|| ' ), srcpoly as ('
|| '	select * from msfilter' 	
|| ' 	where '||nsewfilter
|| ' ), linked as (' 
|| ' 	select t1.'||pkey||' as merge_id, t2.'||pkey||' as drop_id'  
|| ' 	from srcpoly as t1, srcpoly as t2'
|| ' 	where t1.'||pkey||'>t2.'||pkey  
|| ' 	and '||noidgeo||nsewbound
|| ' 	and st_relate(t1.stg_geometry,t2.stg_geometry,'||quote_literal(msbndry)||')'
|| ' ) select merge_id::int, drop_id::int from linked order by merge_id asc, drop_id asc';

raise notice 'RBL %',qstr;
execute qstr as res;
return res;
END
$BODY$
LANGUAGE plpgsql VOLATILE;
-- --------------------------------------------------------------------------------------------------
-- Utility function to log and raise progress messages in long multipart queries
CREATE OR REPLACE FUNCTION report_rbl(d int, t text) RETURNS int AS
$BODY$
BEGIN
-- dont want to call this on every ufid call
-- create table if not exists rbl_report (ref int, msg text, ts timestamp);
insert into rbl_report values (d,t,current_timestamp);
raise notice 'REPORT % - % - %',d,t,current_timestamp;
--returns the dp so we can "select report_rbl(ufid,'this is the ufid') ufid, col2 from table;"
return d;
END
$BODY$
LANGUAGE plpgsql VOLATILE;

-- ---------------------------------------------------------------------------
-- must use union all in recursive for PG<8.5 since arrays not hashable before then
CREATE OR REPLACE FUNCTION generate_aggrbl(arbl text, rbl text) RETURNS text AS
$BODY$
DECLARE
qstr text;
res TEXT;
BEGIN
execute 'drop table if exists '||arbl as res;
qstr = 'create temporary table '||arbl||' as'
|| ' with recursive innerrbl as ('
|| ' 	select array[merge_id,drop_id] ab, 0::int u from '||rbl
|| ' union'
|| '	select array_rbl_agg(aab.ab) x,aub.ab u' 
|| '	from ('
|| '		select ab from innerrbl'
|| '	) aab,' 
|| '	('
|| '		select distinct ab from (select merge_id ab from '||rbl||' union select drop_id ab from '||rbl||') r2'
|| '	) aub' 
|| '	where aub.ab = any(aab.ab) group by aub.ab'
|| ' ),'
|| ' outerrbl as ('
|| '	select distinct ab idarray from ('
|| '		select array_rbl_agg(ab) ab,u from innerrbl where not u=0 group by u'
|| ' 	) s'
|| ' ),'
|| ' frbl(feats,fal) as ('
|| ' 	select distinct'
|| ' 	r.idarray as feats, array_length(r.idarray,1) as al'
|| ' 	from outerrbl r'
|| ' 	join (select idarray[1] as mnv, max(array_length(idarray,1)) as mxl from outerrbl group by idarray[1]) m'
|| ' 	on m.mnv=r.idarray[1] and m.mxl=array_length(r.idarray,1) '
|| ' 	where r.idarray @> any(select idarray from outerrbl)'
|| ' ),'
|| ' fincl(flist,occur) as ('
|| ' 	select a.feats as af,'
|| ' 	max(case when a.u = any(f.feats) and f.fal!=a.fal then 1 else 0 end) as mx'
|| ' 	from (select feats,fal,unnest(feats) as u from frbl) a'
|| ' 	join frbl f on a.fal<=f.fal'
|| ' 	group by af'
|| ' ) select flist from fincl where occur=0';

raise notice 'ARBL %',qstr;
execute qstr as res;
return res;
END
$BODY$
LANGUAGE plpgsql VOLATILE;

-- ---------------------------------------------------------------------------
-- C O L L I S I O N


CREATE OR REPLACE FUNCTION rbl_collision_detect(ctab text,pkey text) RETURNS boolean AS
$BODY$
DECLARE
q1 text;
res text;
msg text := 'UFID Collision in table '||ctab;
BEGIN
q1 = 'select count(*) from (select report_rbl('||pkey||'::int,'||quote_literal(msg)||'::text) ufid from (select '||pkey||',count(*) c from '||ctab||' group by '||pkey||') a where c>1) a';
execute q1 into res;

return res::int>0;
END
$BODY$
LANGUAGE plpgsql VOLATILE;
-- ---------------------------------------------------------------------------


CREATE OR REPLACE FUNCTION rbl_disassociate_ufid_components(interim text, final text,pkey text) RETURNS text AS
-- Removes the ufid_components field from the active table to the associations table
$BODY$
DECLARE
qasc text;
qtab text;
qidp text;
qfdp text;
cols TEXT;
res TEXT;
atab text := 'rbl_associations';

BEGIN

execute 'create table if not exists '||atab||' (ts timestamp, layer varchar,ufid int, ufid_components int[])' as res;

cols = columntext(interim,'',',',array['ufid_components'],'');
qasc = 'insert into '||atab||' select date_trunc(''minute'',current_timestamp),'||quote_literal(final)||', '||pkey||', ufid_components from '||interim||' where array_length(ufid_components,1)>1';
qfdp = 'drop table if exists '||final;
qtab = 'create table '||final||' as select '||cols||' from '||interim;

qidp = 'drop table '||interim;
raise notice 'asc=%, new=%, tab=%, int=%',qasc,qfdp,qtab,qidp;
execute qasc as res;
execute qfdp as res;
execute qtab as res;
execute qidp as res;

return res;
END
$BODY$
LANGUAGE plpgsql VOLATILE;
-- ---------------------------------------------------------------------------
-- args
-- src_table = source table being queries, eg. original_vector_layer
-- op = operation : {st_union,st_memunion}
-- touch = indicator for line/poly table type for setting ST_Relate intersection parameter : {FF2F11212,FF1F00102} and whether ST_SnapToGrid is used
-- bndry = table to crop against, ie cropregions
-- region = crop region selector : {northisland, southisland}
-- dst_table = merged table, eg. new_vector_layer
-- firstpass = flag to indicate new table creation or array initialisation
CREATE OR REPLACE FUNCTION reblockfaster(original text,src_table text,pkey text,op text,touch boolean,bndry text, region text,dst_table text,firstpass boolean) RETURNS boolean AS
$BODY$
DECLARE
res character varying;
q0 TEXT;
q1 TEXT;
q2 TEXT;
q3 TEXT;
q4 TEXT;
q5 TEXT;
q6 TEXT;
link0 TEXT;
link1 TEXT;
link2 TEXT;
cori TEXT;
ufidc1 TEXT;
ufidc2 TEXT;
fluc TEXT;
closeb TEXT;
coltext0 TEXT;
coltext1 TEXT;
coltext2 TEXT;
coltext3 TEXT;
coltext4 TEXT;
noidgeo character varying;
shtbndy character varying;
fp text;
rbt TEXT := 'reblocklist_'||dst_table;
arbt TEXT := 'aggregatedreblocklist_'||dst_table;
msg text := 'Mapsheet boundary-join error for table '||dst_table;

-- snap to grid size to identify merge candidates. Set this large to capture intended merges
stg_id double precision := 1e-11;--1e-11 works for GBI

-- snap to grid size to merge misaligned features (corrects multipoly error @ great barrier) We set this small to minimise error
stg_mv double precision := 1e-11;

BEGIN

q0 = 'drop table if exists '||rbt||';drop table if exists '||arbt||';drop table if exists '||dst_table;
--execute q0 as res;

--select all optional columns
noidgeo = trail(array_to_string(array(select '((t1.'||c.column_name||' is null and t2.'||c.column_name||' is null) or t1.'||c.column_name||' = t2.'||c.column_name||')'
        from information_schema.columns as c
            where table_name = src_table
            and  c.column_name not in(src_table, pkey,'wkb_geometry','ogc_fid','ufid_components')
            order by c.ordinal_position
            ),' and '),'and');

coltext0 = columntext(src_table,'p.',',',array['wkb_geometry','ufid_components'],'T');
perform generate_rbl(rbt, src_table, pkey, bndry, touch, region, firstpass, coltext0, noidgeo, stg_id);
perform generate_aggrbl(arbt, rbt);

-- setup the destination table populating with unmerged geometries

coltext1 = columntext(src_table,'mergetab.',',',array[pkey,'ogc_fid','wkb_geometry','ufid_components'],'T');
coltext2 = columntext(src_table,'mergetab.',',',array[pkey,'ogc_fid','ufid_components','wkb_geometry'],'T');
coltext3 = columntext(src_table,'og.',',',array[pkey,'ogc_fid','ufid_components','wkb_geometry'],'T');
coltext4 = columntext(src_table,'',',',array[pkey,'ogc_fid','ufid_components','wkb_geometry'],'T');

if firstpass then 
	--cori = 'create table '||dst_table||' as';
	ufidc1 = 'array['||pkey||'] as ufid_components,';
	ufidc2 = 'mergetab.flist as ufid_components,';
	fluc = 'u.flist,';
else 
	--cori = 'insert into '||dst_table;
	ufidc1 = 'mergetab.ufid_components::int[] as ufid_components,';
	ufidc2 = 'assemble_ufid_components(mergetab.flist::int[],'||quote_literal(src_table)||','||quote_literal(pkey)||') as ufid_components,';
	fluc = 'array(select distinct unnest(u.flist) order by 1) as flist,';
end if;

--insert non-merging features		
q4 = 'create table '||dst_table||' as'
|| ' select distinct mergetab.ogc_fid, mergetab.'||pkey||'::int,'|| coltext1 || ufidc1
|| ' mergetab.wkb_geometry::geometry'
|| ' from '||quote_ident(src_table) || ' as mergetab'
|| ' join '||quote_ident(bndry)||' cr'
|| ' on st_intersects(mergetab.wkb_geometry::geometry,cr.wkb_geometry::geometry)'
|| ' and cr.region='||quote_literal(region)
|| ' where '||pkey||' not in (select merge_id from '||rbt||' union select drop_id from '||rbt||')';
raise notice 'CTNT %',q4;
execute q4 as res;

if position('(' in op)>0 then closeb = ')';
else closeb = '';
end if; 

--merge and insert features
-- HACK. Outer select checks for MLS to prevent merge until loop/3pt fixed in data
--
q5 = 'insert into '||dst_table
|| ' with splitmerge as ('
|| ' 	select ufid_generator(jointab.ufid_components,'''||original||''') '||pkey||',* from ('
--|| ' 	select ufid_generator(jointab.ufid_components,jointab.wkb_geometry) '||pkey||',* from ('
|| ' 		select max(mergetab.ogc_fid) as ogc_fid, ' || coltext2 || ufidc2 || op
|| '		(array_agg(st_snaptogrid(wkb_geometry,'||quote_literal(stg_mv)||closeb||'))) as wkb_geometry' 
|| '		from ( '
|| ' 			select '||fluc||'o.*'
|| ' 			from ( select unnest(flist) as unnest, flist from '||arbt||') u' 
|| ' 			join '||quote_ident(src_table)||' o' 
|| ' 			on u.unnest = o.'||pkey 
|| ' 		) mergetab'
|| ' 		group by  '||coltext2||' mergetab.flist'
|| ' 	) jointab'
|| ' )'
|| ' select ogc_fid,'||pkey||','||coltext4||'ufid_components, wkb_geometry from splitmerge where st_geometrytype(wkb_geometry) <> all(array[''ST_MultiLineString'',''ST_MultiPolygon''])'
|| ' union'
|| ' select og.ogc_fid,report_rbl(og.'||pkey||'::int,'||quote_literal(msg)||'::text) '||pkey||','||coltext3||'og.ufid_components,og.wkb_geometry'
|| ' from ('
|| ' 	select distinct mergetab.ogc_fid, mergetab.'||pkey||', '|| coltext1 || ufidc1
|| '	mergetab.wkb_geometry::geometry'
|| ' 	from '||quote_ident(src_table)||' as mergetab'
|| ' ) og'
|| ' join ('
|| ' 	select unnest(ufid_components) as '||pkey||', wkb_geometry from splitmerge where st_geometrytype(wkb_geometry) = any(array[''ST_MultiLineString'',''ST_MultiPolygon''])'
|| ' ) sm' 
|| ' on sm.'||pkey||' = og.'||pkey;


raise notice 'MERGE %',q5;
execute q5 as res;

RETURN True;
END
$BODY$
LANGUAGE plpgsql VOLATILE;