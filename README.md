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
