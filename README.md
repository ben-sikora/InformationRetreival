# Python Search Engine -- Information Retreival Grad Course Fall 2021

This Python Search Engine is a fully complete indexer, scorer with a functional query expander/reducer. It offers several indexing options (single, stem, positional) and various scoring algothorims (BM25, Cosine, and Dirichlet Smoothing Likelihood Model). I used the TREC Benchmark dataset to evaluate my dataset and achieved similar results to Elastic Search. 

I want to emphasize that this project was entirely my own work and did not use any templates, packages (one exception for the stemmer), or boiler plate code. I designed the architecture, wrote the code, conducted thorough testing , and evaluated the results. It was significant undertaking, and stands as the most substantial coding project I completed during my undergraduate studies.

## Project Structure
### Indexer

***General Structure***
There are three main classes that define my Project 1 implementation: DocumentNode, FileManager, and Lexicon. Document Node contains most of the information found for a term in each document and acts as a “row” of the posting list. It stores the document id, the frequency of a specific term in the document, and if applicable the positions of those terms. FileManager is a class that deals with the writing/management of files to disk and ultimately merging them together. Most of my implementation, however, lies within the Lexicon class. The Lexicon class contains an ordered dictionary that acts as both my posting list and lexicon. An ordered dictionary was imperative because as terms are added/removed it is important to not change the order of the dictionary as it is acting as my lexicon. Inside the ordered dictionary, lies a key value pair of the term and a second ordered dictionary. The second ordered dictionary stores a document id and that document’s node as a key value pair. Therefore, with a term and it’s docID, I can efficiently find and count the appropriate Document Node. Dictionaries were imperative in the design of my project because they support search, insert, and delete in log(n) time. As I will be accessing these dictionaries for each token of the database, any delay in these processes could have exponential effects on my running time (See Figure 2 and 3 in analysis). 

(Note you MUST run my code with Python 3.7 or higher because ordered dictionaries were not supported until then)

 
![Diagram of File Structure of Index](/assets/images/electrocat.png)
*Figure 1: Outline of the nested dictionary structure.* 


**Processing A Document: Start to Finish** 
The entire process for processing, tokenizing, and storing the documents lies within the “createLexiconDir” function of the Lexicon class. Much of the resetting and counting that happens between documents, also occurs in this function. 

1)	*Pre-Processing*
Lines are read from the files, one by one, using the “tagProcessor” function. “TagProcessor” will not output commented lines, xml tags, or empty lines. When tag-Processor comes to the end of a document it will output “</DOC>”, which allows “createLexiconDir” to handle accordingly. 

2)	*Tokenizing*
Once a line has been read, it is passed to the “indexer” function to be counted. “Indexer” breaks the line by spaces and tokenizes the following words using “wordProcessing” and “countIndex.” 
“WordProcessing” accounts for all special tokens and the case that words need to be separated by punctation.  Once words have been processed, they are handed to “countIndex” -- the final part of the tokenizing process—and an index is added to the appropriate node in the nested dictionary and counted. 

There are various switches across “indexer” that account for all the parsing methods. Since we are also mostly parsing by space, special handling was needed to account for line breaks in phrases and dates (the only special token with a space). 

3)	*Creating and Merging Files*
As documents are being read, “countIndex” is tallying what is being added to memory. If that tally reaches the memory constraint, at the end of the document the dictionary is written to a file using FileManager and the docNode dictionary is cleared. After reading all files, the “merge” function in FileManager will merge the temporary files together and output the final lexicon and posting list. 

Special Token Design Decisions (All follow the requirements of the project. Just illustrating clarification for specific things.)
1)	Monetary Value
a.	Monetary symbols are not stored but their values are. For example, $1,000 and 1,000 are both stored as 1000. This was clarified for me in office hours. 
2)	Dates
a.	If a date is given in two numbers from 00 -21 it is counted as 2000’s. Otherwise, it is counted as 1900
b.	If a date is given an invalid number or symbol, it is parsed as individual terms. For example, if it was single term indexing and the text was September 45 2001, the lexicon would be September, 45, 2001. (This same method was applied to tokens, who did not meet the special token requirements). 
c.	For date ranges (i.e 12-14), I stored the values individually. If a query was given it could still find the chosen document. 
3)	URL
a.	Since urls do not have a standard formatting, I only used common substrings to mark them (http, https, .com, .net, .edu, etc). If a url does not contain one of these common substrings, it cannot be detected in my implantation. In the future, I may implement an url “checker” to see if an url leads to a valid website. 
4)	Acronyms
a.	There was a question on how to distinguish acronyms with no periods in the discussion board (USA, DC, etc). I considered marking words in all caps as acronyms, but there was an abundance of normal text that was capitalized. I then made the decision to treat USA as a normal token in my implementation, as it will still be stored the same as U.S.A. I mention this because it has ramifications for my phrase indexing. 

Indexing Design Decisions (All follow the requirements of the project. Just illustrating clarification for specific things.)
1)	Single Positional
a.	Special tokens have been included in my single positional index. If there are multiple indexes for a special token, there positions are all the same. For example, in “part-of speech”, part, speech, and partofspeech will all have the same position. It is important to mark them all as the same position because each of these indexes carry the same importance to the term before and after them. 
b.	Positions are also marked by subsequent tokens. Therefore, if there were multiple line breaks or punctuation between tokens it would not change the position. This was chosen because I did not want the amount of space between tokens, to be differing across documents. (Benefiting some documents down the line but not others). 
2)	TwoPhrase and ThreePhrase
a.	My phrase parsings are separate and must be clarified in the command line.
b.	As I am clearing phrases that are not at a certain frequency, I wasn’t able to clear them from the lexicon without ruining the order of tokens. This became a problem during merging. As such, I had to keep the lexicon with tokens that did not meet the specific phrase frequency. Note when I give the number of phrases in lexicon, I only included those that appeared in the posting list. 
c.	While single positional contains special tokens, twoPhrase and ThreePhrase do not. 
d.	Separate thresholds were chosen for my phrases. To be counted in my two-phrase indexer, a phrase in a document had to appear at least 6 times. To be counted in my three-phrase indexer, a phrase in a document had to appear at least 3 times. See Table 8 and 9 in my results section for my decision-making process. 

### Scorer
### Query Expansion and Reduction

# How To Run
## Indexing
## Scoring
## Query Expansion and Reduction

# Use and Copyright