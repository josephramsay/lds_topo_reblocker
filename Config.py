################################################################################
#
# Copyright 2015 Crown copyright (c)
# Land Information New Zealand and the New Zealand Government.
# All rights reserved
#
# This program is released under the terms of the 3 clause BSD license. See the 
# LICENSE file for more information.
#
################################################################################
import os
import sys
import re
import json
from string import whitespace

PYVER3 = sys.version_info > (3,)

#2 to 3 imports
if PYVER3:
    import configparser as ConfigParser
else:
    import ConfigParser

import getpass
import base64

try:
    from Crypto.Cipher import AES
    USE_PLAINTEXT = False
except:
    USE_PLAINTEXT = True
    print('Local Password Encoding, DISABLED')
    

UNAME = os.environ['USERNAME'] if re.search('win',sys.platform) else os.environ['LOGNAME']
DEF_CONFIG = {'db':{'host':'127.0.0.1'},'user':{'name':UNAME}}
CONFIG_FILE = os.path.join(os.path.dirname(__file__),'config.ini')


if not USE_PLAINTEXT:
    K='12345678901234567890123456789012'
    PADDING = '{'
    BLOCK_SIZE = 16
    pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
    unpad = lambda s: s.decode('utf8').rstrip(PADDING)
    EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
    #DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)
    DecodeAES = lambda c, e: unpad(c.decrypt(base64.b64decode(e)))
    
class ConfigReader(object):
    '''Reader class for configparser object'''
    cp = ConfigParser.ConfigParser()
    
    def __init__(self):
        self.cp.read(CONFIG_FILE)
        self._readConfig()
        self._envConfig()
        
    def _readConfig(self):
        '''Read ConfigParser object to saved dict'''
        self.d = {}
        for sect in self.cp.sections():
            self.d[sect] = {}
            for opt in self.cp.options(sect):
                val = self._retype(self.cp.get(sect,opt))
                self.d[sect][opt] = val# or None (doesn't work if tryng to assign x=False)
                setattr(self, '{}_{}'.format(sect,opt), val) 
                            
    def _retype(self,val):
        '''Utility function that attempts to cast String values to their correct type after reading from config file
        @param val: String or string representing some numeric/boolean
        @type val: String 
        '''
        if val.startswith('{') and val.endswith('}'): val = json.loads(val)
        else: 
            val = val.replace('"','').strip("'")
            if val.isdigit(): val = int(val)
            elif val.replace('.','',1).isdigit(): val = float(val)
            elif val.lower() in ('true','false'): val = bool(val.lower()=='true')
        return val
                
    def _envConfig(self,prefix=None):
        '''Attempt to fill missing local dict values not included in config file with matching environment variables.
        - I{This if needed to pass encrypted values when it is unsafe to store them in a git repo}
        '''
        #NOTE env vars must use <prefix>_<section>_<option>=val format and are bypassed with null value
        prefix = prefix or (self.env_prefix if hasattr(self,'env_prefix') else 'env')
        for sect in self.d:
            for k,val in self.d[sect].items():
                #check to see if config items are blank, if they are search in env vars
                if val is None or (isinstance(val,str) and ( val.strip() == '' or val == 'None' or all(i in whitespace for i in val) )):
                    envvar = '{}_{}_{}'.format(prefix,sect,k)
                    eval = os.environ.get(envvar)
                    self.d[sect][k] = eval or DEF_CONFIG.get(sect,{}).get(k)
                    
    def _promptUser(self):
        '''I{unused}. If config cannot be populated with ini file and envvars prompt the user for missing values or report failure'''
        p = getpass.getpass()
                    
    def configSectionMap(self,section=None):
        '''Per section config matcher, used in constant reader class'''
        return self.d[section] if section else self.d
    
    #and now some security theatre for your amusement
    
    @staticmethod
    def _detect(p,cti):
        '''detects whether p has been ciphered or not, add conditions as required'''
        return bool(re.match('^{cti}.*$'.format(cti=cti),p))

    
    @staticmethod
    def readp():
        #CT_IND is a const set in config.ini
        from Const import CT_IND
        cp = ConfigParser.ConfigParser()
        cp.read(CONFIG_FILE)
        sometext = cp.get('user','pass')
        if USE_PLAINTEXT:
            return sometext
        else:    
            if ConfigReader._detect(sometext,CT_IND):
                user = getpass.getuser()
                aes = AES.new(K, AES.MODE_CBC,pad(user))
                return DecodeAES(aes,sometext.strip(CT_IND))
            else:
                ConfigReader._writep(sometext)
                return sometext

    @staticmethod  
    def _writep(plaintext):
        from Const import CT_IND
        cp = ConfigParser.ConfigParser()
        cp.read(CONFIG_FILE)
        user = getpass.getuser()
        aes = AES.new(K, AES.MODE_CBC,pad(user))
        ciphertext = '{}{}'.format(CT_IND,EncodeAES(aes,plaintext))
        cp.set('user','pass',ciphertext)
        cp.write(open(CONFIG_FILE,'w'))
        

            
def test():
    #ConfigReader.writep('secretpassword')
    p = ConfigReader.readp()
    print (p)
    
    p = ConfigReader.readp()
    print (p)
    
    ConfigReader._writep(p)
    
    
    
if __name__ == '__main__':
    test() 

        