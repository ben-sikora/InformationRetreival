
class DocumentNode: 
    def __init__(self, docnumber):
        self.doc= docnumber
        self.tf=1
        self.pos=[]
    
    def add(self):
        self.tf= self.tf+1

    def getDocNumber(self):
        return self.doc

    def updatePos(self, posNum):
        self.pos.append(posNum)
    
    def getTermFreq(self):
        return self.tf

    def getFileLine(self):
        line= str(self.doc)+", "+ str(self.tf)
        if(len(self.pos) != 0):
            line= line+ ", "
            for p in self.pos: 
                line= line+ str(p)+ " "
        return line 
                
