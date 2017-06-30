import json
import sys

from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer

lmtzr = WordNetLemmatizer()

wn_synsets={'killing': {'killing.n.02', 'kill.v.01'}, 'injuring': {'injured.a.01'}, 'fire_burning': {'fire.n.01'}, 'job_firing': {'displace.v.03'}}

def extract_keywords(qdata):
    keywords=set()
    for a in ["location", "time", "participant"]:
        if a in qdata:
            if a=="location":
                keywords.add(qdata[a][0].split('/')[-1].replace('_', ' '))
            else:
                keywords.add(qdata[a][0])
    return keywords

def get_event_lemmas(event_types):
    syns=set()
    for et in event_types:
        syns |= wn_synsets[et]
    print(syns)
    syns = [wn.synset(i) for i in syns]
    lemmas=set()
    for s in syns:
        lemmas |=set([l.replace('_', ' ') for l in s.lemma_names()]) 
    print(lemmas)
    return lemmas

def process_question(qdata, infile):
    keywords=extract_keywords(qdata)
    event_types=qdata["event_types"]
    event_lemmas=get_event_lemmas(event_types)

    output=""
    with open(infile, 'r') as f:
        chain=1
        for line in f:
            if line.startswith('#begin'):
                doc="" 
                doc_arr=[]
                answer_doc=""
                noise_doc=""
            elif line.startswith("#end"):
                doc=" ".join(doc_arr)
                doc=doc.replace("NEWLINE", "\n")
                if all(k in doc for k in keywords) and any(t in doc for t in event_types):
                    output+=answer_doc
                    chain+=1
                else:
                    output+=noise_doc
            else:      
                token=line.split()[1]
                doc_arr.append(token)
                
            noise_doc+=line
            token=line.split()[1]
            if token in event_types:
                new_line=line.split()
                new_line[3]=new_line[3].replace('-','(%d)\n' % chain)
                answer_doc+='\t'.join(new_line)
            else:

                answer_doc+=line
    if chain>1:
        return output
    else:
        return ""

if __name__=="__main__":
    input_dir = "../Data/system_input"
    output_dir = "../Data/system_output"
    with open('../Data/questions.json', 'r') as f:
        questions = json.load(f)

    for q in questions:
        fn='%s/%s.conll' % (input_dir, q)
        response=process_question(questions[q], fn)
        if response!="":
            with open('%s/%s.conll' % (output_dir, q), 'w') as outfile:
                outfile.write(response)
