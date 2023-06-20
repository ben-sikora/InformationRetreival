# Python Search Engine -- Information Retreival Grad Course Fall 2021

This Python Search Engine is a fully complete indexer, scorer with a functional query expander/reducer. It offers several indexing options (single, stem, positional) and various scoring algothorims (BM25, Cosine, and Dirichlet Smoothing Likelihood Model). I used the TREC Benchmark dataset to evaluate my dataset and achieved similar results to Elastic Search. 

I want to emphasize that this project was entirely my own work and did not use any templates, packages (one exception for the stemmer), or boiler plate code. I designed the architecture, wrote the code, conducted thorough testing , and evaluated the results. It was significant undertaking, and stands as the most substantial coding project I completed during my undergraduate studies.

## Project Structure
### Indexer

***General Structure***

There are three main classes that define my Project 1 implementation: DocumentNode, FileManager, and Lexicon. Document Node contains most of the information found for a term in each document and acts as a “row” of the posting list. It stores the document id, the frequency of a specific term in the document, and if applicable the positions of those terms. FileManager is a class that deals with the writing/management of files to disk and ultimately merging them together. Most of my implementation, however, lies within the Lexicon class. The Lexicon class contains an ordered dictionary that acts as both my posting list and lexicon. An ordered dictionary was imperative because as terms are added/removed it is important to not change the order of the dictionary as it is acting as my lexicon. Inside the ordered dictionary, lies a key value pair of the term and a second ordered dictionary. The second ordered dictionary stores a document id and that document’s node as a key value pair. Therefore, with a term and it’s docID, I can efficiently find and count the appropriate Document Node. Dictionaries were imperative in the design of my project because they support search, insert, and delete in log(n) time. As I will be accessing these dictionaries for each token of the database, any delay in these processes could have exponential effects on my running time (See Figure 2 and 3 in analysis). 

(Note you MUST run my code with Python 3.7 or higher because ordered dictionaries were not supported until then)

 
![Diagram of File Structure of Index](/assets/figure1Indexer.jpg)

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
***General Structure***

When going about my design for scoring, I had two goals in mind: The first was to never read through the posting list more than once. And the second was to minimize the number of duplicate calculations. The structure I then came to, was a series of dictionaries that stored “evaluation” nodes for both documents and terms. Upon reading the posting list, I would create and manage these nodes so that they contain all the relevant information for a given term or document. The goal of making “evaluation” nodes was so that when I needed a statistic about a term or document, I would only have to find the appropriate node and type the function. The evaluation nodes also made it intuitive for me to store document and term weights, which solve my initial set out of removing duplicate calculations. For simplicity, I also applied the node model to the queries. Although I believe there are other structures that minimize storage space better, my end-design made it very intuitive to calculate Cosine, BM25, and Dirichlet Smoothing relevancy scores. The entire structure is created, stored, and run through the Evaluator class. 
 

![Diagram of File Structure of Scorer](/assets/figure1Scorer.jpg)

*Figure 1: Outline of my Evaluation Node Structure.*


**Program Flow of Static Searching**

The entire process for static searching is contained with the “staticSearching” method of the Evaluator Class. 

1)	*Reading Files in and Query Processing* 
The lexicon, documents, and posting list are all read using their associated “read” methods. The read methods are the ones that build and maintain the evaluation nodes listed in Figure 1, and thus are one of the most crucial components of my project. For processing the query list, I used the “buildQuery” class, which utilizes a skeleton version of my project 1 to process the queries into terms and storing them in “queryNodes.” All the query nodes are then handed back to the evaluator class and stored under “queryNodeList.”

2)	*Calculations, Calculations, Calculations!*
For each of the retrieval methods—Cosine, BM25, and Dirichlet Smoothing—there are three methods. The first, “allCalculations*type*”, is a simple for loop to calculate scores for all the queries. The second, “calculating*type*Query”, calculates all the doc scores for a given query. The final method, “calculating*type*Doc” calculates the score of a document given a certain query. The methods work in a tree structure, using the method preceding it, to handle all the calculations. There are also various helper functions to help with finding term weights. The scores of documents in a query are stored in dictionaries, which are then stored in the “queryScores” list. 

3)	*Making the Results File*
When all the calculations have been completed, the results are printed in “makeResults.” For each query, the document scores are extracted from the dictionary, sorted, and then ranked. Then they are printed following the Trec Eval format, and given the appropriate tag of the retrieval method—Cosine, BM25, or Dirichlet smoothing

