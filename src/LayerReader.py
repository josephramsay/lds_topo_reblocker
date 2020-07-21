'''
Layer Reader
Created on 20/10/2014
@author: jramsay

usage: python LayerReader [-h|--help]|[-c|--cropregion][-i|--import][-e|--export][-p|--process]
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
'''


import sys
import os
import re
import getopt
import psycopg2
import urllib
import json
import shutil
import warnings
from six import StringIO
from six.moves import urllib as ulib
from pprint import pprint

#Python 3
#from abc import ABC,abstractmethod

#Compatible with Python 2 *and* 3:
import abc
ABC = abc.ABCMeta('ABC', (object,), {'__slots__': ()})
abstractmethod = abc.abstractmethod

#PYVER3 = sys.version_info > (3,)
#2 to 3 imports
#if PYVER3:
#    import urllib.request as ulib
#    from urllib.error import HTTPError
#else:
#    import urllib2 as ulib
#    from urllib2 import HTTPError

try:
    import ogr, osr, gdal
except ImportError as iee:
    print(iee)
    from osgeo import ogr, osr, gdal

OVERWRITE = False
ENABLE_VERSIONING = False
DEF_SRS = 2193
USE_EPSG_WEBSERVICE = False
DST_SCHEMA = 'public'
DST_TABLE_PREFIX = 'new_'
DST_SUBDIR = '_new'
SHP_SUFFIXES = ('shp','shx','dbf','prj','cpg')

DEF_CREDS = '.pdb_credentials'
DEF_HOST = 'prdassgeo02.ad.linz.govt.nz'#127.0.0.1'
DEF_PORT = 5432

CONFIG = None
UICONFIG = None

if re.search('posix',os.name):
    DEF_SHAPE_PATH = ('/home/',)
else:
    DEF_SHAPE_PATH = ('C:\\',)

#gdal.ConfigOptions('ENCODING=UTF-8')
#this doesn't seem to work, it just makes failures silent
#gdal.UseExceptions()
GEH_MARKER = 'GDALERROR'

class GdalException(Exception): pass
class GdalStdoutCaptureException(GdalException): pass
class GdalStderrCaptureException(GdalStdoutCaptureException): pass

class GdalErrorHandler(object):
    def __init__(self,err_level=gdal.CE_None):
        self.handler(err_level,0,'')

    def handler(self, err_level, err_no, err_msg):
        self.err_level = err_level
        self.err_no = err_no
        self.err_msg = GEH_MARKER+' Error Handler '+err_msg
        if err_level>0:
            #The exception here won't be caught since this runs in a separate thread 
            #but the stdout print will if we redirect and capture
            print(self.err_msg)
            #raise GdalException(self.err_msg)

def clearGdalExceptions(): gdal.DontUseExceptions()
def setGdalException(e=True):
    old = gdal.GetUseExceptions()
    if e: 
        gdal.PushErrorHandler(GdalErrorHandler().handler)
        gdal.UseExceptions()
    else: 
        gdal.DontUseExceptions()
        gdal.PopErrorHandler()
    return old==1

def captureGdalError(func):
    def wrapCaptureAndCall(*args, **kwargs):
        stderr_fileno,stdout_fileno = sys.stderr,sys.stdout
        sys.stderr = StringIO()
        sys.stdout = StringIO()
        try:
            rv = func(*args, **kwargs)
            err = sys.stderr.getvalue()
            out = sys.stdout.getvalue()
            #if something is in stderr raise
            if err: 
                raise GdalStderrCaptureException('ERROR '+err)
            #if something is in stdout check that is been marked as an error then raise
            if out and out.startswith(GEH_MARKER): 
                raise GdalStdoutCaptureException('OUTPUT '+out)
        except RuntimeError as rune:
            raise GdalStderrCaptureException('Caught GDAL runtime error'+rune)
        except SystemError as syse:
            raise GdalStderrCaptureException('Caught GDAL sys error'+syse)
        finally:
            sys.stderr.close()
            sys.stdout.close()
            sys.stderr,sys.stdout = stderr_fileno,stdout_fileno
            #now repeat the captured errors to the console
            if err: print('x',err,end='')
            if out: print('o',out,end='')
        return rv
    return wrapCaptureAndCall



class LayerCompareException(Exception):pass

class LayerReader(object):
    _src = None
    _dst = None

    def __init__(self,s,d):
        self.dst = d #PGDS()
        self.src = s #SFDS()

    @property
    def dst(self):
        return self._dst

    @dst.setter
    def dst(self,val):
        self._dst = val

    @property
    def src(self):
        return self._src

    @src.setter
    def src(self,val):
        self._src = val

    def transfer(self,filt=None):
        '''loop through list of shapefile paths, since can provide # different paths to check'''
        return self.dst.write(self.src.read(filt))

