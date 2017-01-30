'''
Created on 6/03/2015

@author: jramsay
'''

import re

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver, FileSender
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor


from LayerReader import LayerReader, initds, SFDS, PGDS


class ReblockFileHandler(FileSender):
    def __init__(self):
        #self.layer = layer
        pass

    def connectionMade(self):
        self.sendLine("connect")
    
    def lineReceived(self, line):
        self.sendLine("Uploading file '{}'}".format(line))
        
    def dataReceived(self, line):
        self.sendLine("Uploading file '{}'}".format(line))
    
class ReblockReceiver(LineReceiver):

    layer = 1756
    
    def __init__(self):
        #self.layer = layer
        pass

    def connectionMade(self):
        self.sendLine("Connected to Topo-Reblocker")

    def connectionLost(self, reason):
        self.sendLine("Disconnected from Topo-Reblocker")

    def lineReceived(self, line):
        if re.match('^R.' ,line):
            '''process selected files'''
            self.sendLine("Reblocking {}".format(line))
            #self.reblock(line)
        elif re.match('^U.' ,line):
            '''upload shapefile'''
            self.sendLine("Uploading {}".format(line))
            #self.loadSHP(line)
        elif re.match('^D.' ,line):
            '''download result'''
            self.sendLine("Downloading {}".format(line))
        else:
            self.sendLine("Does not compute. {}".format(line))
            
        
    def loadSHP(self,spath):
        lr = LayerReader(initds(SFDS,spath),initds(PGDS))
        inlayers = [k[1] for k in lr.transfer(self.layer)]
        
    def reblock(self,spath):
        lr = LayerReader(initds(SFDS,spath),initds(PGDS))
        inlayers = [k[1] for k in lr.transfer(self.layer)]
        
    def doDefault(self,x):
        self.sendLine(x)


class ReblockFactory(Factory):

    protocol = ReblockReceiver
    
    def __init__(self):
        pass
    
class ReceiverFactory(Factory):

    protocol = ReblockFileHandler
    
    def __init__(self):
        pass
      
      

def main():
    endpoint = TCP4ServerEndpoint(reactor, 8777)
    endpoint.listen(ReblockFactory())
    #reactor.run() #@UndefinedVariable    
    
    receiver = TCP4ServerEndpoint(reactor, 8778)
    receiver.listen(ReceiverFactory())
    reactor.run() #@UndefinedVariable
    
if __name__ == '__main__':
    main()
