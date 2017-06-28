#!/usr/bin/env python3
import math
import sys
from glob import glob

metrics=['bcub', 'blanc', 'ceafe', 'ceafm', 'muc']

expected={'bcub_f1': 39.830000, 'blanc_f1': 34.905000, 'ceafe_f1': 39.757500, 'ceafm_f1': 39.830000, 'muc_f1': 38.505000, 'doc_p': 0.5861572906550014, 'doc_r': 0.7772016929943902, 'doc_f1': 0.6169931488086041, 'inc_acc': 0.5, 'inc_rmse': 31.304951684997057}

def extract_docs(mydir):
    docs={}
    incidents={}
    qs=set()
    for fn in glob('%s*.conll' % mydir):
        q=int(fn.split('/')[-1].split('.')[0])
        docs[q]=set()
        incidents[q]=set()
        current_doc=""
        with open(fn, 'r') as f:
            for line in f:
                line=line.strip('\n')
                if not line: continue
                elements = line.split('\t')
                if line.startswith('#begin'):
                    current_doc=line.split()[-1]
                elif not line.startswith('#end') and len(elements)==3 and elements[2]!='-':
                    docs[q].add(current_doc)
                    incidents[q].add(elements[2])
        qs.add(q)
    return docs, incidents, qs

def accuracy_evaluation(sys_incidents, gold_incidents, questions):
    correct=0
    for k in sys_incidents:
        if len(gold_incidents[k])==len(sys_incidents[k]):
            correct+=1
    return correct/len(questions)

def rmse_evaluation(sys_incidents, gold_incidents, questions):
    sum_diffs=0.0
    for k in sys_incidents:
        diff=len(gold_incidents[k])-len(sys_incidents[k])
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

        p[q] = tp/(fp + tp)
        r[q] = tp/(fn + tp)
        f1[q] = 2*p[q]*r[q]/(p[q]+r[q])

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

def feq(a,b):
    if abs(a-b)<0.000001:
        return 1
    else:
        return 0

if __name__=="__main__":
    datadir=sys.argv[1]
    TESTMODE=False
    print('Data directory: %s' % datadir)
    if datadir.strip('/')=="Test":
        TESTMODE=True
        print("Running in Test Mode: All scores will be checked against the expected ones.")
    sysdir = "%s/system/" % datadir
    golddir = "%s/gold/" % datadir
    scoresdir = "%s/scores/" % datadir

    ### Compute averages for all mention-level metrics ###

    print()
    print("*** Mention-level evaluation ***")

    for metric in metrics:
        metric_r, metric_p, metric_f1 = compute_mention_avg(scoresdir, metric)
        print('METRIC %s: Precision = %f; Recall = %f; F1-score = %f' % (metric, metric_p, metric_r, metric_f1))
        if TESTMODE:
            k='%s_f1' % metric
            assert feq(expected[k], metric_f1), "%f different than %f for the metric %s" % (metric_f1, expected[k], metric)
    print("*** Mention-level evaluation done. ***")
    print()
    ### Done. ###

    gold_docs, gold_incidents, gold_qs = extract_docs(golddir)
    sys_docs, sys_incidents, sys_qs = extract_docs(sysdir)
    questions = gold_qs & sys_qs

    print("*** Document-level evaluation ***")

    p, r, f1 = document_evaluation(sys_docs, gold_docs, questions)
    avg_p=compute_avg(p)
    avg_r=compute_avg(r)
    avg_f1=compute_avg(f1)
    if TESTMODE:
        assert feq(avg_p,expected['doc_p']), "%f different than %f for the metric %s" % (avg_p, expected['doc_p'], 'Document-level precision')
        assert feq(avg_r,expected['doc_r']), "%f different than %f for the metric %s" % (avg_r, expected['doc_r'], 'Document-level recall')
        assert feq(avg_f1,expected['doc_f1']), "%f different than %f for the metric %s" % (avg_f1, expected['doc_f1'], 'Document-level F1-score')

    print("Precision per question", p)
    print("Average precision", avg_p)
    print("Recall per question", r)
    print("Average recall", avg_r)
    print("F1-score per question", f1)
    print("Average F1-score", avg_f1)

    print("*** Document-level evaluation done. ***")
    print()
    print("*** Incident-level evaluation ***")

    accuracy = accuracy_evaluation(sys_incidents, gold_incidents, questions)
    rmse = rmse_evaluation(sys_incidents, gold_incidents, questions)
    if TESTMODE:
        assert feq(accuracy, expected['inc_acc']), "%f different than %f for the metric %s" % (accuracy, expected['inc_acc'], 'Incident-level accuracy')
        assert feq(rmse, expected['inc_rmse']), "%f different than %f for the metric %s" % (rmse, expected['inc_rmse'], 'Incident-level RMSE')
    print("Accuracy over all questions:", accuracy)
    print("RMSE over all questions:", rmse)

    print("*** Incident-level evaluation done. ***")
    print()
    print("Answered questions: %d" % len(questions))
    print("Total questions: %d" % len(gold_qs))
    print()
    if TESTMODE:
        print("ALL TESTS COMPLETED SUCCESSFULLY")