Program Flow of Dynamic Searching
The entire process for dynamic searching is contained with the “dynamicSearching” method of the Evaluator Class. 

1)	*Phrase Searching*
Since my project 1 implementation split phrases into two parts, I did the same thing for project 2. First my program begins with three phrases. It will read and process the associated queries, posting list, lexicon, and docs. Then for each query, if the any phrase term is equal to or above 3 (Note Table 9 For This Decision), the scores will be calculated using BM25. I chose BM25 for dynamic searching, because it was the fastest retrieval method (Table 1) and, since proximity searching requires a large amount of processing, I didn’t want to extend the search time any more than I had too. Once all queries have been checked, the entire Evaluator is cleared, and the process is repeated for two phrases for all queries that were not given scores. A list of query IDs, “querysLeft,” tracks all the queries which remain to be calculated following each stage. 

2)	*Proximity Searching*
Once all the queries with a high enough document frequency are scored, the remaining are passed to “runAllPositional” to be scored using proximity searching. “runAllPositional” uses a similar tree structure of the retrieval methods, to find documents with the given query phrases. Since BM25 can already determine the presence and absence of query terms, it was important that my proximity search took the order of terms as a high priority. For a document to be scored by proximity search with BM25, it must have contained all the query terms in the exact order of the query and within three words of the term before it (Note Table 10 For This Design Decision). 

3)	*Single BM25*
For every query, if 100 docs have yet to be scored either by phrasing or proximity, then the query is passed to be scored by BM25 using statics single indxing. 

4)	*Making the Results File*
Since for every query there can be two sets of scores, one for phrasing or proximity and another for single, special handling had to be taken for printing the results file. In “makeResultsDynamic,” the first set of scores, either phrase or proximity, are ranked and printed. Then if 100 doc threshold is still not meant, the second set of scores that were calculated using single indexing, are ranked, and printed under the initial scores. 


**Design Decisions for Retrieval Methods**

All
1.	If a query term is not in the collection at all, that term is skipped. This was chosen because although BM25 can handle having no terms in the collection, cosine and Dirichlet Smoothing become undefined (Dividing by 0 for idf of cosine, and log of 0 in Dirichlet Smoothing). 
Cosine: 
1.	As specified in the project, I used this normalized weight function.  
a.	 ![Cosine Normalized Weight Function Equation](/assets/figure2Scorer.png)

BM25
1.	The following constants for BM25 were chosen for both Elastic Search and My Engine (Note K2 is not an option with Elastic Search). Please see Tables 4-6 for the justification of this decision. 
a.	K1= 1.2
b.	B= 0.75
c.	K2= 500
LM
1.	For my language model, I chose a Dirichlet Smoothing query likelihood model, specifically the log version of Dirichlet Smoothing. 
a.	![LM Dirchlet Smoothing Weight Function Equation](/assets/figure3Scorer.png)
b.	For u, I used 429 (the average document length in the collection) for both my own engine and Elastic Search. 

### Query Expansion and Reduction

***General Structure***

My goal for this project was to try to integrate as much of query reduction and expansion into project two as possible. This way I would be able to compare the results from my project two with a high degree of confidence and, if there were any changes needed to be made to query scoring, reduction and expansion would not need to be changed. It was because of this that no new classes were created for this project, and the entire structure relies within the Evaluator and queryBuild classes. For the evaluator class specific query expansion, reduction, and combined methods were added but the relevance calculation methods for BM25 or the language model were not modified. And, for the queryBuild class, there were only changes to the both the query file reading and to adding of term weights. Overall, I was pleased with how integrated my project as I was able to use many of the methods I already had in place from project two.  

**Overall Design Decisions**

1)	*Using Only Single Indexing* 
I chose only to use single indexing, instead of stemming, phrases, or positional, because since the goal of this project is to examine the effects of query reduction and expansion, I thought it would be best to only use one indexer for comparison. In addition, I was also considering these factors: 
a.	Phrase and positional indexing don’t inherently apply for query expansion.
b.	Phrases have incredibly limited terms.
c.	Addition of stop words did not make much of a difference in the results of project 2.
d.	The Stem indexing results from project 2, were highly inconsistent and did not seem to have that much of an effect