#     def _transfer(self):
#         for spath in DEF_SHAPE_PATH:
#             for sfile in self.readdir(spath):#['shingle_poly.shp','building_poly.shp','airport_poly.shp']:
#                 self.load(os.path.join(spath,sfile))

    def purge(self,layer,pkey):
        '''Removes non majority features from layer. If #1 LINE and #10 POLYs in layer, remove the LINE'''
        for f in self.geomatch(layer):
            layer.DeleteFeature(f.GetFID())
            print ('DELETE FID {} (ufid={}) from Layer {}'.format(f.GetFID(),f.GetFieldAsInteger(pkey),layer.GetLayerDefn().GetName()))
        return layer

    def geomatch(self,layer):
        '''Loop features in layer and put geometry type (POLY/LINE etc) in fg array and return types list if not unique'''
        featgroups = {}
        feat = layer.GetNextFeature()
        while feat:
            fgn = feat.GetGeometryRef().GetGeometryName()
            if fgn not in featgroups:
                featgroups[fgn] = ()
            featgroups[fgn] += (feat,)
            feat = layer.GetNextFeature()
        if len(featgroups)>1:
            return featgroups[min([(len(featgroups[i]),i) for i in featgroups])[1]]
        return None

    def reblock(self,u=None,l=None,o=False):
        '''Call the PG reblock function to rebuild mapsheet-split layers'''
        ufid = u if u else 'ufid'
        elements = "array['{0}']".format("','".join(l)) if l else "array['']"

        qstr = "select reblockall('{0}',{1},{2})".format(ufid,elements,o)

        self.dst.connect()
        self.dst.execute(qstr)
        self.dst.disconnect()
    
    def _readdir(self,spath):
        return [fp for fp in os.listdir(spath) if re.search('.shp$',fp)]

class DatasourceException(Exception): pass

class _DS(ABC):
    FN_SPLIT = '###'
    CREATE = True
    uri = None
    dsl = {}
    driver = None
    DRIVER_NAME = None

    OGR_DS_PREFS = ["OVERWRITE=NO","GEOM_TYPE=geometry","ENCODING=UTF-8"]
    OGR_LAYER_PREFS = OGR_DS_PREFS
    
    def __init__(self):
        self.driver = ogr.GetDriverByName(self.DRIVER_NAME)
        
    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        for dsn in self.dsl:
            #print 'releasing',dsn
            if self.dsl[dsn]: self.dsl[dsn].SyncToDisk()
            self.dsl[dsn] = None
        self.dsl = None
        self.driver = None
        
    def _getdsprefs(self):
        return self.OGR_DS_PREFS
        
    def _getlayerprefs(self):
        return self.OGR_LAYER_PREFS


    def clearOverwrite(self): self.setOverwrite(False)
    def setOverwrite(self,o=True):
        global OVERWRITE
        OVERWRITE = o
        old = self.OGR_DS_PREFS[0]
        self.OGR_DS_PREFS[0] = 'OVERWRITE={}'.format('YES' if o else 'NO')
        return old=='OVERWRITE=YES'
        
    def _findSRID(self,name,sr,useweb):
        '''https://stackoverflow.com/a/10807867'''
        res = sr.AutoIdentifyEPSG()
        if res == 0:
            return sr.GetAuthorityCode(None)
        elif useweb:
            res = self._lookupSRID(sr.ExportToWkt())
            if res: return res
        print ('Warning. Layer {0} using DEF_SRS {1}'.format(name,DEF_SRS))    
        return DEF_SRS

    def _lookupSRID(self,wkt): 
        uu='http://prj2epsg.org/search.json?mode=wkt&terms='

        purl='127.0.0.1:3128'
        pscheme="http"
        
        uuwkt = uu + ulib.parse.quote(wkt)
        
        handlers = [
                ulib.request.HTTPHandler(),
                ulib.request.HTTPSHandler(),
                ulib.request.ProxyHandler({pscheme: purl})
            ]
        opener = ulib.request.build_opener(*handlers)
        ulib.request.install_opener(opener)
        
        try:
            res = ulib.request.urlopen(uuwkt)
            return int(json.loads(res.read())['codes'][0]['code'])
        except ulib.error.HTTPError as he:
            print ('SRS WS Convert Error {0}'.format(he))
        
    
    def initalise(self,dsn=None,create=True):
        ds = None
        try:
            upd = 1 if OVERWRITE else 0
            #ds = self.driver.Open(dsn, upd)
            #print ('DSN',dsn)
            ds = ogr.Open(dsn, upd)
            if ds is None:
                raise DatasourceException('Null DS {}'.format(dsn))
        except (RuntimeError, DatasourceException,Exception) as re1:
            if re.search('HTTP error code : 404',str(re1)):
                return None

            if self.CREATE: 
                try:
                    ds = self.create(dsn)
                except RuntimeError as re2:
                    raise DatasourceException('Cannot CREATE DS with {}. {}'.format(dsn,re2))
            else:
                raise DatasourceException('Cannot OPEN DS with {}. {}'.format(dsn,re1))
        finally:
            pass
            #ogr.UseExceptions()
        #print ('DS',ds)
        return ds

    @abstractmethod
    def connect(self): pass
    
    @abstractmethod
    def disconnect(self): pass
    
    @abstractmethod
    def execute(self,qstr,results=True): pass

    @abstractmethod
    def read(self,filt): pass

    @abstractmethod
    def write(self): pass
    
    def create(self,dsn):
        ds = None
        try:
            ds = self.driver.CreateDataSource(dsn, self._getdsprefs())
            if ds is None:
                raise DatasourceException("Error opening/creating DS "+str(dsn))
        except DatasourceException:
            raise
        except RuntimeError:
            '''this is only caught if ogr.UseExceptions() is enabled (which we dont enable since RunErrs thrown even when DS completes)'''
            raise
        return ds

    def layerCompare(self,layer1,layer2,count1=0,count2=0):
        comp1 = {
            'n':layer1.GetName(),
            'g':layer1.GetGeomType(),
            's':layer1.GetSpatialRef().GetName(),
            'fc':layer1.GetFeatureCount(),
            'lc':count1
                }
        comp2 = {
            'n':layer2.GetName(),
            'g':layer2.GetGeomType(),
            's':layer2.GetSpatialRef().GetName(),
            'fc':layer2.GetFeatureCount(),
            'lc':count2
                }
        #Because GDAL isnt returning errors to indicate whether a layer copy failed or not we have to assume failure when 
        #the name, geometry or feature counts of the before and after layers is different

        #if any of these are different                           and if any of these are the same (lc2>lc1)
        #LOGIC
        #if the layer counts are different a new layer has been created and we check if pg(new) matches shp
        #if the layer counts are the same the create part of the copy failed. Did the rows get copied?
        if comp1['lc']==comp2['lc']:
            if any([comp1[i]!=comp2[i] for i in ['n','g','fc']]):
                raise LayerCompareException('Layer Comparison Exception',comp1,comp2)
        elif comp1['lc']<comp2['lc']:
            #have a new layer. Did the rows copy
            if any([comp1[i]!=comp2[i] for i in ['g','fc']]) or comp1['n'].lstrip(DST_TABLE_PREFIX)!= comp2['n'].lstrip(DST_TABLE_PREFIX):
                raise LayerCompareException('Layer Comparison Exception. CreateLayer Succeeded, CopyLayer Failed',comp1,comp2)


    def featureCompare(self,layer1,layer2):
        '''Check for macrons persisting across copy operations'''
        for f1 in layer1.GetFeatures():
            for f2 in layer2.GetFeatures():
                pass


