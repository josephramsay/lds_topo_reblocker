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

class RUIContainer(RUI):
    
    command_list = []
    
    def __init__(self,args):
        self.p2 = args
        super(RUIContainer, self).__init__(self.watch)
        
    def watch(self):
        if self.p2.poll():
            self.process(self.p2.recv())
        self.setCallback(self.watch)

    def process(self,msg):
        print(msg)
        if msg == 'enable_disable':
            self.enable_disable()
        elif msg == 'select':
            self.select()
        else:
            print('command {} not recognised'.format(msg))
            return
        self.command_list.append(msg)
        

class ProcessWrapper(Process):
    
    p1, p2 = Pipe()
    
    def __init__(self,name='ReblockerUI_pw',proc=RUIContainer):
        super(ProcessWrapper, self).__init__(name=name, target=proc, args=(self.p2,))
        self.daemon = True
        self.start()

    def quit(self):
        self.join(timeout=1)
        
    def send(self,command):
        self.p1.send(command)
        
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
         testlog.debug('Test_0.20 ReblockerUI instantiation test')
         self.assertEqual(isinstance(self.rpw._target,type(RUI)), True,'Testlog not instantiated')
         self.assertNotEqual(self.rpw._target,RUI,'Testlog not instantiated')    
        
    def test_20_ReblockerUI_enabledisable(self):
        #assertIsNotNone added in 3.1
        testlog.debug('Test_0.20 ReblockerUI instantiation test')
        
        self.rpw.send('ERROR_COMMAND')
        time.sleep(2)
        self.rpw.send('enable_disable')
        time.sleep(2)
        self.rpw.send('select')
        
        self.assertEqual(True,True,'Testlog not instantiated')    
    
            
        
if __name__ == "__main__":
    unittest.main()
