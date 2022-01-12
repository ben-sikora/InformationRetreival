
from typing import OrderedDict


class evalTermNode: 


    def __init__(self, termID=0):
        self.idf= -1
        self.termID= termID
        self.termDict= OrderedDict()
        self.termPosition= OrderedDict()
    
    def addDocAndTF(self, docID, tf, pos=None):
        self.termDict[docID]= tf
        if pos != None:
            self.termPosition[docID]= pos
    
    def collectionTermFrequency(self):
        total=0
        for docID in self.termDict:
            total= total+ self.termDict[docID]
        return total 
        

    def getTermFrequency(self, docID):
        if docID in self.termDict:
             return self.termDict[docID]
        else:
            return 0
    
    def getDocList(self):
        return list(self.termDict.keys())

    def getDocFrequency(self):
        return len(self.termDict)