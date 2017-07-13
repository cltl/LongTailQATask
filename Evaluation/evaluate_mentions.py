#!/usr/bin/env python3
import math
import sys
from glob import glob
from pprint import pprint
import json

import config

metrics=config.metrics
expected=config.expected

def compute_mention_avg(scoresdir, metric):
    r,p,f1=0.0, 0.0, 0.0
    lc=0
    with open('%s%s_all.conll' % (scoresdir, metric)) as f:
        for line in f:
           #scores=[float(s.split()[-1]) for s in line.split('%') if s.strip()]
           scores=[float(s.split()[-1].strip('%')) for s in line.strip().split('\t') if s]
           r+=scores[0]
           p+=scores[1]
           f1+=scores[2]
           lc+=1

    print("*** Mention-annotated questions answered by the system: %d ***" % lc)
    return p/lc,r/lc,f1/lc 

def feq(a,b):
    if abs(a-b)<0.000001:
        return 1
    else:
        return 0

if __name__=="__main__":
    if len(sys.argv)!=4:
        sys.exit()
    sysdir=sys.argv[1]
    golddir=sys.argv[2]
    scoresdir=sys.argv[3]

    TESTMODE=False
#    if datadir.strip('/')=="Test":
#        TESTMODE=True
#        print("Running in Test Mode: All scores will be checked against the expected ones.")

    scores={}

    ### Compute averages for all mention-level metrics ###

    print()
    print("*** Mention-level evaluation ***")

    for metric in metrics:
        metric_r, metric_p, metric_f1 = compute_mention_avg(scoresdir, metric)
        print('METRIC %s: Precision = %f; Recall = %f; F1-score = %f' % (metric, metric_p, metric_r, metric_f1))
        k='men_%s_f1' % metric
        scores[k] = metric_f1
        if TESTMODE:
            assert feq(expected[k], metric_f1), "%f different than %f for the metric %s" % (metric_f1, expected[k], metric)
    print("*** Mention-level evaluation done. ***")
    print()
    ### Done. ###

    with open('%ssummary_men.json' % scoresdir, 'w') as outfile:
        json.dump(scores, outfile)
        print("*** Summary JSON stored in %ssummary_men.json . ***" % scoresdir)
        print()
    if TESTMODE:
        print("ALL MENTION-LEVEL TESTS COMPLETED SUCCESSFULLY")