class PGDS(_DS):
    INIT_VAL = 1
    DRIVER_NAME = 'PostgreSQL'
    DBNAME = 'reblock'
    CS_TMPLT = "dbname='{2}' host='{0}' port='{1}' user='{3}' password='{4}'"

    OGR_DS_PREFS = ["OVERWRITE=NO","GEOM_TYPE=geometry","ENCODING=UTF-8"]
    OGR_LAYER_PREFS = OGR_DS_PREFS

    cur = None
    conn = None
    connectionstring = None
    
    def __init__(self,fname=None,dbn=None):
        super(PGDS,self).__init__()
        if dbn: self.DBNAME = dbn
        #print 'PGDS',fname,dbn
        if fname: self._parseConnectionString(fname)
        else: fname = self.ogrconnstr()
        self.dsl = {fname:self.initalise(fname, True)}
        
    def __enter__(self):
        self.connect()
        return super(PGDS,self).__enter__()
    
    def __exit__(self, type, value, traceback):
        self.disconnect()
        return super(PGDS,self).__exit__(type, value, traceback)
        
    
    '''this is getting a bit confusing, a connection string shall be "PG: host/db etc &active_schema" and accept PG or plain formats as input'''
    def _parseConnectionString(self,cs):
        #TODO validation
        if cs.startswith('PG'): self.connectionstring = cs
        else: self.connectionstring = 'PG:{} active_schema={}'.format(cs,DST_SCHEMA)
            
    def ogrconnstr(self):
        return self.connectionstring or 'PG:{} active_schema={}'.format(self.connstr(),DST_SCHEMA)
        
    def connstr(self):
        if self.connectionstring: return self.connectionstring.split(':')[1].split('active_schema')[0].rstrip()
        go = self._getopts()
        return PGDS.CS_TMPLT.format(go['HOST'],go['PORT'],go['DBNAME'],go['USER'],go['PASS'],)

    def _getopts(self):
        usr,pwd = CredsReader.userpass(DEF_CREDS)
        h,p = CredsReader.hostport(DEF_CREDS)
        return {'DBNAME':self.DBNAME,'HOST':h if h else DEF_HOST,'PORT':p if p else DEF_PORT,'USER':usr,'PASS':pwd}
    
    def connect(self):
        if not self.cur:
            self.conn = psycopg2.connect(self.connstr())
            self.cur = self.conn.cursor()
        
    def execute(self,qstr,results=False):
        success = self.cur.execute(qstr)
        return self.cur.fetchall() if results else not success or success
        
    def disconnect(self):
        self.cur.close()
        self.conn.commit()

    def read(self,filt):
        '''Read PG tables'''
        layerlist = {}
        #print ('DSL',self.dsl)
        for dsn in self.dsl:
            #print ('dsn',dsn)
            #print ('count',self.dsl[dsn].GetLayerCount())
            for index in range(self.dsl[dsn].GetLayerCount()):
                layer = self.dsl[dsn].GetLayerByIndex(index)
                name = layer.GetLayerDefn().GetName()
                #print ('PGLN',name)
                if name.find(DST_TABLE_PREFIX)==0 \
                and self._tname(name):
                    #checks if (table)name is part of or in any of the filter items
                    if not filt or max([1 if DST_TABLE_PREFIX + f == name else 0 for f in filt]) > 0: 
                        srid = self._findSRID(name,layer.GetSpatialRef(),USE_EPSG_WEBSERVICE)
                        layerlist[(dsn,name,srid)] = layer
        return layerlist
    
    def _tname(self,name):
        '''Debugging shortcut to add list of tables for export'''
        return True
        #return name.find('new_contour')==0
     
    def write(self,layerlist):
        '''Attempts to write/copy contents of layerlist using copylayer|per-feat methods'''
        try:
            old_ow = self.setOverwrite()
            succ1,fail1 = self.writeLayer(layerlist)
            if fail1: 
                succ2,fail2 = self.writeFeature(fail1)
                if fail2:
                    if len(fail1) == len(fail2)== len(layerlist):
                        raise LayerCompareException('No layers written')
                    else: return succ1+succ2   
        except Exception as e:
            print(e)
            raise
        finally:
            self.setOverwrite(old_ow)
        return layerlist


    def writeLayer(self,layerlist):
        '''PG write writes to a single DS since a DS represents a DB connection. SRID not transferred!'''
        successes,failures = {},{}
        try:
            self.connect()
            for dsn in layerlist:
                try:
                    #print 'PG create layer {}'.format(dsn[1])
                    writeto = list(self.dsl.values())[0]
                    c1 = writeto.GetLayerCount()
                    sridq = "select UpdateGeometrySRID('{}','wkb_geometry',{})".format(dsn[1].lower(),dsn[2])

                    writeto.CopyLayer(layerlist[dsn],dsn[1],self._getlayerprefs())
                    writeto.ExecuteSQL(sridq)

                    c2 = writeto.GetLayerCount()
                    lastlayer = writeto.GetLayer(c2-1)

                    self.layerCompare(layerlist[dsn],lastlayer,c1,c2)
                    successes[dsn] = layerlist[dsn]
                except LayerCompareException as lce:
                    '''This indicates that copylayer failed and we should revert to the feature/feature copy method'''
                    print(lce)
                    failures[dsn] = layerlist[dsn]
                except Exception:
                    raise
        finally:
            self.disconnect()
        return successes,failures
    
    def writeFeature(self,layerlist):
        '''HACK to retain SRS 
        https://gis.stackexchange.com/questions/126705/how-to-set-the-spatial-reference-to-a-ogr-layer-using-the-python-api'''
        successes,failures = {},{}
        for dsn in layerlist:
            try:
                (datasource,layername,geomtype,preferences) = list(self.dsl.values())[0],dsn[1],layerlist[dsn].GetLayerDefn().GetGeomType(),self._getdsprefs()
                #print 'PG create layer {}'.format(dsn[1])
                dstsrs = osr.SpatialReference()
                dstsrs.ImportFromEPSG(int(dsn[2]))
                c1 = datasource.GetLayerCount()

                try:
                    dstlayer = datasource.CreateLayer(layername,dstsrs,geomtype,preferences)
                    #dstlayer = list(self.dsl.values())[0].CreateLayer(dsn[1],dstsrs,layerlist[dsn].GetLayerDefn().GetGeomType(),self._getdsprefs())
                except ValueError as ve:
                    print ('Error Creating Layer on Datasource {}. {}'.format(dsn[1],ve))

                # adding fields to new layer
                layerdef = ogr.Feature(layerlist[dsn].GetLayerDefn())
                for i in range(layerdef.GetFieldCount()):
                    dstlayer.CreateField(layerdef.GetFieldDefnRef(i))
                
                # adding the features from input to dest
                c1 = layerlist[dsn].GetFeatureCount()
                for i in range(0, c1):
                    feature = layerlist[dsn].GetFeature(i)
                    try:
                        dstlayer.CreateFeature(feature)
                    except ValueError as ve:
                        print ('Error Creating Feature on Layer {}. {}'.format(dsn[1],ve))
                        
                self.layerCompare(layerlist[dsn],dstlayer,c1,datasource.GetLayerCount())
                successes[dsn] = layerlist[dsn]
            except LayerCompareException as lce:
                print(lce)
                failures[dsn] = layerlist[dsn]
            except Exception:
                raise
        return successes,failures
        
