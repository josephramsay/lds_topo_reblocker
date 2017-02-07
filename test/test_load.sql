CREATE TABLE public.test_pt (  
  ogc_fid integer NOT NULL,
  wkb_geometry geometry(Point,900915),
  t50_fid double precision,
  CONSTRAINT test_pt_pk PRIMARY KEY (ogc_fid)
);

INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (0,ST_GeomFromText('POINT(-71.060316 48.432044)',4326),2436581);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (1,ST_GeomFromText('POINT(-71.060317 48.432044)',4326),2436576);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (2,ST_GeomFromText('POINT(-71.060318 48.432044)',4326),2436577);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (3,ST_GeomFromText('POINT(-71.060319 48.432044)',4326),2436573);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (4,ST_GeomFromText('POINT(-71.060316 48.432045)',4326),2436588);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (5,ST_GeomFromText('POINT(-71.060316 48.432046)',4326),2436574);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (6,ST_GeomFromText('POINT(-71.060316 48.432047)',4326),2436587);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (7,ST_GeomFromText('POINT(-71.060316 48.432048)',4326),2436575);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (8,ST_GeomFromText('POINT(-71.060316 48.432049)',4326),2436572);
INSERT INTO public.test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (9,ST_GeomFromText('POINT(-71.060316 48.432040)',4326),2436584);

CREATE TABLE public.new_test_pt (  
  ogc_fid integer NOT NULL,
  wkb_geometry geometry(Point,900915),
  t50_fid double precision,
  CONSTRAINT new_test_pt_pk PRIMARY KEY (ogc_fid)
);

INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (0,ST_GeomFromText('POINT(-71.060311 48.432044)',4326),2436581);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (1,ST_GeomFromText('POINT(-71.060312 48.432044)',4326),2436576);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (2,ST_GeomFromText('POINT(-71.060313 48.432044)',4326),2436577);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (3,ST_GeomFromText('POINT(-71.060314 48.432044)',4326),2436573);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (4,ST_GeomFromText('POINT(-71.060316 48.432045)',4326),2436588);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (5,ST_GeomFromText('POINT(-71.060316 48.432046)',4326),2436574);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (6,ST_GeomFromText('POINT(-71.060316 48.432047)',4326),2436587);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (7,ST_GeomFromText('POINT(-71.060316 48.432048)',4326),2436575);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (8,ST_GeomFromText('POINT(-71.060316 48.432049)',4326),2436572);
INSERT INTO public.new_test_pt (ogc_fid, wkb_geometry, t50_fid) VALUES (9,ST_GeomFromText('POINT(-71.060316 48.432040)',4326),2436584);

