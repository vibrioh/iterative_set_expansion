## Files
Name | Usage
--- | ---
iterative_set_expansion.py | main program
transcript.txt | sample result
README.md | descriptions
NLPCore.py | PythonNLPCore component
data.py | PythonNLPCore component

absent but required folder:
*/stanford-corenlp-full-2017-06-09*

## Run on Google Cloud
### Deploy
1. install/upgrade packages for Ubuntu 14.04 LTS
```bash
sudo add-apt-repository ppa:webupd8team/java
sudo add-apt-repository ppa:jonathonf/python-2.7
sudo apt-get update
sudo apt-get install oracle-java8-installer
sudo apt-get install unzip
sudo apt-get install git
sudo apt-get install python2.7
sudo apt-get install python-pip
```
2. prepare /stanford-corenlp-full-2017-06-09 folder
```bash
wget http://nlp.stanford.edu/software/stanford-corenlp-full-2017-06-09.zip
unzip stanford-corenlp-full-2017-06-09.zip 
```
3. set program environment
```bash
git clone https://github.com/vibrioh/iterative_set_expansion.git
cd iterative_set_expansion
sudo pip install --upgrade BeautifulSoup4
sudo pip install --upgrade google-api-python-client
mv -v ~/stanford-corenlp-full-2017-06-09 ~/iterative_set_expansion/
```
### Run
Please run with *python2.7.14*, when using *python2.7.10* will cause catching the exception as "<urlopen error [SSL: TLSV1_ALERT_PROTOCOL_VERSION] tlsv1 alert protocol version (_ssl.c:590)>." for some URLs (such as: https://www.biography.com/people/bill-gates-9307520).
```bash
python iterative_set_expansion.py <google api key> <google engine id> <r> <t> <q> <k>
```
for instance
```bash
python iterative_set_expansion.py AIzaSyA_h1kXl0JIC4d2RAkeq-VRWMTbVOijrwA 015239954879085458485:jvjbixbxjiu 4 0.35 "bill gates microsoft" 10
```

## Internal Design
1. The target relations result set is initialized as a dictionary for convenience, intended to use an ordered tuple of query terms as key, the confidence as value.
2. Get 10 URLs through Google Custom Search Engine as project 1.
3. If not the first iteration, get rid of the replicates. Then for each remained URL, get all possible relations regardless of confidences. This is the main function in the whole program, the details will talk in content below.
4. Prune the X with confidence values lower than k.
5. If pruned X contains no less than k results, stop loop and return the results. 
6. Otherwise, take the tuple with highest confidence and check keywords: if one tuple's keywords are not all in the used keywords set, then used as new tuple for another iteration of expansion, otherwise return with results and stop.

## Step 3 Description
1. In the function `get_text(url)` , for each url, we use urllib2 to get web page content, catch exception then return a list of empty string.
2. If the url retrieval is successful in `get_text(url)`, we use `BeautifulSoup` to extract `HTML` contents, get rid of irrelevant text such as `scripts` or `css` styles. Then we combine the remain content to a text by stripping the white space. In the meanwhile, we found there are some length of the "words" are extremely long, so we set a cutoff of 23 letters to exclude such non-sense "words".
3. Two-step annotation:
* First step `annotate(text, properties_step)` takes the orgin plain text, and the properties_step argument = 1 indicates that that annotators are *"tokenize,ssplit,pos,lemma,ner"*. This will return an annotated document.
* Then the `senteces_filter(doc)` will be invoked to get rid of impossible sentences for relation extraction. For the time-efficiency trade-off, we first cut off sentences longer than 50. Then delete the sentences that don't contain entities for the required relation. At the end return the filtered sentences list.
* The second step, `annotate(text, properties_step)` takes the filtered sentences. By indicating the properties_step argument = 2, we are now using the annotators *"tokenize,ssplit,pos,lemma,ner,parse,relation"*. By this round, the relations are embedded within annotated document.
4. Then `extract_r(sentence, X)` is used to extract relations. The valid relations are those with the right entities and the confidences are the highest among all other relations in the same parse tree. Because we use dictionary to store tuples, so it is easy to check the duplicates for both keys and values. These relations are all added to X as long as they are not identical to the previous. And after one iteration, they will be further pruned by prerequisite confidence.
