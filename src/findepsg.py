import sys
from osgeo import osr
import cookielib
import urllib2, urllib
import shlex
from urllib2 import Request, base64, HTTPError
from abc import ABCMeta, abstractmethod
import json



def esriprj2standards(shapeprj_path):
   prj_file = open(shapeprj_path, 'r')
   prj_txt = prj_file.read()
   srs = osr.SpatialReference()
   srs.ImportFromESRI([prj_txt])
   print 'Shape prj is: %s' % prj_txt
   print 'WKT is: %s' % srs.ExportToWkt()
   print 'Proj4 is: %s' % srs.ExportToProj4()
   srs.AutoIdentifyEPSG()
   print 'EPSG is: %s' % srs.GetAuthorityCode(None)



def wsprj2epsg(shapeprj_path):
    #http://prj2epsg.org/search.json?mode=wkt&terms=projcs%5B%22new_zealand_transverse_mercator_2000%22%2cgeogcs%5B%22gcs_nzgd_2000%22%2cdatum%5B%22d_nzgd_2000%22%2cspheroid%5B%22grs_1980%22%2c6378137.0%2c298.257222101%5D%5D%2cprimem%5B%22greenwich%22%2c0.0%5D%2cunit%5B%22degree%22%2c0.0174532925199433%5D%5D%2cprojection%5B%22transverse_mercator%22%5D%2cparameter%5B%22false_easting%22%2c1600000.0%5D%2cparameter%5B%22false_northing%22%2c10000000.0%5D%2cparameter%5B%22central_meridian%22%2c173.0%5D%2cparameter%5B%22scale_factor%22%2c0.9996%5D%2cparameter%5B%22latitude_of_origin%22%2c0.0%5D%2cunit%5B%22meter%22%2c1.0%5D%5D
    uu='http://prj2epsg.org/search.json?mode=wkt&terms='
    
    purl='127.0.0.1:3128'
    puser=None
    ppass=None
    pscheme="http"
    
    prj_file = open(shapeprj_path, 'r')
    prj_txt = prj_file.read()
    ue_txt = uu+urllib.quote(prj_txt)
    print ue_txt
    
    handlers = [
            urllib2.HTTPHandler(),
            urllib2.HTTPSHandler(),
            urllib2.ProxyHandler({pscheme: purl})
        ]
    opener = urllib2.build_opener(*handlers)
    urllib2.install_opener(opener)
    
    #ue_txt='http://www.google.com/'
    try:
        res = urllib2.urlopen(ue_txt)#,data)
        return int(json.loads(res.read())['codes'][0]['code'])
    except HTTPError as he:
        print 'SRS WS Convert Error {0}'.format(he)


    

#sriprj2standards(sys.argv[1])
wsprj2epsg(sys.argv[1])