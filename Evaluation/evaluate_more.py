#!/usr/bin/env python3
import math
import sys

questions=5
metrics=['bcub', 'blanc', 'ceafe', 'ceafm', 'muc']

def extract_docs(mydir):
    q=1
    docs={}
    incidents={}
    while q<=questions:
        docs[q]=set()
        incidents[q]=set()
        current_doc=""
        with open('%s%d.conll' % (mydir, q)) as f:
            for line in f:
                line=line.strip('\n')
                if not line: continue
                elements = line.split('\t')
                if line.startswith('#begin'):
                    current_doc=line.split()[-1]
                elif not line.startswith('#end') and len(elements)==3 and elements[2]!='-':
                    docs[q].add(current_doc)
                    incidents[q].add(elements[2])
        q+=1
    return docs, incidents

def accuracy_evaluation(sys_incidents, gold_incidents):
    correct=0
    for k in gold_incidents:
        if len(gold_incidents[k])==len(sys_incidents[k]):
            correct+=1
    return correct*100.0/questions

def rmse_evaluation(sys_incidents, gold_incidents):
    sum_diffs=0.0
    for k in gold_incidents:
        diff=len(gold_incidents[k])-len(sys_incidents[k])
        diff_sq = diff * diff
        sum_diffs+=diff_sq

    div=sum_diffs/questions
    return math.sqrt(div)

def document_evaluation(sys_documents, gold_documents):

    f1={}
    p={}
    r={}

    q=1
    while q<=questions:
        tp = len(sys_docs[q] & gold_docs[q])
        fp = len(sys_docs[q] - gold_docs[q])
        fn = len(gold_docs[q] - sys_docs[q])

        p[q] = tp/(fp + tp)
        r[q] = tp/(fn + tp)
        f1[q] = 2*p[q]*r[q]/(p[q]+r[q])

        q+=1

    return p, r, f1

def compute_avg(v):
    return sum(v.values())/len(v)

def compute_mention_avg(scoresdir, metric):
    r,p,f1=0.0, 0.0, 0.0
    lc=0
    with open('%s%s_all.conll' % (scoresdir, metric)) as f:
        for line in f:
           scores=[float(s.split()[-1]) for s in line.split('%') if s.strip()]
           r+=scores[0]
           p+=scores[1]
           f1+=scores[2]
           lc+=1
    return p/lc,r/lc,f1/lc 

if __name__=="__main__":
    datadir=sys.argv[1]
    sysdir = "%s/system/" % datadir
    golddir = "%s/gold/" % datadir
    scoresdir = "%s/scores/" % datadir

    ### Compute averages for all mention-level metrics ###

    print("*** Mention-level evaluation ***")

    for metric in metrics:
        metric_r, metric_p, metric_f1 = compute_mention_avg(scoresdir, metric)
        print('METRIC %s: Precision = %f; Recall = %f; F1-score = %f' % (metric, metric_p, metric_r, metric_f1))

    print("*** Mention-level evaluation done. ***")
    print()
    ### Done. ###

    gold_docs, gold_incidents = extract_docs(golddir)
    sys_docs, sys_incidents = extract_docs(sysdir)

    print("*** Document-level evaluation ***")

    p, r, f1 = document_evaluation(sys_docs, gold_docs)

    print("Precision per question", p)
    print("Average precision", compute_avg(p))
    print("Recall per question", r)
    print("Average recall", compute_avg(r))
    print("F1-score per question", f1)
    print("Average F1-score", compute_avg(f1))

    print("*** Document-level evaluation done. ***")
    print()
    print("*** Incident-level evaluation ***")

    accuracy = accuracy_evaluation(sys_incidents, gold_incidents)
    rmse = rmse_evaluation(sys_incidents, gold_incidents)
    print("Accuracy over all questions:", accuracy)
    print("RMSE over all questions:", rmse)

    print("*** Incident-level evaluation done. ***")
