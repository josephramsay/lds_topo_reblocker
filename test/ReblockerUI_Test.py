# coding=utf-8
'''
v.0.0.1

lds_topo_reblocker - ReblockerUI_Test

Copyright 2011 Crown copyright (c)
Land Information New Zealand and the New Zealand Government.
All rights reserved

This program is released under the terms of the new BSD license. See the 
LICENSE file for more information.

Tests on ReblockerUI class

Created on 30/01/2017

@author: jramsay
'''

import unittest
import inspect
import sys
import re
import os
import time
import yaml
from multiprocessing import Process, Pipe

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'../src')))

from Logger import Logger
from LayerReader import LayerReader, initds, SFDS, PGDS
from ReblockerUI import RUI
from LayerReader_Test import config

testlog = Logger.setup('test')

class UnrecognisedRUICommandException(Exception):pass
class RUIContainer(RUI):
    '''Override client side ReblockedUI'''
    
    def __init__(self,args):
        self.p2 = args
        super(RUIContainer, self).__init__(self.watch)
        
    def watch(self):
        if self.p2.poll():
            self.p2.send(self.process(self.p2.recv()))
        self.setCallback(self.watch)

    def process(self,attr):
        '''Check the requested method exists and call it with no args'''
        if attr in [i for i,_ in inspect.getmembers(self, predicate=inspect.ismethod)]:
            return getattr(self,attr)()
        else:
            raise UnrecognisedRUICommandException('Unknown command {}'.format(attr))

        
class ReceiveResponseException(Exception):pass
class ProcessWrapper(Process):
    timeout = 2
    retries = 1
    p1, p2 = Pipe()
    
    def __init__(self,name='ReblockerUI_pw',proc=RUIContainer):
        super(ProcessWrapper, self).__init__(name=name, target=proc, args=(self.p2,))
        self.daemon = True
        self.start()

    def quit(self):
        self.join(timeout=self.timeout)
        
    def send(self,command):
        self.p1.send(command)
        
    def recv(self,tc=None,rc=None):
        '''Receive a result from the pipe, wait tc (s) and retry rc times'''
        r = 0
        if rc == None: rc = self.retries
        tc = tc or self.timeout
        while r<=rc:
            if self.p1.poll(tc):#timeout=tc):#timeout keyword doesnt work on py2.7
                return self.p1.recv()
            r += 1
        #Bypass exception by setting 0 retries in case where timeout expected e.g. unclicked dialog
        if rc != 0: raise ReceiveResponseException('No response received after {}s with {} retries'.format(tc,rc))

    def __enter__(self):
        return self
    
    def __exit__(self, type, value, traceback):
        self.quit()

class Test_00_ReblockerUI_SelfTest(unittest.TestCase):
    
    def setUp(self):
        pass
        
    def tearDown(self):
        pass
    
    def test10_selfTest(self):
        #assertIsNotNone added in 3.1
        self.assertNotEqual(testlog,None,'Testlog not instantiated')
        testlog.debug('ReblockerUI_Test Log')
    
    def test20_layerReader_Init(self):
        #assertIsNotNone added in 3.1
        testlog.debug('Test_0.20 ReblockerUI instantiation test')
        p = Process(name='ReblockerUI_1',target=RUI)
        p.daemon = True
        p.start()
        self.assertNotEqual(p,None,'ReblockerUI not instantiated')
        p.join(timeout=1)
        p.terminate()
        
class Test_10_ReblockerUI_StaticTest(unittest.TestCase):
    
    def setUp(self):
        self.rpw = ProcessWrapper()
        
    def tearDown(self):
        self.rpw.quit()
    
    def test_10_ReblockerUI_RPW(self):
         #assertIsNotNone added in 3.1
         testlog.debug('Test 10.10 ReblockerUI RPW test')
         self.assertEqual(isinstance(self.rpw._target,type(RUI)), True,'Processwrapper _target != ReblockerUI type')
         self.assertNotEqual(self.rpw._target,RUI,'Processwrapper _target = new ReblockerUI')    
        
    def test_20_ReblockerUI_static(self):
        #assertIsNotNone added in 3.1
        L = (('enable_disable',2,1,True),('select',5,0,None))
        testlog.debug('Test 10.20 ReblockerUI Static control test')

        for cmd,t,r,req in L:
            self.rpw.send(cmd)
            res = self.rpw.recv(tc=t,rc=r)
            self.assertEqual(res,req,'Command {}()={} failed with {}'.format(cmd,req,res))
        
#     def test_30_ReblockerUI_dynamic(self):
#         '''Cannot fully test this as it requires a live instance of the LINZ data service'''
#         L = (('remove',2,2,True),('release',2,2,True),('upload',2,2,True),('reblock',2,2,None))
#         
#         testlog.debug('Test 10.30 ReblockerUI Dynamic control test')
#         
#         for cmd,t,r,req in L:
#             self.rpw.send(cmd)
#             self.assertEqual(self.rpw.recv(tc=t,rc=r),req,'Testlog not instantiated')


if __name__ == "__main__":
    unittest.main()
