# coding=utf-8
'''
v.0.0.1

lds_topo_reblocker - LayerReader_Test

Copyright 2011 Crown copyright (c)
Land Information New Zealand and the New Zealand Government.
All rights reserved

This program is released under the terms of the new BSD license. See the 
LICENSE file for more information.

Tests on LayerReader class

Created on 30/01/2017

@author: jramsay
'''

import unittest
import inspect
import sys
import re
import os
import yaml

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'../src')))

from Logger import Logger
from LayerReader import LayerReader, initds, SFDS, PGDS

testlog = Logger.setup('test')

def config():
    connstr = "PG: dbname='{d}' host='{h}' port='{p}' user='{u}' password='{x}' active_schema={s}"
    connstr = "PG: dbname='{d}' user='{u}' password='{x}' active_schema={s}"
    p = {'host':'localhost','database':'','port':5432,'username':'','password':'','schema':'public'}
    #TorL = {'travis':{'host':'127.0.0.1','database':'','port':5432,'username':'','password':'','schema':'public'},
    #        'local' :{'host':'<dev.server>','database':'<dev.db>','port':5432,'username':'','password':'','schema':'<dev.schema>'}}
    #p = TorL['travis' if os.getenv('TRAVIS') else 'local']
    
    with open(os.path.join(os.path.dirname(__file__),"database.yml"), 'r') as dby:
        try:
            p.update(yaml.load(dby)['postgres'])
        except yaml.YAMLError as exc:
            print(exc)
            
    return connstr.format(h=p['host'],d=p['database'],p=p['port'],u=p['username'],x=p['password'],s=p['schema'])


class Test_0_LayerReaderSelfTest(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
    
    def test10_selfTest(self):
        #assertIsNotNone added in 3.1
        self.assertNotEqual(testlog,None,'Testlog not instantiated')
        testlog.debug('LayerReader_Test Log')
    
    def test20_layerReaderInit(self):
        #assertIsNotNone added in 3.1        
        testlog.debug('Test_0.20 LayerReader instantiation test')
        self.assertNotEqual(LayerReader(None,None),None,'LayerReader not instantiated')
        
class Test_4_LayerReaderConfigTest(unittest.TestCase):    
    '''Test LayerReader functions'''
        
    def setUp(self):
        pgds = PGDS(config())
        self.layerreader = LayerReader(initds(SFDS,'CropRegions.shp'),pgds)
        
    def tearDown(self):
        self.layerreader = None
        
    def test10_layerReaderInit(self):
        self.assertNotEqual(self.layerreader,None,'LayerReader not instantiated')
        
    def test20_layerReaderInit(self):
        self.assertNotEqual(self.layerreader,None,'LayerReader not instantiated')
    
class Test_1_PGDS(unittest.TestCase):

    def setUp(self):
        self.pgds = PGDS(config())

    def tearDown(self):
        self.pgds = None

    def test10_pgdsInit(self):
        self.assertNotEqual(self.pgds, None, 'PG DS not instantiated')

    def test20_pgdsNormalConnect(self):
        self.pgds.connect()
        self.assertNotEqual(self.pgds.cur, None, 'PG Cursor not instantiated')
        self.pgds.disconnect()

    def test30_pgdsContextConnect(self):
        with PGDS(config()) as pgds:
            self.assertNotEqual(pgds.cur, None, 'PG context Cursor not instantiated')

    def test40_pgdsExecuteTF(self):
        with PGDS(config()) as pgds:
            res = pgds.execute('select 100', False)
            self.assertEqual(res, True, "Execute doesn't return success")

    def test41_pgdsExecuteRes(self):
        with PGDS(config()) as pgds:
            res = pgds.execute('select 200', True)
            self.assertEqual(res[0][0], 200, 'Execute returns wrong result')
            
    def test50_pgdsRead(self):
        with PGDS(config()) as pgds:
            res = pgds.read(None)
            self.assertNotEqual(res,{},'No results from PG read')
            self.assertEqual(list(res.keys())[0][1] ,'new_test_pt', 'Error matching PG layerlist keys')
            
class Test_2_SFDS(unittest.TestCase):

    DEF_TEST_SHP = '../CropRegions.shp'
    def setUp(self):
        self.sfds = SFDS(self.DEF_TEST_SHP)

    def tearDown(self):
        self.sfds = None
        
    def test10_sfdsInit(self):
        self.assertNotEqual(self.sfds, None, 'SF DS not instantiated')
        
    def test20_sfdsRead(self):
        with SFDS(self.DEF_TEST_SHP) as sfds:
            res = sfds.read(None)
            self.assertNotEqual(res,{},'No results from SF read')
            self.assertEqual(list(res.keys())[0][1] ,'CropRegions', 'Error matching SF layerlist keys')
        
        
if __name__ == "__main__":
    unittest.main()
