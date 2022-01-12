from os import sep, strerror
import re
from typing import List, OrderedDict
import argparse
import fileManager
import os
import time
import documentNode
from nltk.stem import PorterStemmer

stopFile= open("stops.txt", "r")
stopList= []
for line in stopFile:
    for word in line.split():
        stopList.append(word)
stopFile.close()


months= {"january":1, "febuary":2, "march":3, "april":4, "may":5, "june":6, 
"july":7, "august":8, "september":9, "october":10, "november":11, "december":12}


monthsAbr= {"jan":1, "feb":2, "mar":3, "apr":4, "may":5, "jun":6, 
"jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}

commonPre= ["pre","post","re", "de", "en", "ex", "inter", "intra", "sub", "tri"]


class Lexicon:
    def __init__(self):
        #Big Three
        self.dict= OrderedDict()
        self.docList= []
        self.currentDoc= -1

        #Indxing Type
        self.parseMethod="single"

        #For Position Index
        self.posCounter=0

        #For Phrase Work 
        self.termBehind= "xx8xx"
        self.termBehind2= "xx8xx"
        self.phrasesInCurrentDoc= []
        self.phraseFreqMinTwo=6
        self.phraseFreqMinThree= 3

        #For Stemming
        self.stemmer= PorterStemmer()
        
        #Memory management
        self.inputDir=""
        self.fileManage= fileManager.fileManager()
        self.currentMemory=0
        self.memoryConstraint= -1
        self.outputFolder="Output"

        #Special Case Month Handling
        self.month= ""
        self.day= -1
        self.year= -1
        
        #Time work 
        self.timeStart= 1.0
        self.timeMergeStart= 1.0
        self.timeEnd= 1.0
    def grabDoc(self, docID):
        print(self.docList[docID])

    def createLexiconDir(self):
        self.__argParser()
        self.timeStart= time.perf_counter()
        files= os.listdir(self.inputDir)
        docID=0
        self.fileManage.setFolder(self.outputFolder)
        for file in files: 
            print("Looking into... ", file)
            fileName= self.inputDir+"/"+file
            lines= self.__tagParser(fileName)
            docFlag= True
            textFlag=True
            for line in lines:
                if(docFlag):
                    #Start of a new documenet
                    self.currentDoc= docID
                    self.docList.append(line)
                    self.posCounter=0
                    self.termBehind= "xx8xx"
                    self.termBehind2= "xx8xx"
                    docID= docID+1
                    docFlag=False
                elif(textFlag and not docFlag):
                    #skip this line. Parent Doc Number
                    textFlag=False
                elif(line=="</DOC>"):
                    #Reached end of a document
                    docFlag=True
                    textFlag= True

                    if(self.parseMethod == "twoPhrase" or self.parseMethod == "threePhrase"):
                        #Clearing phrases that did not meet the min freq
                        #constraint
                        self.__phraseCleaning()
                    
                    if(self.memoryConstraint != -1 and 
                    self.currentMemory>= self.memoryConstraint):
                        #If above memory constraint will create a file
                        #and clear the dictionary
                        self.fileManage.createFile(self.dict)
                        self.currentMemory=0
                else:
                    #Normal line to be indexeded
                    self.indexer(line)

        #Final File Creation and Merging
        self.fileManage.createFile(self.dict)
        self.currentMemory=0
        self.timeMergeStart= time.perf_counter()
        self.fileManage.merge(self.dict, self.docList)
        self.timeEnd= time.perf_counter()

        #Reporting
        self.printTimes()
        self.fileManage.statsFromInvertedIndex()

    def printTimes(self):
        print("Time to create temp files: ", (self.timeMergeStart- self.timeStart))
        print("Time to merge files: ", (self.timeEnd- self.timeMergeStart))
        print("Total Runtime: ", (self.timeEnd- self.timeStart))
    
    def __phraseCleaning(self):
        phraseFreqMin= -1
        if(self.parseMethod=="twoPhrase"):
            phraseFreqMin= self.phraseFreqMinTwo
        else:
            phraseFreqMin= self.phraseFreqMinThree

        for phrase in self.phrasesInCurrentDoc:
            dictDoc= self.dict[phrase]
            docNode=dictDoc[self.currentDoc]
            phraseFreq= docNode.getTermFreq()
            if(phraseFreq < phraseFreqMin):
                dictDoc.pop(self.currentDoc)
                self.currentMemory= self.currentMemory-1
                #if(len(dictDoc)==0):
                   #self.dict.pop(phrase)
        self.phrasesInCurrentDoc.clear()
    

    def manualSwitch(self, index="single"):
        self.parseMethod= index
    
    def clear(self):
        self.dict.clear()
        #For Position Index
        self.posCounter=0

        #For Phrase Work 
        self.termBehind= "xx8xx"
        self.termBehind2= "xx8xx"

    def getDict(self):
        return self.dict
    
    def indexer(self, line):
        ##Case Folding 
        line= line.lower()

        #Removing commas as not stop words or special cases
        line= re.sub(r",", "", line)

        #Splitting line by spacing one at a time 
        listWords=re.split(r" ", line, maxsplit=1)

        #Setting Flags for Specific Indexing
        flag= True
        posParsing= False 
        phraseParsing= False
        termToBeAdded=False 

        if(self.parseMethod== "singlePos"):
            posParsing= True
        if(self.parseMethod== "twoPhrase" or self.parseMethod== "threePhrase"):
            phraseParsing= True
            #Searching for punctation. Phrases will not cross any puncation. 
            stopSearch= re.compile(r'[^\w+\d+\']')
        

        while(flag):
            # Need to see if this is a word that can be part of a phrase. If 
            #there is any punctation it cannot be. 
            if(phraseParsing and not stopSearch.search(listWords[0]) and "_" not in listWords[0]):
                termToBeAdded= True
            else:
                #Marking that the term cannot be part of a phrase 
                self.termBehind= "xx8xx"
                self.termBehind2= "xx8xx"
            
            #Stripping ending punctation. Mostly periods
            listWords[0]= re.sub(r"\.('')*$", "", listWords[0])

            if((listWords[0] in stopList or listWords[0]== "") and not posParsing):
                #do nothing for single, stem, and phrase index. 
                #Also have to reset both the date and phrase counter 
                termToBeAdded= False
                self.termBehind= "xx8xx"
                self.termBehind2= "xx8xx"
                self.month= ""
                self.day= -1
                self.year= -1
            else:
                if(listWords[0] in months and not phraseParsing):
                    #This could be a month that could be counted
                    self.month= listWords[0]
                elif(self.month != "" and self.year == -1 and self.day == -1 and not phraseParsing):
                    #This could be a day that could be counted
                    if(listWords[0].isnumeric() and int(listWords[0])<33 and int(listWords[0])>0):
                        self.day= int(listWords[0])
                    else:
                        #Did not meet specifications. 
                        # Then have to log what was stored
                        self.posCounter= self.posCounter+1
                        self.__logMonth()
                        self.posCounter= self.posCounter+1
                        self.countIndex(listWords[0])
                        self.month= ""
                        self.day= -1
                        self.year= -1
                elif(self.month != "" and self.day != -1 
                and self.year == -1 and not phraseParsing):
                    if(listWords[0].isnumeric() and int(listWords[0])<9999 and int(listWords[0])>0):
                        #Correct month, date, and year. Count it as an index! 
                        self.year= int(listWords[0])
                        self.__logMonth()
                    else:
                        #Did not meet specifications. 
                        # Then have to log what was stored
                        self.posCounter= self.posCounter+1
                        self.__logMonth()
                        self.posCounter= self.posCounter+1
                        self.countIndex(str(self.day))
                        self.posCounter= self.posCounter+1
                        self.countIndex(listWords[0])
                        self.month= ""
                        self.day= -1
                        self.year= -1
        
                else:
                    #Reseting Months 
                    self.month= ""
                    self.day= -1
                    self.year= -1
                    #Special case handling and tokenizing other 
                    # stops besides spaces
                    processWords= self.__wordProcessing(listWords[0])

                    #List of indexes to be counted from word
                    if(processWords != None):
                        if(posParsing):
                            #Counting Position of the word
                            self.posCounter=self.posCounter+1
                        for wordProc in processWords:
                            #If single, singlePos, or stem 
                            if (wordProc != None and wordProc != "" and not phraseParsing):
                                self.countIndex(wordProc)
                            #Phrase parsing 
                            if (wordProc != None and phraseParsing):
                                #This will also check to see if the term is a 
                                # special case. If not cannot be part of a phrase. 
                                if(termToBeAdded and wordProc != "" and wordProc==listWords[0]):
                                    if(self.parseMethod== "twoPhrase"):
                                        if(self.termBehind != "xx8xx"):
                                            index=self.termBehind+wordProc
                                            index= re.sub(r"\'", "", index)
                                            self.countIndex(index)
                                    else: #in three phases
                                        if(self.termBehind != "xx8xx" and self.termBehind2 != "xx8xx" ):
                                            index=self.termBehind2+ self.termBehind+wordProc
                                            index= re.sub(r"\'", "", index)
                                            self.countIndex(index)
            
            #Moving Back the Phrase Markers
            if(termToBeAdded and self.termBehind != "xx8xx"):
                self.termBehind2=self.termBehind
            if(termToBeAdded):
                self.termBehind=listWords[0]
            termToBeAdded= False
            
            if(len(listWords)==1):
                #No more words to parse in line. 
                flag=False
            else:
                listWords=re.split(r" ",listWords[1], maxsplit=1)
    
    #Will log the correct month as the index. Else will just log that month. 
    def __logMonth(self):
        if(self.month != "" and self.day != -1 and self.year != -1):
            index= str(months[self.month])+ "/"+ str(self.day)+ "/"+ str(self.year)
            self.countIndex(index)
        else:
            self.countIndex(self.month)
    
    #Using an index will count in the appripate part of the dictionary, 
    #appriopate counters, and also set up document nodes. 
    def countIndex(self, index):
        if(self.parseMethod=="stem"):
            index= self.stemmer.stem(index)
        if(index in self.dict.keys()):
            self.__findDocNode(index)
        else:
            self.currentMemory= self.currentMemory+1
            self.dict[index]= {self.currentDoc: documentNode.DocumentNode(self.currentDoc)}
            if(self.parseMethod=="singlePos"):
                self.dict[index][self.currentDoc].updatePos(self.posCounter)
            if(self.parseMethod == "twoPhrase" or self.parseMethod == "threePhrase"):
                self.phrasesInCurrentDoc.append(index)

    def __argParser(self):
        parser= argparse.ArgumentParser(prog= 'main')
        parser.add_argument('-single', dest='single', action= 'store_true')
        parser.add_argument('-singlePos', dest= 'singlePos', action= 'store_true')
        parser.add_argument('-stem', dest= 'stem', action= 'store_true')
        parser.add_argument('-twoPhrase', dest= 'twoPhrase', action= 'store_true')
        parser.add_argument('-threePhrase', dest= 'threePhrase', action= 'store_true')
        parser.add_argument('-memory', dest= 'memory', nargs=1, type=int)
        parser.add_argument('-i', dest= 'inp', nargs=1, type=str,required=True)
        parser.add_argument('-o', dest= 'oup', nargs=1, type=str)

        args= parser.parse_args()
        if(args.single):
            self.parseMethod= "single"
        elif(args.singlePos):
            self.parseMethod= "singlePos"
        elif(args.stem):
            self.parseMethod= "stem"
        elif(args.twoPhrase):
            self.parseMethod= "twoPhrase"
        elif(args.threePhrase):
            self.parseMethod= "threePhrase"
        else:
            raise Exception("No Arugements Given")
        
        self.inputDir= args.inp[0]
        if(args.oup != None):
            self.outputFolder= args.oup[0]
        if(args.memory != None):
            self.memoryConstraint= int(args.memory[0])
        ##Addd This line 
        self.outputFolder= self.outputFolder+"/"+ self.parseMethod

    #Index already exists and needs to be found and counted
    def __findDocNode(self, index):
        dictDocs= self.dict[index]
        if self.currentDoc in dictDocs:
            dictDocs[self.currentDoc].add()
            if(self.parseMethod=="singlePos"):
                dictDocs[self.currentDoc].updatePos(self.posCounter)
        else:
            #Doc Node does not exist for given dictionary. Must be created 
            self.currentMemory= self.currentMemory+1
            newdoc=documentNode.DocumentNode(self.currentDoc)
            if(self.parseMethod=="singlePos"):
                    newdoc.updatePos(self.posCounter)
            dictDocs[self.currentDoc]= newdoc
            if(self.parseMethod == "twoPhrase" or self.parseMethod == "threePhrase"):
                self.phrasesInCurrentDoc.append(index)
                

    #Used in __tagParseer to replace specail html characters.
    def __specCharReplacer(self, line):
        #blank 
        line= re.sub(r'&blank;'," ", line)
        #Hyphen
        line= re.sub(r'&hyph;',"-", line)
        #Section
        line= re.sub(r'&sect;',"§", line)
        #Times
        line= re.sub(r'&times;',"x", line)
        #Ampersand
        line= re.sub(r'&amp;',"&", line)

        return line
    
    #Will read the raw lines of the document 
    def __tagParser(self, fileName):
        frontTag= re.compile(r'<\w+>', flags= re.IGNORECASE)
        backTag= re.compile(r'</\w+>', flags= re.IGNORECASE)
        endDocTag= re.compile(r'</DOC>', flags= re.IGNORECASE)
        importantTags= ["</DOCNO>", "</PARENT>", "</TEXT>"]
        with open(fileName, "rt") as doc:
            line= doc.readline()
            while line: 
                if "<!--" not in line and line != "\n":
                    if frontTag.search(line) or backTag.search(line):
                        if(endDocTag.search(line)):
                            yield "</DOC>"
                        else:
                            extractor= re.compile(r'<\w+> ?(.+) ?(</\w+>)', flags= re.IGNORECASE)
                            match= extractor.search(line)
                            if(match):
                                if(match.group(2) != None and match.group(2)  not in importantTags):
                                    yield self.__specCharReplacer(match.group(1).rstrip()+".")
                                else:
                                    yield self.__specCharReplacer(match.group(1))
                    else:
                        line= line.rstrip()
                        line= line.strip()
                        if(line != ""):
                            yield self.__specCharReplacer(line)
                line= doc.readline()

    def __wordProcessing(self, word):    
        #Words List
        wordsList=[]
        #Alphabet digit
        alphDigit= re.compile(r'^([a-z]+)-(\d+)$')
        alphDigitThree= re.compile(r'^([a-z]{3,})-(\d+)$')
        #Digit Alphabet
        digitAlph= re.compile(r'^(\d+)\-([a-z]+)$')
        digitAlphThree= re.compile(r'^(\d+)-([a-z]{3,})$')
        #Hyphenated Terms 
        hyph= re.compile(r'^([a-z]+)\-([a-z]+)\-*([a-z]*)\-*([a-z]*)$')
        #Money
        moneyandNum= re.compile(r'^\${0,1}\d+(\.{0,1}\d+)?\${0,1}$')
        #Dates 
        dateGen= re.compile(r'^(\d*\w*)[\/ -](\d+)[\/ -](\d+)$')
        dateNum= re.compile(r'^(\d+)[\/ -](\d+)[\/ -](\d+)$')
        #Email Addresses
        email= re.compile(r'\w+@\w+\.\w+')
        #Ip Addresses
        ip= re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')
        #websites
        commonWeb= ["http", "https", ".com", ".net", ".org", ".gov", ".zone"]
        webBool= False
        for sub in commonWeb: 
            if(word.find(sub) != -1):
                webBool= True
                break
        #fileExtensions
        fileExtensions= [".pdf", ".hmtl", ".py", ".csv", ".email", ".pkg"]
        for sub in fileExtensions: 
            if(word.find(sub) != -1):
                word= re.sub(r'\.', "?", word)
                break
        
        #Period Remover abreviations and file extensions
        period= re.compile(r'[a-z]+\.')

        #generic puncation search 
        generic= re.compile(r'[^\w\d\']')

        if(alphDigit.search(word)):
            if(alphDigitThree.search(word)):
                match= alphDigitThree.search(word)
                wordsList.append(re.sub(r"[^\w]", "", word))
                wordsList.append(match.group(1))
            else:
                wordsList.append(re.sub(r"[^\w]", "", word))
            return wordsList
        elif(digitAlph.search(word)):
            if(digitAlphThree.search(word)):
                match= digitAlphThree.search(word)
                wordsList.append(re.sub(r"[^\w]", "", word))
                wordsList.append(match.group(2))
            else:
                wordsList.append(re.sub(r"[^\w]", "", word))
            return wordsList
        elif(hyph.search(word)):
            word= re.sub(r'\-', " ", word)
            wordsTemp= word.split()
            word=""
            prefix= False
            for wordT in wordsTemp:
                if(wordT in commonPre):
                    prefix=True
                if(wordT not in stopList and wordT not in commonPre):
                    wordsList.append(wordT)
                    word= word+wordT
                elif(wordT not in commonPre):
                    word= word+wordT
            if(not prefix):
                wordsList.append(word)
            return wordsList
        elif(moneyandNum.search(word)):
            match= moneyandNum.search(word)
            if(match.group(1)!=None and int(re.sub(r'\.', "", match.group(1))) ==0):
                #Removing trailing zeros
                word= re.sub(r'\.0*', "", word)
                wordsList.append(word.replace("$", ""))
            else:
                #Storing float 
                wordsList.append(word.replace("$", ""))
            return wordsList
        elif(dateGen.search(word)):
            match= dateGen.search(word)
            if(dateNum.search(word) or (str(match.group(1)) in monthsAbr)):
                if(dateNum.search(word)):
                    month= int(match.group(1))
                elif(match.group(1) in monthsAbr): 
                    month= monthsAbr[match.group(1)]
                day= int(match.group(2))
                year= int(match.group(3))
                if(0<month and month<=12):
                    if(0<day and day<32):
                        if(0<=year and year<=9999):
                            if(year<100):
                                if(0<=year and year<=21):
                                    if(year<10):
                                        year="200"+ str(year)
                                    else:
                                        year="20"+ str(year)
                                else:
                                    year="19"+ str(year)
                            wordsList.append(str(month)+ "/"+str(day)+"/"+ str(year))
                            return wordsList
            #Some parsiing problem with dates. Just treat everything as token
            word= re.sub(r'[^\w\d]', " ",word)
            return word.split()
        elif(email.search(word)):
            wordsList.append(word)
            return wordsList
        elif(ip.search(word)):
            wordsList.append(word)
            return wordsList
        elif(webBool):
            wordsList.append(word)
            return wordsList
        elif(period.search(word)):
            word= re.sub(r'\.', "", word)
            if(generic.search(word) or "_" in word):
                word= re.sub(r'[^\w\d]', " ",word)
                word= re.sub(r'_', " ",word)
                tempList= word.split()
                for wordT in tempList:
                    wordsList.append(wordT)
                return wordsList
            else:
                wordsList.append(word)
                return wordsList
        else:
            if(generic.search(word) or "_" in word):
                word= re.sub(r'[^\w\d\']', " ",word)
                #Underscore requires special treatment as it is included with \w
                word= re.sub(r'_', " ",word)
                tempList= word.split()
                for wordT in tempList:
                    if(self.parseMethod == "singlePos"):
                        wordsList.extend(self.__wordProcessing(wordT))
                    elif(wordT not in stopList):
                        wordsList.extend(self.__wordProcessing(wordT))
                return wordsList
            #Final removal of punctation. At this point its just apostrophes.
            word= re.sub(r'[^\w\d]', "",word)
            wordsList.append(word)
            return wordsList

