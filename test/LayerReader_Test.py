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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'../src')))

from Logger import Logger
from LayerReader import LayerReader, initds, SFDS, PGDS


testlog = Logger.setup('test')
PGCONNSTR = "PG: dbname='{d}' host='{h}' port='{p}' user='{u}' password='{x}' active_schema={s}"
#1:['127.0.0.1','template1',5432,'postgres','password','public'],
PP = {1:['127.0.0.1','test_db',5432,'test_user','test_pass','public'],
      2:['127.0.0.1','test_db',5432,'test_user','test_pass','public']}
P = PP[1 if os.getenv('TRAVIS') else 2]


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
        
class Test_1_LayerReaderConfigTest(unittest.TestCase):    
    '''Test LayerReader functions'''
        
    def setUp(self):
        pgds = PGDS(PGCONNSTR.format(h=P[0],d=P[1],p=P[2],u=P[3],x=P[4],s=P[5]))
        self.layerreader = LayerReader(initds(SFDS,'CropRegions.shp'),pgds)
        
    def tearDown(self):
        self.layerreader = None
        
    def test10_layerReaderInit(self):
        self.assertNotEqual(self.layerreader,None,'LayerReader not instantiated')
        
    def test10_layerReaderInit(self):
        self.assertNotEqual(self.layerreader,None,'LayerReader not instantiated')
    
    
if __name__ == "__main__":
    unittest.main()