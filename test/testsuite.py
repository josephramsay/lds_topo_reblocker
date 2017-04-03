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
from ReblockerUI_Test import *
#import LayerReader_Test 

def suite():
    suite = unittest.TestLoader()
    suite.loadTestsFromTestCase(LayerReader_Test)
    suite.loadTestsFromTestCase(ReblockerUI_Test)
    
    return suite
    
    
if __name__ == "__main__":
    unittest.main()