class PGDS_Version(PGDS):
    '''table versioning for PG'''
    def __init__(self,fname=None):
        super(PGDS_Version,self).__init__()

    def execute(self,qstr):
        edittext = self._genVerText()
        self.cur.execute("SELECT table_version.ver_create_revision('{0}');".format(edittext))
        res = self.cur.execute(qstr)
        self.cur.execute("SELECT table_version.ver_complete_revision();")
        return res
    
    def _genVerText(self):
        return 'this is my edit'
    
    def _enableVer(self,schema,table):
        self.cur.execute("SELECT table_version.ver_enable_versioning('{0}', '{1}');".format(schema,table))
    
    def _disableVer(self,schema,table):
        self.cur.execute("SELECT table_version.ver_disable_versioning('{0}', '{1}');".format(schema,table))


class SFDS(_DS):
    
    INIT_VAL = 1
    DRIVER_NAME = 'ESRI Shapefile'

    OGR_DS_PREFS = []
    OGR_LAYER_PREFS = ["OVERWRITE=NO","GEOM_TYPE=geometry","ENCODING=UTF-8"]
    
    def __init__(self,fname=None):
        super(SFDS,self).__init__()
        #print 'SFDS',fname
        self._initpath(fname)
        
    def _initpath(self,fname):
        self.shppath = DEF_SHAPE_PATH
        if fname: 
            if os.path.isdir(fname):
                #if provided fname is a directory make this the source path
                self.shppath = (fname,)
                #and init all the files in this directory
                self.dsl = self._getFileDS()
            else:
                #if fname is a file init this alone
                fname = os.path.normpath(os.path.join(os.path.dirname(__file__),fname))
                self.dsl = {fname:self.initalise(fname, True)}
        else:
            self.dsl = self._getFileDS()
    
    def connstr(self):
        #TODO do something intelligent here like read from a def dir?
        return 'shapefile.shp'
    
    def readdir(self,spath):
        return [fp for fp in os.listdir(spath) if re.search('.shp$',fp)]
        
    def _getFileDS(self):
        '''loop directories + shapefiles + layers'''
        shplist = {}
        for spath in self.shppath:
            for sfile in self.readdir(spath):#['shingle_poly.shp','building_poly.shp','airport_poly.shp']:
                shpname = os.path.join(spath,sfile)
                #recursive so potentially problematic on nested directories
                shplist[shpname] = SFDS(shpname).dsl[shpname]
        return shplist
        
    def connect(self):
        pass

    def disconnect(self):
        pass
    
    def execute(self,qstr):
        pass

    def read(self,filt):
        '''Shapefile reader'''
        layerlist = {}
        for dsn in self.dsl:
            for index in range(self.dsl[dsn].GetLayerCount()):
                layer = self.dsl[dsn].GetLayerByIndex(index)
                name = layer.GetLayerDefn().GetName()
                #print ('SFLN',name)
                #checks if name is part of in any if the filter items
                if not filt or max([1 if f in name else 0 for f in filt])>0: 
                    srid = self._findSRID(name,layer.GetSpatialRef(),USE_EPSG_WEBSERVICE)
                    layerlist[(dsn,name,srid)] = layer
        return layerlist

    def write(self,layerlist,cropcolumn=None):
        '''Attempt to two different write/copy methods'''
        try:
            succ1,fail1 = self.writeLayer(layerlist,cropcolumn)
            if fail1: 
                #succ2,fail2 = self.writeLayerAlt(fail1,cropcolumn)
                succ2,fail2 = self.writeFeature(fail1,cropcolumn)
                if fail2:
                    if len(fail1) == len(fail2)== len(layerlist):
                        raise LayerCompareException('No layers written')
                    else: return succ1+succ2
        except Exception as e:
            print(e)
            raise
        return layerlist

    def setupDS(self,dsn):
        srcname = re.sub('^'+DST_TABLE_PREFIX,'',dsn[1])
        srcpath = os.path.abspath(self.shppath[0]+DST_SUBDIR)
        srcfile = os.path.abspath(os.path.join(srcpath,srcname+'.shp'))
        if not os.path.exists(srcpath): os.mkdir(srcpath)
        if os.path.exists(srcfile): self.driver.DeleteDataSource(srcfile)
        return srcname,self.driver.CreateDataSource(srcfile,self._getdsprefs())

    def writeLayer(self,layerlist,cropcolumn):
        '''TODO. Write new shp per layer overwriting existing'''
        #set gdal exceptions to catch unicode errors
        old = setGdalException()
        successes,failures = {},{}
        for dsn in layerlist:
            try:
                srcname,dstds = self.setupDS(dsn)
                #dstds = self.driver.Create(srcfile,self._getdsprefs())
                c1 = dstds.GetLayerCount()
                cpy = self._copyLayer_wrapper(dstds,layerlist,dsn,srcname)
                #this section hacked in to add delete column functionality
                if cropcolumn:
                    col = cpy.GetLayerDefn().GetFieldIndex(cropcolumn)
                    cpy.DeleteField(col)
                self.layerCompare(layerlist[dsn],cpy,c1,dstds.GetLayerCount())
                successes[dsn] = layerlist[dsn]
            except Warning as w:
                #this is supposed to catch gdal warnings...
                print (w)
            except RuntimeError as rune:
                #this is supposed to catch gdal errors with GdalExceptions turned on...
                print (rune)
            except GdalStdoutCaptureException as goc:
                failures[dsn] = layerlist[dsn]
            except LayerCompareException as lce:
                '''This indicates that copylayer failed and we should revert to the feature/feature copy method'''
                print(lce)
                failures[dsn] = layerlist[dsn]
            except Exception:
                raise
            finally:
                #now set gdal exceptions back to what they were previously
                setGdalException(old)
                dstds.SyncToDisk()
                dstds.Destroy()
        return successes,failures

    @captureGdalError
    def _copyLayer_wrapper(self,dstds,layerlist,dsn,srcname):
        return dstds.CopyLayer(layerlist[dsn],srcname,self._getlayerprefs())
        
    @captureGdalError
    def _createFeature_wrapper(self,dstlyr,feature):
        return dstlyr.CreateFeature(feature)
        
    @captureGdalError
    def _createFeatureOverwrite_wrapper(self,dstlyr,feature):
        dstlyr.CreateFeature(feature)
        newfeat = self._overwriteField(feature,dstlyr.GetFeature(feature.GetFID()-1))
        if newfeat: 
            dstlyr.DeleteFeature(feature.GetFID())
            dstlyr.CreateFeature(newfeat)



    def writeFeature(self,layerlist,cropcolumn):
        '''Per-feature writer'''
        copyFeature  = self._createFeature_wrapper
        cfid = id(copyFeature)
        successes,failures = {},{}
        for dsn in layerlist:
            old = setGdalException()
            try:
                #dstds = self.dsl.values()
                dstname,dstds = self.setupDS(dsn)
                geomtype,preferences = layerlist[dsn].GetLayerDefn().GetGeomType(),self._getlayerprefs()
                #print 'PG create layer {}'.format(dsn[1])
                dstsrs = osr.SpatialReference()
                dstsrs.ImportFromEPSG(int(dsn[2]))
                c1 = dstds.GetLayerCount()

                try:
                    dstlayer = dstds.CreateLayer(dstname,dstsrs,geomtype,preferences)
                    #dstlayer = list(self.dsl.values())[0].CreateLayer(dsn[1],dstsrs,layerlist[dsn].GetLayerDefn().GetGeomType(),self._getdsprefs())
                except ValueError as ve:
                    print ('Error Creating Layer on Datasource {}. {}'.format(dsn[1],ve))

                # adding fields to new layer
                layerdef = ogr.Feature(layerlist[dsn].GetLayerDefn())
                for i in range(layerdef.GetFieldCount()):
                    dstlayer.CreateField(layerdef.GetFieldDefnRef(i))
                
                # adding the features from input to dest
                
                layerlist[dsn].ResetReading()
                feature = layerlist[dsn].GetNextFeature()
                while feature:
                    try:
                        assert cfid == id(copyFeature), 'CopyFeature check fail'
                        copyFeature(dstlayer,feature)
                    except GdalStdoutCaptureException as goc:
                        # the utf-8 error only gets reported once so we have to assume every subsequent call has failed too
                        # thats why we swap out the create-layer function with the create-overwrite-field one 
                        copyFeature = self._createFeatureOverwrite_wrapper
                        cfid = id(copyFeature)
                        #Now just try and fix the incorrect but already written feature
                        try:
                            self._overwriteField(feature,dstlayer.GetFeature(feature.GetFID()-1))
                        except Exception as e:
                            print('Field copy didn\'t work, bailing out',e)
                            raise
                        
                        #copyFeature(dstlayer,feature)
                        #failures[dsn] = layerlist[dsn]
                    except ValueError as ve:
                        print ('Error Creating Feature on Layer {}. {}'.format(dsn[1],ve))
                    feature = layerlist[dsn].GetNextFeature()

                c2 = layerlist[dsn].GetFeatureCount()

                self.layerCompare(layerlist[dsn],dstlayer,c1,c2)
                successes[dsn] = layerlist[dsn]
            except LayerCompareException as lce:
                print(lce)
                failures[dsn] = layerlist[dsn]
            except Exception:
                raise
            finally:
                #now set gdal exceptions back to what they were previously
                setGdalException(old)
                dstds.SyncToDisk()
                dstds.Destroy()
        return successes,failures

    def _overwriteField(self,srcfeat,dstfeat):
        #macvowels = ['u0100','u0101','u0112','u0113','u012A','u012B','u014C','u014D','u016A','u016B']
        ffield = []
        sfc = srcfeat.GetFieldCount()
        for i in range(0,sfc):
            fvalue = srcfeat.GetFieldAsString(i)
            fname = srcfeat.GetFieldDefnRef(i).name
            ftype = srcfeat.GetFieldDefnRef(i).type
            ffield.append( {'n':fname,'t':ftype,'v':fvalue,'i':i} )
        pprint(ffield)
        if any([f['n'] == 'macronated' and f['v'] == 'Y' for f in ffield]):
            value = [(f['i'],f['v'].encode('utf-8')) for f in ffield if f['n'] == 'name' and f['t'] == 4][0]
            dstfeat.SetFieldString(value[0],value[1])
            print('Write',value[1],'-> Read',dstfeat.GetFieldAsString(value[0]))
            #assert dstfeat.GetFieldAsString(value[0]) == value[1], 'Unequal written fields'
            return dstfeat
        return None

    def writeLayerAlt(self,layerlist,cropcolumn):
        '''Alternative shape writer, still uses copylayer'''
        successes,failures = {},{}
        for dsn in layerlist:
            #dsn = ("PG:dbname='reblock' host='127.0.0.1' port='5432' active_schema=public", 'new_native_poly')
            #srcname = dsn[1].split('.')[-1]
            srcname = re.sub('^'+DST_TABLE_PREFIX,'',dsn[1])
            #srcfile = os.path.abspath(os.path.join(self.shppath[0],'..'))#,srcname+'.shp'))
            srcfile = os.path.abspath(self.shppath[0]+DST_SUBDIR)#,srcname+'.shp'))
            if not os.path.exists(srcfile): os.mkdir(srcfile)
            #srcsrs = layerlist[dsn].GetSpatialRef()
            try:
                if OVERWRITE:
                    try:
                        self.driver.DeleteDataSource(srcfile)
                    except:
                        for suf in SHP_SUFFIXES:
                            f = '{0}/{1}.{2}'.format(srcfile,srcname,suf)
                            if os.path.isfile(f): 
                                try: os.remove(f)
                                except : shutil.rmtree(f, ignore_errors=True)
                dstds = self.driver.CreateDataSource(srcfile,self._getdsprefs())
                #dstds = self.driver.Create(srcfile,self._getdsprefs())
                c1 = dstds.GetLayerCount()
                self._copyLayer_wrapper(dstds,layerlist,dsn,srcname)
                #dstds.CopyLayer(layerlist[dsn],srcname,self._getlayerprefs())

                c2 = dstds.GetLayerCount()
                lastlayer = dstds.GetLayer(c2-1)
                self.layerCompare(layerlist[dsn],lastlayer,c1,c2)
                successes[dsn] = layerlist[dsn]
            except LayerCompareException as lce:
                print(lce)
                failures[dsn] = layerlist[dsn]
        return successes,failures
       
