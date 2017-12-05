import json
import sys
from nltk.corpus import wordnet as wn
from datetime import datetime
from collections import OrderedDict


wn_synsets={'killing': {'killing.n.02', 'kill.v.01'}, 'injuring': {'injure.v.01', 'injured.a.01'}, 'fire_burning': {'fire.n.01'}, 'job_firing': {'displace.v.03'}} # the set of synsets that correspond to the question's event type, according to the task description
# Extract the values given for the event properties (time, location, participant) in the question, as keywords
def extract_keywords_and_time(qdata):
    keywords=set()
    time=None
    for a in ["location", "time", "participant"]:
        if a in qdata:
            raw_value=list(qdata[a].values())[0]
            if a=="time": #time is not a keyword but is processed differently
                time=qdata[a]
            elif a=="location": # locations are preprocessed to remove the root of the URI
                keywords.add(raw_value.split('/')[-1].replace('_', ' '))
            else:
                keywords.add(raw_value)
    return keywords, time

# Obtain the event lemmas based on the event type in the question. This is done by first mapping the event type to its synsets in WordNet, and then extracting the lemmas of those WordNet synsets
def get_event_lemmas(event_type):
    syns = set(wn_synsets[event_type])
    syns = [wn.synset(i) for i in syns]
    lemmas=set()
    for s in syns:
        lemmas |=set([l.replace('_', ' ') for l in s.lemma_names()])
    return lemmas

# Obtain event types that a lemma refers to
def get_et_for_lemmas(etypes={'killing', 'injuring'}):
    lemma2et={}
    for etype in etypes:
        lemmas=get_event_lemmas(etype)
        for lemma in lemmas:
            lemma2et[lemma]=etype
    return lemma2et


# check if the DCT fits the question time
def time_fits(dct, qtime):
    if qtime is None:
        return True
    dt = datetime.strptime(dct, '%Y-%m-%d')
    dct_day = dt.strftime("%d/%m/%Y")
    dct_month = dt.strftime("%m/%Y")
    dct_year = dt.strftime("%Y")
    
    for granularity in qtime:
        if granularity=='day':
            qdt=datetime.strptime(qtime[granularity], '%d/%m/%Y')
            qdt_day = qdt.strftime("%d/%m/%Y")
            return qdt_day==dct_day
        elif granularity=='month':
            qdt=datetime.strptime(qtime[granularity], '%m/%Y')
            qdt_month = qdt.strftime("%m/%Y")
            return qdt_month==dct_month
        elif granularity=='year':
            qdt=datetime.strptime(qtime[granularity], '%Y')
            qdt_year = qdt.strftime("%Y")
            return qdt_year==dct_year
        else:
            continue

# This is the main function for processing of a question
# For each document, we create its version as answer document and as noise document. When we get to its end (#end document), then we decide whether to append the noise or the answer document. We choose the answer document if all event property keywords are found and at least one f the event lemmas was found in the document text.
# For the subtask S1, we make sure that the document is one (if it is not, we don't answer the question). Here we assume that all mentions and their documents are correferential (because we know that the total number of answer incidents is 1).
# For the subtask S2, we assume that the answer mentions belonging to the same document are correferential, but the ones belonging to different documents are not.
def process_question(qdata, conll_data, answer_is_one=False):
    keywords, q_time=extract_keywords_and_time(qdata)
    event_type=qdata["event_type"]
    event_lemmas=get_event_lemmas(event_type)
    qdocs=qdata['input_doc_ids']

    #output=""
    answer_docs=set()

    for docid in qdocs:
        docdata=conll_data[docid]
        dct=docdata['dct']
        lines=docdata['content']

        tokens=[]
        for line in lines:
            token=line.split()[1]
            if token=='NEWLINE':
                token='\n'
            tokens.append(token)
        text=' '.join(tokens)

        if all(k in text for k in keywords) and any(t in tokens for t in event_lemmas) and time_fits(dct, q_time):
            answer_docs.add(docid)

    if answer_is_one: # s1
        if len(answer_docs):
            return answer_docs, 1
        else:
            return answer_docs, 0
    else: # s2 or s3$
        return answer_docs, len(answer_docs)

def mention_annotation(conll_data):
    lemma2et=get_et_for_lemmas()
    output_conll=""
    docnum=0
    for docid, docdata in conll_data.items():
        output_conll+= docdata['start_line']
        for line in docdata['content']:
            line=line.strip()
            tid, token, part, annotation = line.split('\t')
            if token in lemma2et:
                if lemma2et[token]=='killing':
                    annotation='20%d' % docnum
                else: # injuring
                    annotation='21%d' % docnum
            output_conll+='\t'.join([tid, token, part, annotation]) + '\n'
        output_conll+=docdata['end_line']
        docnum+=1

    return output_conll

def load_conll_data(file_location):
    conll_data=OrderedDict()
    with open(file_location, 'r') as f:
        #chain=1
        for line in f:
            if line.startswith('#begin'):
                docid=""
#                docid = line.lstrip("#begin document (").rstrip().rstrip("); ")
                list_of_lines=[]
                start_line=line
            elif line.startswith("#end"):
                end_line = line
                conll_data[docid]={
                    'dct': dct,
                    'content': list_of_lines,
                    'start_line': start_line,
                    'end_line': end_line
                }
            else:
                line_elements=line.split()
                token=line_elements[1]
                if docid=="":
                    docid=line_elements[0].split('.')[0]
                if line_elements[2]=='DCT':
                    start_line+=line
                    dct=token
                else: 
                    list_of_lines.append(line)
    return conll_data

def main(subtask):
    print("Subtask %s" % subtask)
    if len(sys.argv)<3:
        print("Please supply the input and the output folder as arguments")
        print("Example: python3 baseline1.py inputdir outputdir")
        sys.exit()
    input_dir = "%s/%s" % (sys.argv[1], subtask) # the directory of the input data
    output_dir = "%s/%s" % (sys.argv[2], subtask) # the directory of the output data
    with open('%s/questions.json' % input_dir, 'r') as f:
        questions = json.load(f)

    conll_data=load_conll_data("%s/docs.conll" % input_dir)

    conll_output = mention_annotation(conll_data)
    with open('%s/docs.conll' % output_dir, 'w') as outfile:
        outfile.write(conll_output)

    answers_json={}
    for q in questions:
        answer_docs, num_answer=process_question(questions[q], conll_data, subtask=="s1")
        if subtask=="s1" and num_answer!=1: continue # don't answer if the answer for s1 is incorrect
        answers_json[q]={"numerical_answer": num_answer, "answer_docs": list(answer_docs)}

    with open('%s/answers.json' % output_dir, 'w') as outjson:
        json.dump(answers_json, outjson, indent=4)


if __name__=="__main__":
    for subtask in ["s1", "s2"]:
        main(subtask)
