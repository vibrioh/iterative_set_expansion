# coding: utf-8


import os
import sys

reload(sys)
sys.setdefaultencoding("utf-8")
import urllib2
from bs4 import BeautifulSoup
from collections import defaultdict
from NLPCore import NLPCoreClient
from googleapiclient.discovery import build


# pre-defined args for test
# JSON_API_KEY, SEARCH_ENGINE_ID, r, t, q, k = "AIzaSyA_h1kXl0JIC4d2RAkeq-VRWMTbVOijrwA", "015239954879085458485:jvjbixbxjiu", 1, 0.3, "Tom Hanks Los Angeles",  10

def search(query_terms):
    '''
    Search by calling Google Custom Search API
    with input query terms.
    Return a list of (10) urls.
    '''
    # Call Google Custom Search API
    service = build("customsearch", "v1", developerKey=JSON_API_KEY)
    # query = ' '.join(query_terms)
    res = service.cse().list(q=query_terms, cx=SEARCH_ENGINE_ID).execute()

    # Parse returned query results
    urls = []
    for item in res['items']:
        # unicode to utf-8
        link = item['link'].encode('utf-8').strip()
        urls.append(link)
    return urls


def get_text(url):
    '''
    extract plain text from web page in given url
    :param url: str
    :return: a list of a str of the text
    '''
    f = ""
    try:
        f = urllib2.urlopen(url).read()
    except Exception as e:
        print "May not retrieve {}. \nException: {}.".format(url, e)
        return [""]
    soup = BeautifulSoup(f, "html.parser", from_encoding="utf-8")
    for script in soup(["script", "style", "sup"]):
        script.extract()
    text = soup.get_text()
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
    return [" ".join(chunk for chunk in chunks if (chunk and len(str(chunk)) < 23)) if text else ""]


def annotate(text, properties_step):
    '''
    use NLPcore to annotate text and extract relations
    :param text: list of sentences, a list of a str
    :param properties_step: 1 or 2, the first step or the second step
    :return: annotated document
    '''
    properties_1 = {
        "annotators": "tokenize,ssplit,pos,lemma,ner",
        "ner.useSUTime": "0"
    }

    properties_2 = {
        "annotators": "tokenize,ssplit,pos,lemma,ner,parse,relation",
        # Second pipeline; leave out parse,relation for first
        "parse.model": "edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz",
        # Must be present for the second pipeline!
        "ner.useSUTime": "0"
    }
    nlpcore_path = os.path.abspath("stanford-corenlp-full-2017-06-09")
    # nlpcore_path = "/Users/vibrioh/local_projects/stanford-corenlp-full-2017-06-09"

    clinet = NLPCoreClient(nlpcore_path)
    if properties_step == 1:
        pipeline = properties_1
    else:
        pipeline = properties_2
    doc = clinet.annotate(text, pipeline)

    return doc


def senteces_filter(doc):
    '''
    Live_In: people and location
    Located_In: two locations
    OrgBased_In: organization and location
    Work_For: organization and people

    :param doc: annotated document
    :return: list of filtered sentences
    '''
    filtered_sentences = []
    for sentence in doc.sentences:
        entities = defaultdict(int)
        tokens = sentence.tokens
        if len(tokens) > 50:
            continue
        for token in tokens:
            if token.ner != "O":
                entities[token.ner] += 1
        if r == 1 and "PERSON" in entities and "LOCATION" in entities:
            filtered_sentences.append([' '.join([token.word for token in tokens])])
        elif r == 2 and entities["LOCATION"] > 1:
            filtered_sentences.append([' '.join([token.word for token in tokens])])
        elif r == 3 and "ORGANIZATION" in entities and "LOCATION" in entities:
            filtered_sentences.append([' '.join([token.word for token in tokens])])
        elif r == 4 and "ORGANIZATION" in entities and "PERSON" in entities:
            filtered_sentences.append([' '.join([token.word for token in tokens])])
    return filtered_sentences


def extract_r(sentence, X):
    '''
    this is used to extract possible relations from the results from the second parsing
    reporting by printing out each found relation
    :param sentence: each sentence parsing document
    :param X: extracted relations dictionary
    :return: X, the dictionary
    '''
    for rel in sentence.relations:
        EntityType1 = rel.entities[0].type
        EntityType2 = rel.entities[1].type
        pros = rel.probabilities
        Confidence = float(pros[r_dict[r]])
        is_r = True
        if {EntityType1, EntityType2} != r_set[r]:
            continue
        for value in pros.values():
            if Confidence < float(value):
                is_r = False
                break
        if is_r:
            EntityValue1 = rel.entities[0].value
            EntityValue2 = rel.entities[1].value
            extracted = {EntityType1: EntityValue1, EntityType2: EntityValue2, "Confidence": Confidence}
            tuple_key = {(extracted[r_list[r][0]], extracted[r_list[r][1]]): Confidence}
            if (extracted[r_list[r][0]], extracted[r_list[r][1]]) in X:
                if X[(extracted[r_list[r][0]], extracted[r_list[r][1]])] < Confidence:
                    print "=============== EXTRACTED RELATION ==============="
                    str_sent = ' '.join([token.word for token in sentence.tokens])
                    str_sent = str_sent.replace("-LSB- ''", "").replace("-LSB- '", "").replace("-LSB- `", "").replace(
                        "'' -RSB-", "").replace("' -RSB-", "").replace("-LSB-", "").replace("-RSB-", "").replace(
                        "-LRB-", "").replace("-RRB-", "")
                    print "Sentence: " + str_sent
                    print "RelationType: {} | Confidence= {} | EntityType1= {} | EntityValue1= {} | EntityType2= {} | EntityValue2= {}".format(
                        r_dict[r], Confidence, EntityType1, EntityValue1, EntityType2, EntityValue2)
                    print "============== END OF RELATION DESC =============="
                    X[(extracted[r_list[r][0]], extracted[r_list[r][1]])] = Confidence
            else:
                X.update(tuple_key)
                print "=============== EXTRACTED RELATION ==============="
                str_sent = ' '.join([token.word for token in sentence.tokens])
                str_sent = str_sent.replace("-LSB- ''", "").replace("-LSB- '", "").replace("-LSB- `", "").replace(
                    "'' -RSB-", "").replace("' -RSB-", "").replace("-LSB-", "").replace("-RSB-", "").replace("-LRB-",
                                                                                                             "").replace(
                    "-RRB-", "")
                print "Sentence: " + str_sent
                print "RelationType: {} | Confidence= {} | EntityType1= {} | EntityValue1= {} | EntityType2= {} | EntityValue2= {}".format(
                    r_dict[r], Confidence, EntityType1, EntityValue1, EntityType2, EntityValue2)
                print "============== END OF RELATION DESC =============="
    return X