class Reporter(object):
    def __init__(self):
        pass
        
    
    def getComponents(self,id):
        res = None
        qstr = "select ts,layer,ufid_components from rbl_associations where ufid = {}".format(id)
        with PGDS() as pgds:
            pgds.connect()
            res = pgds.execute(qstr,results=True)
            
        for line in res:
            print ('ID {} in Layer {} contains segments {}  -  (constructed on {})'.format(id,line[1],line[2],line[0]))
        
        
#   -----------------------------------------------------------------------------------------------

class CredsReader(object):
    '''Class reading named credentials file contains KV pairs, provides conveninece UP, HP and API'''
    
    @classmethod
    def userpass(cls,upfile):
        return (cls.searchfile(upfile,'username'),cls.searchfile(upfile,'password'))
    
    @classmethod
    def hostport(cls,upfile):
        return (cls.searchfile(upfile,'host'),cls.searchfile(upfile,'port'))
    
    @classmethod
    def apikey(cls,kfile):
        return cls.searchfile(kfile,'key')
    
    @classmethod
    def creds(cls,cfile):
        '''Read CIFS credentials file'''
        return (cls.searchfile(cfile,'username'),cls.searchfile(cfile,'password'),cls.searchfile(cfile,'domain','WGRP'))
    
    @classmethod
    def searchfile(cls,sfile,skey,default=None):
        try:
            with open(sfile,'r') as h:
                for line in h.readlines():
                    k = re.search('^{key}=(.*)$'.format(key=skey),line)
                    if k: return k.group(1)
        except FileNotFoundError:
            return CredsReader._walk(sfile,skey,default,'..')
        return default

    @classmethod
    def _walk(cls,sfile,skey,default,dir):
        '''Simple directory walker looking for named file in all sub dirs'''
        for p,_,f in os.walk(dir):
            if sfile in f: 
                return CredsReader.searchfile(os.path.join(p,sfile), skey, default)
        raise FileNotFoundError('File not found during directory walk of {}'.format(dir))

