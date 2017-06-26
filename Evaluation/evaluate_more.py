#!/usr/bin/env python3
import math
import sys

questions=5
metrics=['bcub', 'blanc', 'ceafe', 'ceafm', 'muc']

expected={'bcub_f1': 59.886667, 'blanc_f1': 56.603333, 'ceafe_f1': 59.838333, 'ceafm_f1': 59.886667, 'muc_f1': 59.003333, 'doc_p': 0.6689258325240012, 'doc_r': 0.8217613543955121, 'doc_f1': 0.6935945190468833, 'inc_acc': 0.60, 'inc_rmse': 28.0}

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
    return correct/questions

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

def feq(a,b):
    if abs(a-b)<0.000001:
        print('less')
        return 1
    else:
        print(abs(a-b))
        print('more')
        return 0

if __name__=="__main__":
    datadir=sys.argv[1]
    TESTMODE=False
    print(datadir)
    if datadir.strip('/')=="Test":
        TESTMODE=True
        print("Running in Test Mode: All scores will be checked against the expected ones.")
    sysdir = "%s/system/" % datadir
    golddir = "%s/gold/" % datadir
    scoresdir = "%s/scores/" % datadir

    ### Compute averages for all mention-level metrics ###

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

    gold_docs, gold_incidents = extract_docs(golddir)
    sys_docs, sys_incidents = extract_docs(sysdir)

    print("*** Document-level evaluation ***")

    p, r, f1 = document_evaluation(sys_docs, gold_docs)
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

    accuracy = accuracy_evaluation(sys_incidents, gold_incidents)
    rmse = rmse_evaluation(sys_incidents, gold_incidents)
    if TESTMODE:
        assert feq(accuracy, expected['inc_acc']), "%f different than %f for the metric %s" % (accuracy, expected['inc_acc'], 'Incident-level accuracy')
        assert feq(rmse, expected['inc_rmse']), "%f different than %f for the metric %s" % (rmse, expected['inc_rmse'], 'Incident-level RMSE')
    print("Accuracy over all questions:", accuracy)
    print("RMSE over all questions:", rmse)

    print("*** Incident-level evaluation done. ***")

    if TESTMODE:
        print("ALL TESTS COMPLETED SUCCESSFULLY")