def expand(urls, X):
    '''
    main function in each iteration, for each url, extract all relations that required by arguments
    :param urls: list of urls
    :param X: the relation dictionary
    :return: X, the dictionary
    '''
    for url in urls:
        start_size = len(X)
        print "Processing: {}".format(url)
        text = get_text(url)
        ann_1 = annotate(text, 1)
        ann_1_filtered_sentences = senteces_filter(ann_1)
        for sentence in ann_1_filtered_sentences:
            ann_2 = annotate(sentence, 2)
            for sentence in ann_2.sentences:
                extract_r(sentence, X)
        print "Relations extracted from this website: {} (Overall: {})".format(len(X) - start_size, len(X))
    return X


def main():
    # Parse Arguments
    global JSON_API_KEY, SEARCH_ENGINE_ID, r_dict, r, r_set, r_list, t, origin_q, q, k
    JSON_API_KEY, SEARCH_ENGINE_ID, r, t, q, k = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], \
                                                 sys.argv[6]
    r_dict = {1: "Live_In", 2: "Located_In", 3: "OrgBased_In", 4: "Work_For"}
    r = int(r)
    r_set = {1: {"PEOPLE", "LOCATION"}, 2: {"LOCATION", "LOCATION"}, 3: {"ORGANIZATION", "LOCATION"},
             4: {"ORGANIZATION", "PEOPLE"}}
    r_list = {1: ["PEOPLE", "LOCATION"], 2: ["LOCATION", "LOCATION"], 3: ["ORGANIZATION", "LOCATION"],
              4: ["ORGANIZATION", "PEOPLE"]}
    t = float(t)
    origin_q = q
    k = int(k)
    it = 1
    X = {}
    print "Parameters:"
    print "Client key      = {}\nEngine key      = {}\nRelation        = {}\nThreshold       = {}\nQuery           = {}\n# of Tuples     = {}".format(
        JSON_API_KEY, SEARCH_ENGINE_ID, r_dict[r], t, origin_q, k)
    print "Loading necessary libraries; this will take a few seconds..."
    all_urls = set()
    not_yet_k = True
    all_q = set()
    # main loop: while not k or can not find more or more than 100 iterations just in case
    while not_yet_k:
        q_list = q.lower().strip('\n').split()
        for word in q_list:
            all_q.add(word)
        new_urls = search(q)
        urls = []
        for url in new_urls:
            if url not in all_urls:
                all_urls.add(url)
                urls.append(url)
        print "=========== Iteration: {} - Query: {} ===========".format(it, q)
        # the main function in the loop
        expand(urls, X)

        relations = []
        for key, value in sorted(X.iteritems(), key=lambda (k, v): (v, k), reverse=True):
            if value > t:
                relations.append([value, key[0], key[1]])
            else:
                del X[key]
        print "Pruning relations below threshold..."
        print "Number of tuples after pruning: {}".format(len(X))
        print "================== ALL RELATIONS ================="
        for relation in relations:
            print "Relation Type: {}\t| Confidence: {:0.3f}\t\t| Entity #1: {} ({}) \t\t\t| Entity #2: {} ({})".format(
                r, relation[0], relation[1], r_list[r][0], relation[2], r_list[r][1])
        if len(X) >= k:
            print "Program reached {} number of tuples. Shutting down...".format(k)
            not_yet_k = False
        elif it > 100:
            print "Maximum 100 iterations reached. Shutting down..."
            not_yet_k = False
        else:
            new_q = ""
            for key, value in sorted(X.iteritems(), key=lambda (k, v): (v, k), reverse=True):
                if key[0].lower() not in all_q and key[1].lower() not in all_q:
                    new_q = key[0] + " " + key[1]
                    all_q.add(key[0].lower())
                    all_q.add(key[0].lower())
                    break
            if new_q == "":
                not_yet_k = False
                print "ISE has 'stalled' before retrieving {} high-confidence tuples.".format(k)
            else:
                q = new_q
                it += 1
    return


if __name__ == '__main__':
    main()