def initds(ds,arg=None):
    '''load an initial DS (for example a postgres connection) if required'''
    return ds(arg) if arg else ds()
    #return ds() if ds.INIT_VAL else None



def main():
    global OVERWRITE
    global OGR_COPY_PREFS
    global USE_EPSG_WEBSERVICE            
    global ENABLE_VERSIONING
    
    switch = None
    
    spath = None
    layer = None
    ufidname = 'unknown'
    loadcropregions = False
    actionflag = 7
    selectflag = False
    
    try:
        opts, _ = getopt.getopt(sys.argv[1:], "hcieposd:l:u:m:wvnxyrz", ["help","cropregion","import","export","process","overwrite","selection","dir=","layer=","ufid=","merge=","webservice","version","nolaunder","excise","deepexcise","release","linkrelease"])
    except getopt.error as msg:
        usage(msg)
        sys.exit(2)
    
    #do the help check first
    if any([True for i in opts if re.search('-h',i[0])]):
        print (__doc__)
        sys.exit(0)
        
    #opts
    for o, a in opts:
        if o in ("-h", "--help"):
            print (__doc__)
            sys.exit(0)
        if o in ("-c", "--cropregion"):
            loadcropregions = True        
        if o in ("-i", "--import"):
            actionflag = 1        
        if o in ("-e", "--export"):
            actionflag = 2 
        if o in ("-p", "--process"):
            actionflag = 4
        if o in ("-o", "--overwrite"):
            OVERWRITE = True
            #OGR_COPY_PREFS[0] = 'OVERWRITE=YES'
        if o in ("-s","--select"):
            selectflag = True
        if o in ("-d", "--dir"):
            spath = a
            print ('Setting spath to:',spath)
        if o in ("-l", "--layer"):
            layer = [a,]
        if o in ("-u", "--ufid"):
            if not a.islower():
                ufidname = a.lower()
                print ('Converting UC "{}" FID to LC "{}"'.format(a,ufidname))
            else: ufidname = a
        if o in ("-m","--merged"):
            r = Reporter()
            r.getComponents(a)
            sys.exit(0)
        if o in ("-w", "--webservice"):
            USE_EPSG_WEBSERVICE = True
        if o in ("-v", "--version"):
            ENABLE_VERSIONING = True
        if o in ("-n","--nolaunder"):
            pass
            #dont do this, bad things happen
            #OGR_COPY_PREFS.append('LAUNDER=NO')
        if o in ("-x","--excise"):
            switch = 'CROP'
        if o in ("-y","--deepexcise"):
            switch = 'DEEPCROP'
        if o in ("-r","--release"):
            switch = 'RELEASE'
        if o in ("-z","--linkrelease"):
            switch = 'LINKRELEASE'
        
    if switch == 'CROP':
        crop(spath,ufidname)
    elif switch == 'DEEPCROP':
        deepcrop(spath,ufidname)
    elif switch == 'RELEASE':
        release(link=False)
    elif switch == 'LINKRELEASE':
        release(link=True)
    else:
        convertImpl(spath,layer,ufidname,actionflag,selectflag,loadcropregions)
       