2)	*Using Only BM25 and LM*
Again, since the goal for this project is to experiment with reduction and expansion, I thought it was best to minimize other parameters as much as possible and chose only to use BM25 and my language model. In addition, cosine had the worst performance in my project 2 results. As a reminder, for my language model, I used Dirchlet Smoothing. 

3)	*Default Parameters* 
The default parameters for my project are 5 documents retrieved per query and 5 terms per document. The default query threshold is 0.6. These defaults were chosen as they provide the best performance with BM25 across each of the methods (Table 1, Table 5, and Table 7). If you ever want to change these defaults, please consult the read me for this project as you can do so from the terminal.  

**Program Flow and Design Decisions of Query Expansion**  

For Query Expansion, I chose to do the Rocchio Vector Space Relevance Feedback without the subtracting of non-relevant terms (thus a y of 0). The entire structure of query expansion lies in the “queryExpansion” method of the Evaluator Class. 

1) *Reading Files in and Scoring*
All the reading of files and initial scoring was the same as for project two. The relevance method used is either BM25 or the language model.  

2) *Choosing The Terms to Add to Query* 
The actual expansion of the query is contained within the “makeExpansionQuery” method. I first rank the documents using the scoring of the specified relevance calculation. Then taking the specified top docs, I loop through each documents’ terms and calculate their relative term importance score using the “topTermsInDoc” method. The importance score I used was the product of idf and the number of times the term appears in the selected relevant document set. For each document, I rank its terms using the importance score and select the top terms to be added to the query. When adding expanded terms to the query, I used only a 0.05 beta weight which was represented in the query term frequency (Note Table 4 for this Design Decision).

3) *Rerunning Scoring with New Expanded Query*
After the new queries have been created, I clear and rerun the scoring of the documents with the new queries and print the ranked results. 

**Program Flow and Design Decisions of Query Reduction**  

For Query Reduction, I chose to do a percentage total of the query terms based on term idf. The entire structure of query expansion lies in the “queryReduction” method of the Evaluator Class. 

1)	*Reading Files In*
All the reading of files in was the same as before, except for the reading of the query file. Since we are reading the narrative section for query reduction, I built another method in the queryBuild class called “tagParserReduction” to account for this.

2)	*Modifying and Reducing Query* 
After creating the initial query terms, the reduction of the query happens in the “makeReducedQuery” method. The query terms are ranked by their idfs, and then a new query is created with the specified query threshold.   

3)	*Rerunning Scoring with New Reduced Query*
After the new queries have been created, I score the documents using the specified retrieval method and print the ranked results. 


**Program Flow and Design Decisions of Combined Query Expansion and Reduction** 

For the combined Query Reduction and Expansion, I chose to run reduction first and then expansion. The entire structure of combined query reduction and expansion lies in the “queryReduction” method of the Evaluator Class. 

1)	*Reading Files In*
As I am using query reduction, I read all the files as normal but used the “tagParserReduction” to read the narrative section of the queries.  

2)	*Query Reduction, Expansion, and Results*
I run query reduction first and score the documents. Then using the query from reduction and the scored documents, I select the top documents and terms for expansion. After creating the new query, I calculate the scores one final time and print the results. All the methods used are from above. 


# How To Run

Before Runnning: 
Please run with Python 3.7 or higher. My implementation 
relys on ordered dictionaries which were not supported until then.

The only non-standard library that was used was my Porter Stemmer. 
Please make sure you install nltk before running. 
https://www.nltk.org/install.html

Also make sure that stops.txt is in the source directory
## Indexing
***HOW TO RUN:***

I used switches to parse my program. Below are their calls 
and how to use them 

-i [input directory] *REQUIRED* 
Please provide the path to the given folder that contains the files to run. 
Do not include the last "/" in the folder. 

-o [output directory]
If you want to specifcy the ouput directory to be set, please add it here. If 
no directory is given, by default it will create and output a "Output" 
folder. 

-memory [memory constraint]
If you want to specificy a memory constraint, add the desired memory after this tag. 
If no tag is given, my program will use unlimted memory

Indexing tags (Use to pick which indexer to use)
-single
-singlePos
-stem
-twoPhrase
-threePhrase

Some example commands: 
```
python3 build.py -single -i BigSample -memory 1000
python3 build.py -i BigSample -single -o OutputSpecail 
python3 build.py -i BigSample -stem -memory 100000
python3 build.py -twoPhrase -i BigSample
```
## Scoring

