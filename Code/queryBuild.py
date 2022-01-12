import re
from typing import OrderedDict
import queryNode
import lexicon
import documentNode

class QueryBuilder:
    def __init__(self):
        self.queryNodeList= []
        self.lex= lexicon.Lexicon()
        self.lex.phraseFreqMinTwo= 0
        self.lex.phraseFreqMinThree= 0
        self.lex.manualSwitch("single")

    def setIndex(self, type):
        self.lex.manualSwitch(type)

    def printList(self):

        for q in self.queryNodeList:
            print("Tag: ", q.tag)
            print("Query: ", q.orginalQ)
            for key in q.procQ: 
                print("ProcessedQueryTerm: ", key)
                doc= q.procQ[key]
                print("ProcessedQueryTermFrequncy: ", doc.getTermFreq())
                print("ProcessedQueryTermPositions: ", doc.pos)
            print()
    
    def getQueryList(self):
        return self.queryNodeList
    
    def searchIndex(self, fileName= "queryfile.txt"):
        self.__tagParser(fileName)
    
    def searchNarrativeIndex(self, fileName= "queryfile.txt"):
        self.__tagParserReduction(fileName)

    def __tagParserReduction(self, fileName):
        startDocTag= re.compile(r'<top>', flags= re.IGNORECASE)
        numDocTag= re.compile(r'(<num> Number: )(.*)', flags= re.IGNORECASE)
        titleDocTag= re.compile(r'(<narr>)(.*)', flags= re.IGNORECASE)
        endDocTag= re.compile(r'(</top>)(.*)', flags= re.IGNORECASE)
        backSlashT= re.compile(r'\t', flags= re.IGNORECASE)
        backSlashN= re.compile(r'\n', flags= re.IGNORECASE)
        qbuild= None
        flag= False
        
        with open(fileName, "rt") as doc:
            line= doc.readline()
            while line:
            #for x in range(10): 
                if startDocTag.search(line):
                    if qbuild != None:
                        self.queryNodeList.append(qbuild)
                    qbuild= queryNode.QueryNode()
                elif numDocTag.search(line):
                    match= numDocTag.search(line)
                    qbuild.addTag(int(match.group(2)))
                elif titleDocTag.search(line):
                    flag= True
                elif(flag and not endDocTag.search(line)):
                    if backSlashT.search(line) or backSlashN.search(line):
                        line=re.sub(r'\t', "", line)
                        line=re.sub(r'\n', "", line)
                    if(line==""):
                        line= doc.readline()
                        continue 
                    qbuild.addQ(line)
                    ##Processing of line
                    self.lex.indexer(line)
                elif endDocTag.search(line):
                    flag=False
                    dict= self.lex.getDict()
                    newDict= OrderedDict()
                    for key in dict:
                        newDict[key]= dict[key][-1]
                    qbuild.addProcQ(newDict)
                    self.lex.clear()

                line= doc.readline()
        self.queryNodeList.append(qbuild)

    def __tagParser(self, fileName):
        startDocTag= re.compile(r'<top>', flags= re.IGNORECASE)
        numDocTag= re.compile(r'(<num> Number: )(.*)', flags= re.IGNORECASE)
        titleDocTag= re.compile(r'(<title> Topic: )(.*)', flags= re.IGNORECASE)
        backSlashT= re.compile(r'\t', flags= re.IGNORECASE)
        backSlashN= re.compile(r'\n', flags= re.IGNORECASE)
        qbuild= None
        
        with open(fileName, "rt") as doc:
            line= doc.readline()
            while line:
            #for x in range(10): 
                if startDocTag.search(line):
                    if qbuild != None:
                        self.queryNodeList.append(qbuild)
                    qbuild= queryNode.QueryNode()
                elif numDocTag.search(line):
                    match= numDocTag.search(line)
                    qbuild.addTag(int(match.group(2)))
                elif titleDocTag.search(line):
                    match= titleDocTag.search(line)
                    line=match.group(2)
                    if backSlashT.search(line) or backSlashN.search(line):
                        line=re.sub(r'\t', "", line)
                        line=re.sub(r'\n', "", line)
                    qbuild.addQ(line)
                    ##Processing of line
                    self.lex.indexer(line)
                    
                    dict= self.lex.getDict()
                    newDict= OrderedDict()
                    for key in dict:
                        newDict[key]= dict[key][-1]
                    qbuild.addProcQ(newDict)
                    self.lex.clear()

                line= doc.readline()
        self.queryNodeList.append(qbuild)
    