def setConfig(uiconfig,config):
    global CONFIG
    CONFIG = config
    global UICONFIG
    UICONFIG = uiconfig

def convert(uiconfig,config):
    setConfig(uiconfig,config)
    #setOverwrite(uiconfig.opt_overwrite)
    global OVERWRITE
    OVERWRITE = uiconfig.opt_overwrite
    # layer [A2] set to None since never used and acts as filter
    # actionflag [A4] set to 7=import/process/export
    # selectflag [A5] set to True = only process shp in dir
    convertImpl(uiconfig.val_dir,None,uiconfig.val_fid,7,True,uiconfig.opt_cropreg)
    
def convertImpl(spath,layer,ufidname,actionflag,selectflag,loadcropregions):            
    #actionflag = 2
    #inlayers=['airport_poly','lake_poly','railway_cl']  
    inlayers = ()
    
    if ENABLE_VERSIONING:
        PXDS = PGDS_Version
    else:
        PXDS = PGDS
        
    '''Initialise source and dest DS objects'''
    if loadcropregions:
        lr = LayerReader(initds(SFDS,'CropRegions.shp'),initds(PXDS))
        lr.transfer()
             
    # UPLOAD. Transfer shapefiles up to DB and call reblocker 
    if actionflag & 1:
        print ('Transfer Shape -> PostgreSQL')
        with SFDS(spath) as sfds:
            with PXDS() as pxds:
                lr = LayerReader(sfds,pxds)
                inlayers = [k[1] for k in lr.transfer(layer)]
        #lr = LayerReader(initds(SFDS,spath),initds(PXDS))
        #inlayers = [k[1] for k in lr.transfer(layer)]
    
    # REBLOCK
    if actionflag & 4:
        print ('Reblock PG Layers')
        with PXDS() as pxds:
            lr = LayerReader(None,pxds)
            lchoose = layer if layer else (inlayers if selectflag else None)
            lr.reblock(u=ufidname,l=lchoose,o=OVERWRITE)
        #lr = LayerReader(None,initds(PXDS))
        #lchoose = layer if layer else (inlayers if selectflag else None)
        #lr.reblock(u=ufidname,l=lchoose,o=OVERWRITE)
        
    # DOWNLOAD. Write reblocked tables out to shapefile
    if actionflag & 2:
        print ('Transfer PostgreSQL -> Shape')
        with SFDS(spath) as sfds:
            with PXDS() as pxds:
                lr = LayerReader(pxds,sfds)
                inlayers = inlayers if inlayers else [i[i.rfind('/')+1:i.rfind('.')] for i in lr.dst.dsl]
                [k[1] for k in lr.transfer(inlayers if selectflag else layer)]
        #lr = LayerReader(initds(PXDS),initds(SFDS,spath))
        #inlayers = inlayers if inlayers else [i[i.rfind('/')+1:i.rfind('.')] for i in lr.dst.dsl]
        #outlayers = [k[1] for k in lr.transfer(inlayers if selectflag else layer)]
        
