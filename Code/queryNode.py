
from typing import OrderedDict
import documentNode

class QueryNode: 


    def __init__(self):
        self.tag= -1
        self.orginalQ= []
        self.procQ= None
        self.totalWeightCosine= -1 
        self.querySumSqrdCosine= -1
    
    def addTag(self, tag):
        self.tag= tag
    

    def addProcQ(self, q):
        self.procQ=q
    
    def addProcQExpan(self, q):
        if(q in self.procQ):
            self.procQ[q].tf= self.procQ[q].tf+0.05
        else:
            self.procQ[q]= documentNode.DocumentNode(-1)
            self.procQ[q].tf= 0.05
    
    def addQ(self, q):
        self.orginalQ.append(q)
    
    def getQTF(self, q):
        tf= 0
        for qPart in self.procQ:
            if qPart==q:
                continue


    

