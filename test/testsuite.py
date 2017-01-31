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

from LayerReader_Test import *
#import LayerReader_Test 

def suite():
    suite = unittest.TestSuite()
    suite.addTest(Test_0_LayerReaderSelfTest())
    suite.addTest(Test_1_LayerReaderConfigTest())
    #suite.addTest(LayerReader_Test("Test_0_LayerReaderSelfTest"))
    #suite.addTest(LayerReader_Test("Test_1_LayerReaderConfigTest"))
    return suite


# TL1 = ('Test_0_LayerReaderSelfTest','Test_1_LayerReaderConfigTest')
# class LayerReaderTestSuite(unittest.TestSuite):
#     def __init__(self):
#         unittest.TestSuite.__init__(self,map(LayerReader_Test,TL1))
    
    
if __name__ == "__main__":
    unittest.main()