def deepcrop(spath,ufidname):
    '''Does a fid crop on a directory incl subs'''
    for (sub, _, _) in os.walk(spath):
        if not re.search(DST_SUBDIR,sub): crop(sub,ufidname)
    
def crop(spath,ufidname):
    '''strips out a names column from shapefile'''
    with SFDS(spath) as sfds:
        sfds.write(sfds.read(None),ufidname)
        
def release(link=False):
    '''Links/Releases (reblock->topoview) copy of latest reblock tables for public consumption'''
    qlist = ('select release_topo_layers()',)
    if link: qlist = ('select link_topo_layers()',)+qlist
    with PGDS(dbn='topo_rdb') as pgds:
        pgds.connect()
        for qstr in qlist:
            res = pgds.execute(qstr,results=True)
            print ('Release return code for "{}" = {}'.format(qstr,res or 'OK'))
        pgds.disconnect()
            
def usage(msg):
    print (msg,'\n'+'-'*50,__doc__)
    
if __name__ == '__main__':
    main()
    
'''
TODO
1. Transfer SRS from src to dst, extract srid from spatialref. ANS Use Webservice lookup with enable option
2. ERROR. updategeometrysrid() not working on cropregions table. ANS. args are case sensitive! use .lower()
3. FEAT. Versioning. Using PxDS version wrapper. Not appropriate while input/output is shapefile

'''