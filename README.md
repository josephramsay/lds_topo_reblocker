# lds_topo_reblocker - README
Topo Map Sheet Reblocking Scripts

[![Build Status](https://travis-ci.org/josephramsay/lds_topo_reblocker.svg?branch=master)](https://travis-ci.org/josephramsay/lds_topo_reblocker)
[![Coverage Status](https://coveralls.io/repos/github/josephramsay/lds_topo_reblocker/badge.svg?branch=master)](https://coveralls.io/github/josephramsay/lds_topo_reblocker?branch=master)

# DESCRIPTION
The Topo Reblocker is an application used to stitch together topopgraphic mapsheets into seamless layers.

# REQUIREMENTS
Linux / Windows installation

## Phase 1
In the LINZ context Topo mapsheets are produced in 1:50 or 1:250 scale mapsheets covering the land area of New Zealand. On this basis all vector layer produced by LINZ Topography are similarly constrained, during pre production, to these same mapsheet boundaries. The Topo Reblocker reads feature layers as shapefile uploading to a database backend. The database side of the application identifies intersecting vector lines and polygons and concatenates these into a single feature. The resulting feature set is returned to the user as a single layer.

## Phase 2
Since the end destination of the seamless feature sets produced by the Topo Reblocker is LDS, functionality to enable users to upload directly from the application to LDS is also provided.


# QUICKSTART

1. Unzip the reblocker.zip archive
2. Run the python executable ReblockerUI.py
3. For command line operations refer to the usage notes below

# USAGE

Command line usage:
On Windows corporate machines, put your shapefiles you want reblocked into a directly on your local machine
C:\Users\<your_user_name>\Documents\reblock_lines

Then open QGIS OSGEO4W shell, and run command like this (example):
```
python3 LayerReader.py -d C:\Users\<your_user_name>\Documents\reblock_lines -s -o -u t250_fid
```

```
python LayerReader [-h|--help]|[-c|--cropregion][-i|--import][-e|--export][-p|--process]
            [-d|--dir </shapefile/dir>][-s|--select][-l|--layer <layername>][-o|--overwrite]
            [-u|--ufid <primary-key>][-m|--merge <primary-key>][-w|--webservice][-v|--version]
            [-x/-excise][-y/--deepexcise][-r/--release][-z/--linkrelease]
-h/--help : Print out this help message
-c/--cropregion : Reload auxilliary map files
    i.e. CropRegions to subdivide area and utilise less memory when processing
-i/--import : Run Shape to PostgreSQL Only
-e/--export : Run PostgreSQL to Shape Only
-p/--process : Run Reblocking process Only
-o/--overwrite : Overwrite (imported and reblocked tables)
-s/--selection : Only process and export layers found in the import directory
-d/--dir <path> : Specifiy a shapefile import directory
-l/--layer <layer> : Specify a single layer to import/process/export
-u/--ufid <ufid> : Specify the name of the primary key field for a layer/set-of-layers
    e.g. t50_fid/t250_fid
-m/--merge <ufid> : Returns the layers using this composite ID and its components
-w/--webservice : Enable Webservice lookup for missing EPSG
-v/--version : Enable table versioning
-x/--excise : Remove named column from output shapefile
-y/--deepexcise : Remove named column from output shapefile (including all subdirectories)
-r/--release : Release reblocking data to topo_rdb
-z/--linkrelease : Link and Release reblocking data to topo_rdb
```

# MAINTENANCE

The reblocker consists of two parts. The client part where the user manages shapefiles selecting files they want to have processed. Results are typically generated back to the user as modfified shapefiles once processing completes. The server part of the applicaion is really just a database table preserving generated feature IDs and a some postgis functions that process feature joins.

## Client

The client is a Python script called LayerReader.py . Users run this directly adding options as listed above. The LayerReader module has a Shapefile and a Postgres class with read/write methods and some common utilities. The read write process basically follows the format

DS1.init('db')
DS2.init('shp')
DS1.write(DS2.read())
DS1.process()
DS2.write(DS1.read())

Notes.
1. SetupDS subverts this process
2. Gdal printed errors are caught using the @capture... decorator
3. ReblockerUI and ReblockerServer are WIP intended to provide a GUI component and push file management to a server
4. CropRegions are geographically distinct user defined regions (e.g. NI/SI) that split processing load

## Database

The database module contains functions that preprocess and filter potential reblock candidate features. The function that refines the possible features to reblock is the generate_rbl function which sequentially filters the features in a layer achieving a minimimal candidate list. The workhorse function that actually joins features together is the generate_aggrbl function. This works using a recursive aggregate that appends feature segments together. Two other important function are the ufid_generator and the ufid_sequence functions. These track whether a ufid has been assigned previously based on component fids and generates a new sequence if a set of component fids hasn't been seen before.

Once a layer has been submitted for processing the following actions occur;
1. The dataset is split between cropregion bounds
2. Round edge points so they match boundry lines (exvals)
3. A determination is made whether edge points touch mapsheet boundaries (msfilter)
4. Filter only touching points (srcpoly)
5. Cross match all layer features to see if they touch
6. Output 1-to-1 list of joins to perform. This is the "reblocklist"
7. Action notified joins


Notes.
1. Feature edges are (in part) detected based on whether they touch mapsheet boundaries. The northsouth/eastwest functions calculate these boundaries. Other boundaries are arbitrary and hardcoded in the function, nonstandard.
2. Whether edges/points touch is quite dependent on some hardcoded parameters, std_id and std_mv, which define snap-to-grid accuracy.
3. Attention should be paid to Great Barrier Island. Ask Topo about this
4. The Rename Strategy spreadheet outlines the procedure that is followed for ID renaming when a feature translates/scales or merges/splits with another feature.


```
