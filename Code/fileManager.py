import os
import statistics

class fileManager:
    def __init__(self, endFolder=""):
        self.files=[]
        self.fileCounter= 0
        self.endFolder= endFolder
        self.endFileName= "invertedIndex.csv"

    def setFolder(self, folder):
        self.endFolder= folder
        if(not os.path.exists(folder)):
            os.makedirs(folder)
        self.endFileName= self.appendFolder(self.endFileName)
            
    def appendFolder(self, filename):
        filename= self.endFolder+"/"+filename
        return filename

    def createFile(self, dict):
        fileName= str(self.fileCounter)+ "-File"
        fileName= self.appendFolder(fileName)
        f= open(fileName, "x")
        f.write("termId, docID, termFrequency, position")
        f.write("\n")
        termID=0
        for key in dict:
            docDict= dict[key]
            if(len(docDict) != 0):
                for key in docDict: 
                    f.write(str(termID)+", ")
                    f.write(docDict[key].getFileLine())
                    f.write("\n")
                docDict.clear()
            termID= termID+1
        self.fileCounter= self.fileCounter+1
        f.close()

    def merge(self, dict, docs):
        if(os.path.exists(self.endFileName)):
            os.remove(self.endFileName)
        lengthFile= self.fileCounter
        listFiles= []
        if(lengthFile==1):
            os.rename(self.appendFolder("0-File"), self.endFileName)
            self.__makeLexicon(dict)
            self.__makeDocList(docs)
            return
        if(lengthFile%2 ==1 ): #Odd. Need to make even
            self.mergeFiles(self.__fileName(lengthFile-1), self.__fileName(lengthFile-2))
            for x in range(lengthFile-2):
                listFiles.append(x)
            listFiles.append(self.fileCounter-1)
            lengthFile= lengthFile-1
        else: #even 
            for x in range(lengthFile):
                listFiles.append(x)
        while (len(listFiles) !=1):
            newList=[]
            for x in range(int(len(listFiles)/2)):
                self.mergeFiles(self.__fileName(listFiles[x*2]), self.__fileName(listFiles[(2*x)+1]))
                newList.append(self.fileCounter-1)
            listFiles=newList
            if(len(listFiles) !=1 and len(listFiles)%2==1):
                self.mergeFiles(self.__fileName(listFiles[len(listFiles)-1]), self.__fileName(listFiles[len(listFiles)-2]))
                listFiles.pop()
                listFiles.pop()
                listFiles.append(self.fileCounter-1)
        os.rename(self.__fileName(str(self.fileCounter-1)), self.endFileName)

        #Making Lexicon
        self.__makeLexicon(dict)

        #Making DocList
        self.__makeDocList(docs)
        return

    def __makeLexicon(self, dict): 
        #Making Lexicon
        if(os.path.exists(self.appendFolder("lexicon.csv"))):
            os.remove(self.appendFolder("lexicon.csv"))
        f= open(self.appendFolder("lexicon.csv"), "x")
        f.write("Term, termID")
        f.write("\n")
        x=0
        for key in dict:
            f.write(key)
            f.write(", ")
            f.write(str(x))
            f.write("\n")
            x=x+1
        f.close()
    
    def __makeDocList(self, docs): 
        if(os.path.exists(self.appendFolder("docs.csv"))):
            os.remove(self.appendFolder("docs.csv"))
        f= open(self.appendFolder("docs.csv"), "x")
        f.write("docID, doc")
        f.write("\n")
        x=0
        for doc in docs:
            f.write(str(x))
            f.write(", ")
            f.write(doc)
            f.write("\n")
            x=x+1
        f.close()


    
    def mergeFiles(self, f1, f2):
        f1= str(f1)
        f2= str(f2)
        file1= open(f1)
        file2= open(f2)
        finalFile=  str(self.fileCounter)+ "-File"
        finalFile= self.appendFolder(finalFile)
        f= open(finalFile, "x")
        f.write("termId, docID, termFrequency, position")
        f.write("\n")
        ##Read once to get titles out of the way 
        lineF1= file1.readline().replace("\n", "")
        lineF2= file2.readline().replace("\n", "")

        #Actual lines
        lineF1= file1.readline().replace("\n", "")
        lineF2= file2.readline().replace("\n", "")
        while(lineF1 != "" or lineF2 != ""):
            #Deciding which side to write
            if(lineF2==""):
                f.write(lineF1)
                f.write("\n")
                lineF1= file1.readline().replace("\n", "")
            elif(lineF1==""):
                f.write(lineF2)
                f.write("\n")
                lineF2= file2.readline().replace("\n", "")
            else:
                listF1= lineF1.split(",")
                termIDF1= int(listF1[0])
                docIDF1= int(listF1[1])
                listF2= lineF2.split(",")
                termIDF2= int(listF2[0])
                docIDF2= int(listF2[1])
                if(termIDF1<termIDF2):
                    f.write(lineF1)
                    f.write("\n")
                    lineF1= file1.readline().replace("\n", "")
                elif(termIDF2<termIDF1):
                    f.write(lineF2)
                    f.write("\n")
                    lineF2= file2.readline().replace("\n", "")
                else:
                    if(docIDF1<docIDF2):
                        f.write(lineF1)
                        f.write("\n")
                        lineF1= file1.readline().replace("\n", "")
                    elif(docIDF2<docIDF1):
                        f.write(lineF2)
                        f.write("\n")
                        lineF2= file2.readline().replace("\n", "")
                    else:
                        ##Equal. Don't think it will come here but if so just pick one. 
                        f.write(lineF2)
                        f.write("\n")
                        lineF2= file2.readline().replace("\n", "")
        #End While loop 
        f.close()
        file1.close()
        file2.close()
        os.remove(f1)
        os.remove(f2)
        self.fileCounter=self.fileCounter+1
    
    def __fileName(self, numF):
        return self.appendFolder(str(numF)+"-File")

    def statsFromInvertedIndex(self, numberOfDocs= -1):
        f= open(self.appendFolder("invertedIndex.csv"))
        line= f.readline()
        line= f.readline()
        tally=0
        currentIndex= 0
        docFreq=[]
        docSet= set()
        if(not line):
            return
        first=True
        while(True):
            line= line.replace(",", "")
            words= line.split()
            index= int(words[0])
            if(first):
                currentIndex=index
                first=False
            doc= int(words[1])
            docSet.add(doc)
            if(index == currentIndex):
                tally= tally+1
            else: 
                docFreq.append(tally)
                tally=1
                currentIndex=index
            line= f.readline()
            if(not line):
                docFreq.append(tally)
                break
        print("Lexicon Length: ", len(docFreq))
        print("Max df: ", max(docFreq))
        print("Min df: ", min(docFreq))
        print("Mean df: ", statistics.mean(docFreq))
        print("Median df: ", statistics.median(docFreq))
        print("Number of Docs: ", len(docSet))

        f.close()
                
                

                



                    
        

        
            
                
            

