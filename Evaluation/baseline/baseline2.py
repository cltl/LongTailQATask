import json
import sys
from nltk.corpus import wordnet as wn
from datetime import datetime
from collections import OrderedDict
import os

wn_synsets={'killing': {'killing.n.02', 'kill.v.01'}, 'injuring': {'injure.v.01', 'injured.a.01'}, 'fire_burning': {'fire.n.01'}, 'job_firing': {'displace.v.03'}} # the set of synsets that correspond to the question's event type, according to the task description

def extract_keywords_and_time(qdata):
    """
    Extract the values given for the event properties (time, location, participant) in the question, as keywords.
    """
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

def get_event_lemmas(event_type):
    """
    Obtain the event lemmas based on the event type in the question. This is done by first mapping the event type to its synsets in WordNet, and then extracting the lemmas of those WordNet synsets.
    """
    syns = set(wn_synsets[event_type])
    syns = [wn.synset(i) for i in syns]
    lemmas=set()
    for s in syns:
        lemmas |=set([l.replace('_', ' ') for l in s.lemma_names()])
    return lemmas

def get_et_for_lemmas(etypes={'killing', 'injuring'}):
    """
    Obtain event types that a lemma refers to.
    """
    lemma2et={}
    for etype in etypes:
        lemmas=get_event_lemmas(etype)
        for lemma in lemmas:
            lemma2et[lemma]=etype
    return lemma2et


def time_fits(dct, qtime):
    """
    Check if the DCT fits the question time.
    """
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

def process_question(qdata, conll_data, answer_is_one=False):
    """
    Process a question and produce an answer (numerical answer and set of documents).
    A document belongs to the set of answer documents if: 1) its publishing time fits the question time; 2) all event property keywords from the question are found in the document text; and 3) at least one of the event lemmas was found in the document text.
    For the subtask S1, we make sure that the numeric answer is one (if it is not, we don't answer the question). We assume that all answer documents of S1 report on the same incident.
    For the subtask S2, we assume that each document reports on a different incident.
    """
    keywords, q_time=extract_keywords_and_time(qdata)
    event_type=qdata["event_type"]
    event_lemmas=get_event_lemmas(event_type)

    answer_docs=set()

    for docid, docdata in conll_data.items():
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
    """
    Annotate the data with mentions and produce the resulting CONLL string.
    We consider the event mentions belonging to the same document to be correferential, and the ones belonging to different documents non-coreferential.
    """
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
                    annotation='(20%d)' % docnum
                else: # injuring
                    annotation='(21%d)' % docnum
            output_conll+='\t'.join([tid, token, part, annotation]) + '\n'
        output_conll+=docdata['end_line']
        docnum+=1

    return output_conll

def load_conll_data(file_location):
    """
    Load the conll file data into a dictionary.
    """
    conll_data=OrderedDict()
    with open(file_location, 'r') as f:
        for line in f:
            if line.startswith('#begin'):
                docid=""
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
                if docid=="":
                    docid=line_elements[0].split('.')[0]
                if line_elements[2]=='DCT':
                    start_line+=line
                    dct=line_elements[1]
                else: 
                    list_of_lines.append(line)
    return conll_data

def main(subtask):
    """
    Main processing function for a subtask.
    """
    print("Subtask %s" % subtask)
    input_dir = "%s/%s" % (sys.argv[1], subtask) # the directory of the input data
    output_dir = "%s/%s" % (sys.argv[2], subtask) # the directory of the output data
    os.makedirs(output_dir, exist_ok=True)

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
    if len(sys.argv)<3:
        print("Please supply the input and the output folder as arguments")
        print("Example: python3 baseline1.py inputdir outputdir")
        sys.exit()

    for subtask in ["s1", "s2"]:
        main(subtask)
