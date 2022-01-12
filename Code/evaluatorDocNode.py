
from typing import OrderedDict


class evalDocNode: 


    def __init__(self, docID=0):
        self.docLength=0
        self.docID= docID
        self.cosineWeight= -1
        self.docDict= OrderedDict()
    
    def addTermAndTF(self, termID, tf):
        self.docDict[termID]= tf
        self.docLength= self.docLength+ tf


    def getTermFrequency(self, term):
        if term in self.docDict:
            return self.docDict[term]
        else:
            return 0

    def getDocLength(self):
        return self.docLength

    def getTerms(self):
        return list(self.docDict.keys)