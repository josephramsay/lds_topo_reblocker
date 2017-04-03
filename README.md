# lds_topo_reblocker
Topo Map Sheet Reblocking Scripts

# Requirements
Linux / Windows installation

# Description
The Topo Reblocker is an application used to stitch together topopgraphic mapsheets into seamless layers.

## Phase 1
In the LINZ context Topo mapsheets are produced in 1:50 or 1:250 scale mapsheets covering the land area of New Zealand. On this basis all vector layer produced by LINZ Topography are similarly constrained, during pre production, to these same mapsheet boundaries. The Topo Reblocker reads feature layers as shapefile uploading to a database backend. The database side of the application identifies intersecting vector lines and polygons and concatenates these into a single feature. The resulting feature set is returned to the user as a single layer.

## Phase 2
Since the end destination of the seamless feature sets produced by the Topo Reblocker is LDS, functionality to enable users to upload directly from the application to LDS is also provided.

# Usage

## Command Line


## GUI
