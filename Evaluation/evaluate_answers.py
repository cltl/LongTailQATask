#!/usr/bin/env python3
import math
import sys
from pprint import pprint
import json

import config

metrics=config.metrics
expected=config.expected

def extract_data(data, gold=True):
    qs=set(data.keys())
    docs={}
    incidents={}
    for q in data:
        if gold:
            docs[q]=set(doc for inc_id in data[q]["answer_docs"] for doc in data[q]["answer_docs"][inc_id])
        else: # system's format is simpler
            docs[q]=set(data[q]["answer_docs"])
        incidents[q]=data[q]["numerical_answer"]
    return docs, incidents, qs

"""
def extract_docs(mydir):
    docs={}
    incidents={}
    qs=set()
    for fn in glob('%s*.conll' % mydir):
        q=fn.split('/')[-1].split('.')[0]
        docs[q]=set()
        incs=set()
        current_doc=""
        with open(fn, 'r') as f:
            for line in f:
                line=line.strip('\n')
                if not line: continue
                elements = line.split('\t')
                if line.startswith('#begin'):
                    current_doc=line.split()[-1].lstrip('(').rstrip(');')
                elif not line.startswith('#end') and len(elements)==4 and elements[3]!='-':
                    docs[q].add(current_doc)
                    incs.add(elements[3])
        incidents[q]=len(incs)
        qs.add(q)
    return docs, incidents, qs
"""

def accuracy_evaluation(sys_incidents, gold_incidents, questions):
    correct=0
    for k in sys_incidents:
        if gold_incidents[k]==sys_incidents[k]:
            correct+=1
    return correct/len(questions)

def rmse_evaluation(sys_incidents, gold_incidents, questions):
    sum_diffs=0.0
    for k in sys_incidents:
        diff=gold_incidents[k]-sys_incidents[k]
        diff_sq = diff * diff
        sum_diffs+=diff_sq

    div=sum_diffs/len(questions)
    return math.sqrt(div)

def document_evaluation(sys_documents, gold_documents, questions):

    f1={}
    p={}
    r={}

    for q in questions:
        tp = len(sys_docs[q] & gold_docs[q])
        fp = len(sys_docs[q] - gold_docs[q])
        fn = len(gold_docs[q] - sys_docs[q])

        if tp+fp+fn>0:
            p[q] = tp/(fp + tp)
            r[q] = tp/(fn + tp)
            f1[q] = 2*p[q]*r[q]/(p[q]+r[q])
        else:
            p[q]=1.0
            r[q]=1.0
            f1[q]=1.0

    return p, r, f1

def compute_avg(v):
    return sum(v.values())/len(v)

def feq(a,b):
    if abs(a-b)<0.000001:
        return 1
    else:
        return 0

if __name__=="__main__":
    sysjson=sys.argv[1]
    goldjson=sys.argv[2]
    scoresjson=sys.argv[3]

    with open(sysjson, 'r') as datafile:
        sysdata=json.load(datafile)
        
    with open(goldjson, 'r') as datafile:
        golddata=json.load(datafile)

    TESTMODE=False
#    if datadir.strip('/')=="Test":
#        TESTMODE=True
#        print("Running in Test Mode: All scores will be checked against the expected ones.")

    scores={}

    gold_docs, gold_incidents, gold_qs = extract_data(golddata)
    sys_docs, sys_incidents, sys_qs = extract_data(sysdata, False)
    questions = gold_qs & sys_qs

    print("*** Document-level evaluation ***")

    p, r, f1 = document_evaluation(sys_docs, gold_docs, questions)
    scores['doc_p']=compute_avg(p)
    scores['doc_r']=compute_avg(r)
    scores['doc_f1']=compute_avg(f1)
    if TESTMODE:
        assert feq(scores['doc_p'],expected['doc_p']), "%f different than %f for the metric %s" % (scores['doc_p'], expected['doc_p'], 'Document-level precision')
        assert feq(scores['doc_r'],expected['doc_r']), "%f different than %f for the metric %s" % (scores['doc_r'], expected['doc_r'], 'Document-level recall')
        assert feq(scores['doc_f1'],expected['doc_f1']), "%f different than %f for the metric %s" % (scores['doc_f1'], expected['doc_f1'], 'Document-level F1-score')

    print("Precision per question", p)
    print("Average precision", scores['doc_p'])
    print("Recall per question", r)
    print("Average recall", scores['doc_r'])
    print("F1-score per question", f1)
    print("Average F1-score", scores['doc_f1'])

    print("*** Document-level evaluation done. ***")
    print()
    print("*** Incident-level evaluation ***")

    scores['inc_acc'] = accuracy_evaluation(sys_incidents, gold_incidents, questions)
    scores['inc_rmse'] = rmse_evaluation(sys_incidents, gold_incidents, questions)
    if TESTMODE:
        assert feq(scores['inc_acc'], expected['inc_acc']), "%f different than %f for the metric %s" % (scores['inc_acc'], expected['inc_acc'], 'Incident-level accuracy')
        assert feq(scores['inc_rmse'], expected['inc_rmse']), "%f different than %f for the metric %s" % (scores['inc_rmse'], expected['inc_rmse'], 'Incident-level RMSE')
    print("Accuracy over all questions:", scores['inc_acc'])
    print("RMSE over all questions:", scores['inc_rmse'])

    print("*** Incident-level evaluation done. ***")
    print()
    print("Answered questions: %d" % len(questions))
    print("Total questions: %d" % len(gold_qs))
    print()

    print()
    print("*** SUMMARY: ***")
    pprint(scores)
    print("*** Evaluation done. ***")
    print()

    with open(scoresjson, 'w') as outfile:
        json.dump(scores, outfile)
        print("*** Summary JSON stored in %s . ***" % scoresjson)
        print()
    if TESTMODE:
        print("ALL TESTS COMPLETED SUCCESSFULLY")