***HOW TO RUN:***

**STATIC SEARCHING**
I used switches to parse the files

-index [index directory] *REQUIRED* 
Please provide the path to the given folder that contains the indexes to run. 
Do not include the last "/" in the folder. 

-query [query file] *REQUIRED* 
Please input the file that contains all the querys. 
If that file is within a folder please speicify that specific path.

Choosing Indexer (Please select one) *REQUIRED* 
-single 
-stem

Choosing Retreival Method (Please select one) *REQUIRED* 
-cosine
-bm25
-lm

-t [run trec_eval] 
If trec_eval and qrel.txt are on in the same source directory as query.py, you can chose to add the -t tag 
which will run trec_eval for you and print the results. 

-o [output directory] 
If you would like to specifcy the output directory of the results.txt file, please change that here. 

Some example commands: 
```
python3 query.py -index Output -query querfile.txt -single -bm25 -t 
python3 query.py -index Output -query querfile.txt -lm -stem -o ResultsFolder
python3 query.py -index Output -query querfile.txt -bm25 -stem -o ResultsFile -t
```


**DYNAMIC SEARCHING**
I used switches to parse the files

-index [index directory] *REQUIRED* 
Please provide the path to the given folder that contains all the indexes to run. 
Do not include the last "/" in the folder. 

-query [query file] *REQUIRED* 
Please input the file that contains all the querys. 
If that file is within a folder please speicify that specific path.

-phraseThreshold [changing Phrase Threshold]
As stated in my desing document, if you would like to change the phrase threshold so you can see the results.txt
file and verify phrases are working properly, you can do so here. 

-t [run trec_eval] 
If trec_eval and qrel.txt are on in the same source directory as query.py, you can chose to add the -t tag 
which will run trec_eval for you and print the results. 

-o [output directory] 
If you would like to specifcy the output directory of the results.txt file, please change that here. 

```
Some example commands: 
python3 query_dynamic.py -index Output -query querfile.txt -t 
python3 query_dynamic.py -index Output -query querfile.txt -o ResultsFolder
python3 query_dynamic.py -index Output -query querfile.txt -phraseThreshold -t
```
## Query Expansion and Reduction

***HOW TO RUN:***

QUERY EXPANSION, REDUCTION, AND COMBINED
I used switches to parse the files

-index [index directory] *REQUIRED* 
Please provide the path to the given folder that contains the indexes to run. 
Do not include the last "/" in the folder. 

-query [query file] *REQUIRED* 
Please input the file that contains all the querys. 
If that file is within a folder please speicify that specific path.

Choosing Indexer (Please select one) *REQUIRED* 
-single 

Choosing Retreival Method (Please select one) *REQUIRED* 
-bm25
-lm

Choosing Query Modification Method (Please select one) *REQUIRED*
-queryE
-queryR
-queryRE

Key:
queryE: Query Expansion
queryR: Query Reduction 
queryRE: Query Reduction and Expansion

Specifying Amount of Terms Per Document For Expansion
If you would like to specify your own term parameter please write the flag and the number you 
would like next to it. By default this value is 5.  
-terms [number]

Specifying Amount of Documents Per Query For Expansion
If you would like to specify your own doc parameter please write the flag and the number you 
would like next to it. By default this value is 5.  
-docs [number]

Specifying Query Threshold For Query Reduction
If you would like to specify your own doc parameter please write the flag and the number you would like next to it. By default this value is 5.  
-threshold [number (0-1)]

-t [run trec_eval] 
If trec_eval and qrel.txt are on in the same source directory as query.py, you can chose to add the -t tag 
which will run trec_eval for you and print the results. 

-o [output directory] 
If you would like to specifcy the output directory of the results.txt file, please change that here. 

Some example commands: 
```
python3 project3.py -index Output -query queryfile.txt -single -bm25 -t -queryR
python3 project3.py -index Output -query queryfile.txt -single -lm -t -queryRE
python3 project3.py -index Output -query queryfile.txt -single -lm -queryE
python3 project3.py -index Output -query queryfile.txt -single -lm -queryE -terms 5 -docs 3
python3 project3.py -index Output -query queryfile.txt -single -lm -queryR -threshold 0.2
python3 project3.py -index Output -query queryfile.txt -single -lm -queryRE -threshold 0.2 -terms 5 -docs 2
```

