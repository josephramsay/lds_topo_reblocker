CREATE TABLE public.test_pt (  
  ogc_fid integer NOT NULL,
  wkb_geometry geometry(Point,4326),
  t50_fid double precision,
  CONSTRAINT test_pt_pk PRIMARY KEY (ogc_fid)
);

INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (0,ST_GeomFromText('POINT(-71.060316 48.433044)',4326),2436581);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (1,ST_GeomFromText('POINT(-71.060327 48.434044)',4326),2436576);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (2,ST_GeomFromText('POINT(-71.060338 48.435044)',4326),2436577);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (3,ST_GeomFromText('POINT(-71.060349 48.436044)',4326),2436573);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (4,ST_GeomFromText('POINT(-71.060356 48.437045)',4326),2436588);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (5,ST_GeomFromText('POINT(-71.060366 48.438046)',4326),2436574);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (6,ST_GeomFromText('POINT(-71.060376 48.439047)',4326),2436587);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (7,ST_GeomFromText('POINT(-71.060386 48.430048)',4326),2436575);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (8,ST_GeomFromText('POINT(-71.060396 48.431049)',4326),2436572);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (9,ST_GeomFromText('POINT(-71.060316 48.432040)',4326),2436584);

CREATE TABLE public.new_test_pt (  
  ogc_fid integer NOT NULL,
  wkb_geometry geometry(Point,4326),
  t50_fid double precision,
  CONSTRAINT new_test_pt_pk PRIMARY KEY (ogc_fid)
);

INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (0,ST_GeomFromText('POINT(-71.061311 48.432944)',4326),2436581);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (1,ST_GeomFromText('POINT(-71.062312 48.432744)',4326),2436576);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (2,ST_GeomFromText('POINT(-71.063313 48.432844)',4326),2436577);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (3,ST_GeomFromText('POINT(-71.064314 48.432644)',4326),2436573);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (4,ST_GeomFromText('POINT(-71.065316 48.432545)',4326),2436588);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (5,ST_GeomFromText('POINT(-71.066316 48.432346)',4326),2436574);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (6,ST_GeomFromText('POINT(-71.067316 48.432447)',4326),2436587);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (7,ST_GeomFromText('POINT(-71.068316 48.432248)',4326),2436575);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (8,ST_GeomFromText('POINT(-71.069316 48.432049)',4326),2436572);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (9,ST_GeomFromText('POINT(-71.060316 48.432140)',4326),2436584);

