from typing import List, OrderedDict
from queryBuild import QueryBuilder
import queryBuild
import math
import os
import queryNode
import documentNode
import argparse
import subprocess
import evaluatorDocNode
import evaluatorTermNode
from enum import Enum
import time

class index(Enum):
    THREEPHRASE= 1
    TWOPHRASE= 2
    SINGLEPOS=3
    STEM= 4
    SINGLE= 5

class Evaluator:
    def __init__(self):
        self.termLookupDict= OrderedDict()
        self.termDict=OrderedDict()
        self.docDict=OrderedDict()
        self.build= queryBuild.QueryBuilder()
        self.queryNodeList= []
        #self.totalWeightBMQ= -1
        self.queryScores=[]
        self.queryScoreType= []
        self.docLookupDict= OrderedDict()
        self.termNumberLookUpDict= OrderedDict()
        self.totalLength= 0

        #Constants in BM5
        self.b= 0.75
        self.k1= 1.2
        self.k2= 500

        #Output Folder 
        self.outputFolder= "Results"

        '''
        Difference between terms. Note this number is 1 higher 
        than mentioned in the design document because this is 
        accounting for positions. I.E if this value was 1 there would be no words allowed between query Terms. 
        '''
        self.dif= 4

        #Cutoff for phrases
        self.phraseCuttoff=3

        #Number of Terms Retrieved Per Document 
        self.termRetrv= 5

        ##Number of Docs Retreived For Expansion
        self.docRetrv= 5

        ##Percent of terms in Expansion
        self.reduce= 0.6

        ##Docs Retrieved Per Query. Added for project 3
        self.docsPerQuery= 99


    def readLexicon(self, lexiconFile):
        lexicon= open(lexiconFile, "r")
        #Ignore Line
        line= lexicon.readline()
        for line in lexicon:
            words= line.split()
            term= words[0].replace(",", "")
            termID= int(words[1])
            self.termLookupDict[term]= termID
            self.termNumberLookUpDict[termID]= term
    
    
    def readDocCSV(self, output, typeI):
        filename= output+"/"+ typeI+ "/docs.csv"
        f= open(filename, "r")
        #Ignore Line
        line= f.readline()
        for line in f:
            words= line.split()
            docID= int(words[0].replace(",", ""))
            doc= words[1]
            self.docLookupDict[docID]= doc
    
    def readQueryList(self, type, fileName):
        self.build.setIndex(type)
        self.build.searchIndex(fileName)
        self.queryNodeList= self.build.getQueryList()
    
    def readNarrativeQueryList(self, type, fileName):
        self.build.setIndex(type)
        self.build.searchNarrativeIndex(fileName)
        self.queryNodeList= self.build.getQueryList()

    #This is the function that builds all of my evaluation nodes. 
    def readPostingList(self, postFile):
        pl= open(postFile, "r")
        #Ignore Line
        line= pl.readline()

        for line in pl:
            words= line.split()
            termID= int(words[0].replace(",", ""))
            docID= int(words[1].replace(",", ""))
            termFQ= int(words[2].replace(",", ""))
            self.totalLength= self.totalLength+ termFQ
            postArray=[]
            if len(words)>3:
                for x in range (3, len(words)):
                    postArray.append(int(words[x]))

            ##Adding TermNode
            if termID in self.termDict:
                termNode=self.termDict[termID]
                if len(postArray) == 0:
                    termNode.addDocAndTF(docID, termFQ)
                else:
                    termNode.addDocAndTF(docID, termFQ, postArray)
            else:
                termNode= evaluatorTermNode.evalTermNode(termID)
                if len(postArray) == 0:
                    termNode.addDocAndTF(docID, termFQ)
                else:
                    termNode.addDocAndTF(docID, termFQ, postArray)
                self.termDict[termID]= termNode

            ##Adding DocNode
            if docID in self.docDict:
                docNode=self.docDict[docID]
                docNode.addTermAndTF(termID, termFQ)
            else:
                docNode= evaluatorDocNode.evalDocNode(termID)
                docNode.addTermAndTF(termID, termFQ)
                self.docDict[docID]= docNode
    
    ##Clearing All Dictionaries. Used in dynamic searching. 
    def clear(self):
        self.termLookupDict.clear()
        self.docLookupDict.clear()
        self.termDict.clear()
        self.queryNodeList.clear()
        self.docDict.clear()

    
    #Phrase searching and calculculating 
    def phraseBM(self, typeI, querysLeft= []):
        #Calculating  
        x= 0
        newQuerysLeft=[]
        for query in self.queryNodeList:
            if len(querysLeft)!=0 and x not in querysLeft:
                continue
            maxdf= -1
            for queryTerm in query.procQ:
                if queryTerm in self.termLookupDict:
                    qID= self.termLookupDict[queryTerm]
                    if qID in self.termDict:
                        temp= self.termDict[qID].getDocFrequency()
                    else:
                        temp=0
                    if temp> maxdf:
                        maxdf= temp
        
            #If Max Frequenecy Above Cutoff otherwise add to be scored later
            if maxdf >= self.phraseCuttoff:
                docScores= self.calculatingBMScoreQuery(query)
                self.queryScores[x]= docScores
                self.queryScoreType[x]= typeI
            else:
                newQuerysLeft.append(x)

            ##Append Counter
            x=x+1
        return newQuerysLeft
    
    ##Reading all the files after being given the folder of project 1 output,
    #The location of the queryfile and the index type. 
    def readAllFiles(self, outputfolder, queryfile, typeIndex, narrative=False):

        lexicon= outputfolder+"/"+ typeIndex +"/lexicon.csv"
        postingList= outputfolder+"/"+ typeIndex +"/invertedIndex.csv"
        self.readLexicon(lexicon)
        if(not narrative):
            self.readQueryList(typeIndex, queryfile)
        elif(narrative):
            self.readNarrativeQueryList(typeIndex, queryfile)
        self.readPostingList(postingList)
        self.readDocCSV(outputfolder, typeIndex)
    
    

    def __arparser(self, parser):
        parser= argparse.ArgumentParser(prog= 'query')
        parser.add_argument('-single', dest='single', action= 'store_true')
        parser.add_argument('-stem', dest= 'stem', action= 'store_true')
        parser.add_argument('-cosine', dest= 'cosine', action= 'store_true')
        parser.add_argument('-bm25', dest= 'bm25', action= 'store_true')
        parser.add_argument('-lm', dest= 'lm', action= 'store_true')
        parser.add_argument('-t', dest= 'trec', action= 'store_true')
        parser.add_argument('-index', dest= 'indexPath', nargs=1, type=str,required=True)
        parser.add_argument('-query', dest= 'queryPath', nargs=1, type=str,required=True)
        parser.add_argument('-o', dest= 'output', nargs=1, type=str)
        parser.add_argument('-phraseThreshold', dest= 'phraseThreshold', action= 'store_true')
        parser.add_argument('-queryR', dest= 'queryRed', action= 'store_true')
        parser.add_argument('-queryE', dest= 'queryExpan', action= 'store_true')
        parser.add_argument('-queryRE', dest= 'queryExpanAndRed', action= 'store_true')
        parser.add_argument('-terms', dest= 'termsAdded', nargs=1, type= int)
        parser.add_argument('-docs', dest= 'docsAdded', nargs=1, type= int)
        parser.add_argument('-threshold', dest= 'threshold', nargs=1, type= float)


        args= parser.parse_args()
        return args
    

    def __runtreveval(self): 
            filename= self.outputFolder+"/results.txt"
            results= subprocess.run(["./trec_eval", "qrel.txt", filename],capture_output= True, text=True)
            print(results.stdout)
    
    def __calculateScores(self, args):
        ##Calculating Scores
        if(args.cosine):
            self.calculatingAllCosineScores()
            typeI= "cosine"
        elif(args.bm25):
            self.calculatingAllBMScores()
            typeI= "bm25"
        elif(args.lm):
            self.calculatingAllDSScores()
            typeI= "dirchlet smoothing"
        else:
            raise Exception("No Retreival Method Given")
        return typeI
    
    def settingParm(self, args):
        if(args.termsAdded != None):
            self.termRetrv= args.termsAdded[0]
        if(args.docsAdded != None):
            self.docRetrv= args.docsAdded[0]
        if(args.threshold != None):
            self.reduce= args.threshold[0]

    def queryRedAndExpan(self, args):
        ##Reading Files
        if(args.stem):
            self.readAllFiles(args.indexPath[0], args.queryPath[0], "stem",narrative=True)
        else:
            self.readAllFiles(args.indexPath[0], args.queryPath[0], "single",narrative=True)

        ##Set parameters
        self.settingParm(args)
        
        ##Make expanded query 
        self.makeReducedQuery()
        
        ##Calculating Scores
        typeI=self.__calculateScores(args)

        ##Expanded Query
        self.makeExpansionQuery()

        ##Clearing that needs to happen
        self.queryScores.clear()

        ##Calculating Scores Again
        typeI=self.__calculateScores(args)

        ##Print Results
        self.makeResults(type= typeI)

    def queryReduction(self, args):
        #Output Folder
        if (args.output != None):
            self.outputFolder= args.output[0]

        ##Reading Files
        if(args.stem):
            self.readAllFiles(args.indexPath[0], args.queryPath[0], "stem",narrative=True)
        else:
            self.readAllFiles(args.indexPath[0], args.queryPath[0], "single",narrative=True)
        
        ##Set parameters
        self.settingParm(args)


        ##Make expanded query 
        self.makeReducedQuery()

        ##Testing
        #self.printList()
        
        ##Calculating Scores
        typeI=self.__calculateScores(args)

        ##Print Results
        self.makeResults(type= typeI)

    ##Query Expansion 
    def queryExpansion(self, args):
        ##Reading Files
        if(args.single):
            self.readAllFiles(args.indexPath[0], args.queryPath[0], "single")
        else: 
            raise Exception("Valid Indexer Not Given")
        
        ##Set parameters
        self.settingParm(args)


        ##Calculating Scores
        typeI= self.__calculateScores(args)
        
        ##Make expanded query 
        self.makeExpansionQuery()
        #self.printList()

        ##Clearing that needs to happen
        self.queryScores.clear()

        ##Run Results Again w/Expanded query
        typeI= self.__calculateScores(args)

        ##Print Results
        self.makeResults(type= typeI)
    
    
    def queryModification(self):
        timeStart= time.perf_counter()
        parser= argparse.ArgumentParser(prog= 'query')
        args= self.__arparser(parser)
        #Output Folder
        if (args.output != None):
            self.outputFolder= args.output[0]

        if(args.queryExpan):
            self.queryExpansion(args)
        elif(args.queryRed):
            self.queryReduction(args)
        else: 
            self.queryRedAndExpan(args)
        
        ##Printing Time Data
        timeEnd= time.perf_counter()
        print("Query Processign Time: ", str(timeEnd-timeStart))

        ##Run trec eval 
        if(args.trec):
            self.__runtreveval()


    def makeReducedQuery(self):
        newQueryList= []
        totalDocs= len(self.docDict)
        for x in range(0, len(self.queryNodeList)):
            oldNode= self.queryNodeList[x]
            idfScores= OrderedDict()
            for term in oldNode.procQ: 
                if term in self.termLookupDict:
                    termID= self.termLookupDict[term]
                    df= len(self.termDict[termID].termDict)
                    idf= math.log((totalDocs/df), 10)
                    idfScores[term]= idf
                else:
                    idfScores[term]= -10000000
            
            #Ranking queryterms
            idfScores= sorted(idfScores.items(), key= lambda x: x[1], reverse= True)

            ##Adding new terms to query 
            newQueryNode= queryNode.QueryNode()
            newQueryNode.tag= oldNode.tag
            newprocQ= OrderedDict()
            count=1
            maxTerms= math.floor(self.reduce*len(idfScores))
            for i in idfScores:
                newprocQ[i[0]]= documentNode.DocumentNode(-1)
                newprocQ[i[0]].tf= oldNode.procQ[i[0]].tf
                if count== maxTerms:
                    break
                count= count+1
            newQueryNode.procQ= newprocQ
            newQueryList.append(newQueryNode)
        #Final Transfer 
        self.queryNodeList= newQueryList
            


    def makeExpansionQuery(self):
        newQueryList= []
        for x in range(0, len(self.queryNodeList)):
            oldNode= self.queryNodeList[x]
            scores= self.queryScores[x]
            ##In the case query had no docs
            if scores== None: 
                newQueryNode= queryNode.QueryNode()
                newQueryNode.tag= oldNode.tag
                newQueryNode.procQ= oldNode.procQ
                newQueryList.append(newQueryNode)
                continue 
            scores= sorted(scores.items(), key= lambda x: x[1], reverse= True)

            #Building Top Doc List 
            topDocs=[]
            count=0
            for i in scores:
                topDocs.append(i[0])
                if count==self.docRetrv-1:
                    break
                count= count+1
            
            #Making new queryNode
            newQueryNode= queryNode.QueryNode()
            newQueryNode.tag= oldNode.tag
            newQueryNode.procQ= oldNode.procQ
            for doc in topDocs:
                topTermList= self.topTermsInDoc(doc, topDocs)
                for term in topTermList:
                    #Converet term back to word. Need to make new dictionnary from reading lexicon 
                    termWord= self.termNumberLookUpDict[term]
                    newQueryNode.addProcQExpan(termWord)
            newQueryList.append(newQueryNode)
        
        ##Final Edits
        self.queryNodeList.clear()
        self.queryNodeList= newQueryList

            
    
    def topTermsInDoc(self, doc, topDocs):
        evalDocNode= self.docDict[doc]
        docDict= evalDocNode.docDict
        termScores= OrderedDict()
        totalDocs= len(self.docDict)

        ##Building Scores For Doc
        minTerm= -1
        for term in docDict:
            if minTerm==-1:
                minTerm= term

            ##Calculating this terms score
            #df= docDict[term]
            df= len(self.termDict[term].termDict)
            idf= math.log((totalDocs/df), 10)
            n= self.termInDocs(term, topDocs)
            score= n*idf
            
            ##Handling Top Terms 
            if len(termScores) < self.termRetrv:
                termScores[term]=score
                if score<termScores[minTerm]:
                    minTerm= term
            elif(score> termScores[minTerm]):
                del termScores[minTerm]
                termScores[term]= score
                #New Min
                minTerm= None
                for term in termScores:
                    if minTerm== None:
                        minTerm= term
                        continue
                    if termScores[minTerm]>termScores[term]:
                        minTerm= term
        return termScores
        

    def termInDocs(self, term, topDocs):
        count= 0
        for doc in topDocs:
            tf= self.docDict[doc].getTermFrequency(term)
            if tf==0:
                continue
            else:
                count= count+1
        return count 




    #The main method of the static searching 
    def staticSearching(self):
        timeStart= time.perf_counter()
        parser= argparse.ArgumentParser(prog= 'query')
        args= self.__arparser(parser)
        typeI=""
        #Output Folder
        if (args.output != None):
            self.outputFolder= args.output[0]

        ##Reading Files
        if(args.stem):
            self.readAllFiles(args.indexPath[0], args.queryPath[0], "stem")
        else:
            self.readAllFiles(args.indexPath[0], args.queryPath[0], "single")
        
        ##Calculating Scores
        typeI= self.__calculateScores(args)
            

        ##Print Results
        self.makeResults(type= typeI)

        ##Printing Time Data
        timeEnd= time.perf_counter()
        print("Query Processign Time: ", str(timeEnd-timeStart))


        ##Run trec eval 
        if(args.trec):
            self.__runtreveval()
    
    #The main method of the dynamic searching 
    def dynamicSearching(self):
        timeStart= time.perf_counter()
        parser= argparse.ArgumentParser(prog= 'query_dynamic')
        args= self.__arparser(parser)
        if(args.phraseThreshold):
            self.phraseCuttoff= 1

        #Output Folder
        if (args.output != None):
            self.outputFolder= args.output[0]

        ##Other Folders. This output folder is the output of project 1. 
        outputfolder= args.indexPath[0]
        queryfile= args.queryPath[0]

        ##Three Phrase
        self.readAllFiles(outputfolder, queryfile, "threePhrase")

        ##Setting up Score Listing and Scoring Type
        self.queryScores= [None]*len(self.queryNodeList)
        self.queryScoreType= [None]*len(self.queryNodeList)
        ##Running Three Phrase
        querysLeft= self.phraseBM(index.THREEPHRASE)

        #Clearing dictionaries
        self.clear()

        ##Two Phrase
        self.readAllFiles(outputfolder, queryfile, "twoPhrase")

        ##Running Two Phrase
        querysLeft= self.phraseBM(index.TWOPHRASE,querysLeft)

        #Clearing Dictionaries
        self.clear()

        #Single Postional Reading 
        self.readAllFiles(outputfolder, queryfile, "singlePos")

        ##Running Single Positional 
        querysLeft=self.runAllPositional(querysLeft)

        #Clearing Dictionaries
        self.clear()

        #Single Postional Reading
        self.readAllFiles(outputfolder, queryfile, "single")

        ##Running Single Positional 
        queryScoresSingle= self.calculatingRemainingBMScores()
        self.makeResultsDynamic(queryScoresSingle)

        ##Printing Time Data
        timeEnd= time.perf_counter()
        print("Query Processign Time: ", str(timeEnd-timeStart))

        ##Run trec eval 
        if(args.trec):
            self.__runtreveval()

                

    def calculatingAllCosineScores(self):
        #Going Through Each Query 
        for query in self.queryNodeList: 
            scores= self.calculatingCosineScoreQuery(query)
            self.queryScores.append(scores)


    def calculatingAllBMScores(self):
        #Going Through Each Query 
        for query in self.queryNodeList: 
            scores= self.calculatingBMScoreQuery(query)
            self.queryScores.append(scores)
    
    ##For Dynamic Searching. Need to store scores in a different query. 
    def calculatingRemainingBMScores(self):
        #Going Through Each Query 
        queryScoresSingle= []
        for query in self.queryNodeList:
            scores= self.calculatingBMScoreQuery(query)
            queryScoresSingle.append(scores)
        return queryScoresSingle
    
    def calculatingAllDSScores(self):
        #Going Through Each Query 
        for query in self.queryNodeList: 
            scores= self.calculatingDSScoreQuery(query)
            self.queryScores.append(scores)
        
    

    def makeResultsDynamic(self, queryScoresSingle): 
        if(not os.path.exists(self.outputFolder)):
            os.makedirs(self.outputFolder)
        filename= self.outputFolder+ "/results.txt"
        if(os.path.exists(filename)):
            os.remove(filename)
        f= open(filename, "x")

        
        for x in range(0, len(self.queryNodeList)):
            queryNode= self.queryNodeList[x]
            scores= self.queryScores[x]
            rank=1
            count=1
            type=self.queryScoreType[x]
            if(type==index.TWOPHRASE):
                type= "twoPhrase"
            elif(type==index.THREEPHRASE):
                type= "threePhrase"
            elif(type==index.SINGLEPOS):
                type= "proximity"

            docsAdded= OrderedDict()
            ##Rank Three-Phrase, Two-Phrase, SinglePositional
            if scores != None and len(scores)!=0:
                #Sorting scores
                scores= sorted(scores.items(), key= lambda x: x[1], reverse= True)
                for i in scores: 
                    f.write(str(queryNode.tag))
                    f.write(" ")
                    f.write(str(0))
                    f.write(" ")
                    f.write(self.docLookupDict[i[0]])
                    f.write(" ")
                    f.write(str(rank))
                    f.write(" ")
                    f.write(str(i[1]))
                    f.write(" ")
                    f.write(str(type))
                    f.write("\n")
                    rank= rank +1

                    #Docs Added
                    docsAdded[i[0]]=1 
                    if(count>99):
                        break
                    count= count+1

            ##Now running for Single Processing
            scores= queryScoresSingle[x]
            scores= sorted(scores.items(), key= lambda x: x[1], reverse= True)
            for i in scores: 
                if i[0] in docsAdded:
                    continue
                f.write(str(queryNode.tag))
                f.write(" ")
                f.write(str(0))
                f.write(" ")
                f.write(self.docLookupDict[i[0]])
                f.write(" ")
                f.write(str(rank))
                f.write(" ")
                f.write(str(i[1]))
                f.write(" ")
                f.write("Single")                   
                f.write("\n")
                rank= rank +1
                if(count>99):
                    break
                count= count+1
        f.close()
    
    def makeResults(self, test= False, type= "!tag"): 

        if(not os.path.exists(self.outputFolder)):
            os.makedirs(self.outputFolder)
        filename= self.outputFolder+ "/results.txt"
        if(os.path.exists(filename)):
            os.remove(filename)
        f= open(filename, "x")

        
        for x in range(0, len(self.queryNodeList)):
            queryNode= self.queryNodeList[x]
            scores= self.queryScores[x]
            ##In the case query had no docs
            if scores== None: 
                continue 
            scores= sorted(scores.items(), key= lambda x: x[1], reverse= True)
            rank=1
            count=1
            for i in scores: 
                f.write(str(queryNode.tag))
                f.write(" ")
                f.write(str(0))
                f.write(" ")
                if test: 
                    f.write(str(i[0]))
                else:
                    f.write(self.docLookupDict[i[0]])
                f.write(" ")
                f.write(str(rank))
                f.write(" ")
                f.write(str(i[1]))
                f.write(" ")
                f.write(str(type))
                f.write("\n")
                rank= rank +1
                if(count>self.docsPerQuery):
                    break
                count= count+1
            
        f.close()

    ##Calculating Dirchleet Smoothing scores. Need to go through every doc.
    def calculatingDSScoreQuery(self, query):
        #Documents with Scores 
        docScores=OrderedDict()
        for doc in self.docDict:
                        #docScore=0
            docScore= self.calculatingDSScoreDoc(query, doc)
            docScores[doc]= docScore 
        return docScores

    def calculatingBMScoreQuery(self, query):
        #Documents with Scores 
        docScores=OrderedDict()
        for queryTerm in query.procQ:
            if queryTerm in self.termLookupDict:
                qID= self.termLookupDict[queryTerm]

                ##Largely for my phrase calculation 
                if qID not in self.termDict:
                    continue
                termEvalNode= self.termDict[qID]

                for doc in termEvalNode.termDict:
                    if doc in docScores:
                        continue
                    else:
                        #docScore=0
                        docScore= self.calculatingBMScoreDoc(query, doc)
                        docScores[doc]= docScore 
            else:
                continue 
        
        return docScores

    
    def calculatingBMScoreDoc(self, query, doc):
        totalScore= 0 
        for queryTerm in query.procQ:
            temp=0
            if queryTerm in self.termLookupDict:
                termID= self.termLookupDict[queryTerm]

                ##Largerly for Phrases
                if termID not in self.termDict:
                    continue
                tf= self.termDict[termID].getTermFrequency(doc)
                if tf==0:
                    temp=0
                else:
                    qtf= query.procQ[queryTerm].getTermFreq()
                    docLength= self.docDict[doc].getDocLength()
                    averageDocLength= self.totalLength/ len(self.docDict)
                    w= self.weightTermBM(termID)
                    docScoreNum= (self.k1+ 1)*tf
                    docScoreDen= tf+ (self.k1*(1-self.b+(self.b*(docLength/averageDocLength))))
                    queryScore= ((self.k2+1)*qtf)/(self.k2+qtf)
                    #Final Calc
                    temp= w*(docScoreNum/docScoreDen)*queryScore
            totalScore= totalScore+ temp

        return totalScore

    def calculatingCosineScoreQuery(self, query):
        ##Documents with Scores 
        docScores=OrderedDict()

        ##Figuring out Total Query Sqaured Score 
        querySumSqrd= 0
        for queryTerm in query.procQ: 
            if queryTerm in self.termLookupDict:
                qID= self.termLookupDict[queryTerm]
                temp= self.weightQueryCosine(queryTerm, query)
            else: 
                temp =0
            querySumSqrd= querySumSqrd+ (temp**2)
        
        query.querySumSqrdCosine= querySumSqrd

        ##Figuring Out What Documents To Calculate 
        for queryTerm in query.procQ: 
            if queryTerm in self.termLookupDict:
                qID= self.termLookupDict[queryTerm]
                termEvalNode= self.termDict[qID]

                ##Docs With at Least One Term 
                for doc in termEvalNode.termDict:
                    if doc in docScores:
                            ##Already been calculated
                        continue 
                    else:
                        docScore= self.calculatingCosineScoreDoc(query, doc)
                        docScores[doc]= docScore
            else:
                #Terms don't exist in dictionary
                continue 
        return docScores


    def calculatingDSScoreDoc(self, query, docID):
        evalDocNode= self.docDict[docID]
        docLength= evalDocNode.docLength
        colLength= self.totalLength
        
        #Average doclength
        u= self.totalLength/len(self.docDict)


        score=0
        for queryTerm in query.procQ:
            if queryTerm in self.termLookupDict:
                termID= self.termLookupDict[queryTerm]
                tfDOC= self.termDict[termID].getTermFrequency(docID)
                tfCol=self.termDict[termID].collectionTermFrequency()
                if tfCol ==0:
                    continue 
                num= tfDOC+ (u*(tfCol/colLength))
                den= docLength+ u
                temp= math.log((num/den), 10)
                score= score+temp
            else:
                continue
        return score

                    
    def calculatingCosineScoreDoc(self, query, docID):
        evalDocNode= self.docDict[docID]
        
        ##Calculating Sum Square Term Weights
        docSumSqrdVSM= 0
        for term in evalDocNode.docDict:
            termWeight= self.weightTermCosine(term, docID)
            docSumSqrdVSM= docSumSqrdVSM + (termWeight**2)

        
        ##Calculating Final Score
        score=0
        for term in query.procQ:
            temp=0
            if term in self.termLookupDict:
                termID= self.termLookupDict[term]
                weightTermDoc= self.weightTermCosine(termID, docID)
                weightTermQuery= self.weightQueryCosine(term, query)
                temp= weightTermDoc*weightTermQuery
                temp = temp/math.sqrt((docSumSqrdVSM* query.querySumSqrdCosine))
            else:
                temp=0
            score= score+temp 
        return score

    
    def weightQueryCosine(self, queryTerm, queryNode):
        qID= self.termLookupDict[queryTerm]
        docNode= queryNode.procQ[queryTerm]

        totalDocs= len(self.docDict)
        qtf= docNode.getTermFreq()
        qdf= self.termDict[qID].getDocFrequency()
        idf= math.log((totalDocs/qdf), 10)
        num= (math.log(qtf, 10)+1)*idf
        
        if queryNode.totalWeightCosine == -1: 
            denom= 0 
            for queryTerm in queryNode.procQ:
                temp=0
                if queryTerm in self.termLookupDict:
                    qTempID= self.termLookupDict[queryTerm]
                    qtempTF= queryNode.procQ[queryTerm].getTermFreq()
                    qTempDF= self.termDict[qTempID].getDocFrequency()
                    qTempIDF= math.log((totalDocs/qTempDF), 10)
                    temp= (math.log(qtempTF, 10)+1)*qTempIDF
                    temp= temp**2
                else:
                    temp=0
                denom= temp + denom
            queryNode.totalWeightCosine= denom
        else:
            denom= queryNode.totalWeightCosine
        return num/denom


    
    def weightTermCosine(self, termID, docID): 
        totalDocs= len(self.docDict)
        termfreq= self.termDict[termID].getTermFrequency(docID)
        if termfreq==0:
            return 0
        docFreq= self.termDict[termID].getDocFrequency()
        idf= math.log((totalDocs/docFreq), 10)

        ##Numerator
        num= (math.log(termfreq, 10)+1)*idf

        ##Demoninator 
        denom= 0
        if self.docDict[docID].cosineWeight == -1:
            termsInDOC= self.docDict[docID].docDict
            for term in termsInDOC:
                 termfreq= self.docDict[docID].getTermFrequency(term)
                 docFreq= self.termDict[term].getDocFrequency()
                 idf= math.log((totalDocs/docFreq),10 )
                 temp= (math.log(termfreq, 10)+1)*idf
                 temp= temp**2
                 denom= denom+ temp
            self.docDict[docID].cosineWeight= denom
        else:
            denom= self.docDict[docID].cosineWeight

        return num/denom
    
    #The idf for BM25
    def weightTermBM(self, termID):
        totalDocs= len(self.docDict)
        df= 0
        if termID in self.termDict:
            df= self.termDict[termID].getDocFrequency()
        total= (totalDocs-df+0.5)/(df+0.5)
        return math.log(total, 10)
    

    #After being given all querys that have left to be scored.
    def runAllPositional(self, querysLeft):
        querysLeftNew=[]
        for x in querysLeft:
            query= self.queryNodeList[x]
            scores= self.postionalScoreQuery(query)
            ##No documents were found that contained the query hrase.
            if scores==None:
                querysLeftNew.append(x)
            elif(len(scores)==0):
                querysLeftNew.append(x)
            else:
                ##Documentts were found and scord. 
                self.queryScores[x]=scores
                self.queryScoreType[x]= index.SINGLEPOS
        
        return querysLeftNew
            

    def postionalScoreQuery(self, query):
        flag=False
        mdf= 100000000
        mID= -1

        ##Finding Term with minimum doc frequency
        for queryTerm in query.procQ: 
            if queryTerm not in self.termLookupDict:
                continue
            qID= self.termLookupDict[queryTerm]
            df= self.termDict[qID].getDocFrequency()
            if df< mdf:
                mdf= df
                mID= qID

        ##None of the terms were in the query
        if mdf== 100000000:
            return None

        #Evalualation termNode of minimum query
        evalTermN= self.termDict[mID]


        docQueryTerm= OrderedDict()
        ##Looking Through All Docs
        for doc in evalTermN.termDict:
            flag=False
            ##Need To See If Doc Has All Terms
            for queryTerm in query.procQ:
                if queryTerm not in self.termLookupDict:
                    flag=True
                    break
                qID= self.termLookupDict[queryTerm]
                tf= self.termDict[qID].getTermFrequency(doc)
                if tf==0:
                    flag= True
                    break
            ##Document Did not Have All Terms or term did not exist. 
            # Thus phrase cannot
            if flag:
                continue

            #Need to see if document has all terms 
            phraseFreq= self.postionalFrequency(query, doc)

            ##Document Has All Terms but no positional phrases
            if phraseFreq==0:
                continue

            ##Document has phrase at least once
            docScore= self.calculatingBMScoreDoc(query, doc)
            docQueryTerm[doc]= docScore
        

        return docQueryTerm
        


    #Will calculate if a document has the query terms in the speicified order.
    def postionalFrequency(self, query, doc):
        previousList= None
        queryTermList= self.getQueryTermOrder(query)
        for queryTerm in queryTermList:
            qID= self.termLookupDict[queryTerm]
            termNode= self.termDict[qID]
            termPos= termNode.termPosition[doc]
            if previousList==None:
                previousList= termPos
                continue
            newList= []
            for x in previousList:
                for y in termPos:
                    if (x<=y and y<=x+self.dif):
                        newList.append(y)
                    if (y>x+ self.dif):
                        break
            if len(newList)==0:
                return 0
            previousList= newList
        return len(previousList)

    #Returns the total length of a query
    def getQueryLength(self, query):
        totalLength=0
        for queryTerm in query.procQ:
            tf= query.procQ[queryTerm].getTermFreq()
            totalLength= tf+totalLength
        return totalLength
    

    #Returns the order of terms of a query. 
    def getQueryTermOrder(self, query):
        queryTermList= [None]*self.getQueryLength(query)
        first=True
        min=1
        for queryTerm in query.procQ:
            posTemp= query.procQ[queryTerm].pos

            if(first):
                if(posTemp[0] != 1):
                    min= posTemp[0]
                first=False
            for pos in posTemp:
                pos= pos-1
                pos= pos-(min-1)
                if(queryTermList[pos]==None):
                    queryTermList[pos]= queryTerm
                else:
                    while(queryTermList[pos] != None):
                        pos=pos+1
                    queryTermList[pos]= queryTerm
        return queryTermList
        

    
    #A helper function for me
    def checkStats(self):
        for query in self.queryNodeList:
            print("Query Tag:", query.tag)
            print("Orginal Query", query.orginalQ)
            for term in query.procQ:
                print("Term:", term)
                print("TermFrequency", query.procQ[term].getTermFreq())
                if len(query.procQ[term].pos) != 0:
                    print("Postions",  query.procQ[term].pos)

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



            

