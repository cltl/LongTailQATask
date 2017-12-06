#!/usr/bin/env python
import sys
import os
import os.path
import json
import math
import subprocess
from glob import glob

# Extraction of data for both gold and system response
def extract_data(data, extract_incidents=True, gold=True):
    qs=set(data.keys())
    docs={}
    incidents={}
    for q in data:
        if gold:
            docs[q]=set(doc for inc_id in data[q]["answer_docs"] for doc in data[q]["answer_docs"][inc_id])
        elif "answer_docs" in data[q]: # system's format is simpler
            docs[q]=set(data[q]["answer_docs"])
        else: #if the question key exists but there are no documents specified, assume an empty set of docs
            info_print("You did not provide any documents for the question %s. Assuming your answer is an empty set." % q)
            docs[q]=set()
        if extract_incidents: # s2 or s3
            incidents[q]=data[q]["numerical_answer"]
        elif not gold and "answer_docs" in data[q]:
            info_print("You provided a numerical answer for the question %s. Note that subtask 1 does not ask for a numerical answer, since the answer is always 1!" % q)
    return docs, incidents, qs

# Evaluation f-ns
def accuracy_evaluation(sys_incidents, gold_incidents, questions):
    correct=0
    for k in sys_incidents:
        if gold_incidents[k]==sys_incidents[k]:
            correct+=1
    return correct*100.0/len(questions)

def rmse_evaluation(sys_incidents, gold_incidents, questions):
    sum_diffs=0.0
    for k in sys_incidents:
        diff=gold_incidents[k]-sys_incidents[k]
        diff_sq = diff * diff
        sum_diffs+=diff_sq

    div=sum_diffs*1.0/len(questions)
    return math.sqrt(div)

def document_evaluation(sys_documents, gold_documents, questions):

    f1={}
    p={}
    r={}

    for q in questions:
        tp = len(sys_docs[q] & gold_docs[q])*1.0
        fp = len(sys_docs[q] - gold_docs[q])*1.0
        fn = len(gold_docs[q] - sys_docs[q])*1.0

        if tp+fp+fn>0:
            if fp+tp>0.0:
                p[q] = tp/(fp + tp)
            else:
                p[q] = 0.0
            if fn + tp > 0.0:
                r[q] = tp/(fn + tp)
            else:
                r[q] = 0.0
            if p[q]+r[q]>0.0:
                f1[q] = 2*p[q]*r[q]/(p[q]+r[q])
            else:
                f1[q]=0.0
        else:
            p[q]=1.0
            r[q]=1.0
            f1[q]=1.0

    return p, r, f1

def filter_documents(path):
    new_path=path + ".filtered"
    skip=False
    with open(path, 'r') as infile:
        with open(new_path, 'w') as w:
            for line in infile:
                if not line.startswith('#'):
                    if not skip:
                        w.write(line)
                elif line.startswith('#begin document'):
                    doc_id = line[17:-3]
                    if doc_id in annotated_docs:
                        skip=False
                        w.write(line)
                    else:
                        skip=True
                elif line.startswith('#end document'):
                    if not skip:
                        w.write(line)
    return new_path

def mention_evaluation(syspath, goldpath, outdir, metrics, stask):
    if not os.path.exists(syspath):
        warn_print("None of the questions annotated with mentions in the gold data were annotated by this submission, for subtask %s." % stask)
        return 0.0
    for metric in metrics:
        outfile = '%s/%s.conll' % (outdir, metric)
        outfile_all = '%s/%s_all.conll' % (outdir, metric)
        cmds = [ 
            'perl %s/scorer.pl %s %s %s > %s' % (os.getcwd(), metric, goldpath, syspath, outfile),
            'tail -2 %s | head -1 >> %s' % (outfile, outfile_all)
        ]
        for cmd in cmds:
            subprocess.check_output(cmd, shell=True)
    avg=compute_mention_avg(outdir, metrics)
    info_print("S%s: Average coreference score over the %d metrics: %f" % (stask, len(metrics), avg))
    return avg

def compute_mention_avg(scoresdir, metrics):
    sum_score=0.0
    for metric in metrics:
        metric_r, metric_p, metric_f1 = obtain_metric_score(scoresdir, metric)
        sum_score += metric_f1
    return sum_score/len(metrics)

def obtain_metric_score(scoresdir, metric):
    scores_file = '%s/%s_all.conll' % (scoresdir, metric)
    if not os.path.exists(scores_file):
        return 0.0, 0.0, 0.0
    with open(scores_file) as f:
        line=f.readline()
        scores=[float(s.split()[-1].strip('%')) for s in line.strip().split('\t') if s]
        r=scores[0]
        p=scores[1]
        f1=scores[2]
        return p,r,f1

# Utils
def compute_avg(v):
    return sum(v.values())/len(v)

# Printing f-ns
def warn_print(m):
    print("WARN: %s\n" % m)
    return

def info_print(m):
    print("INFO: %s\n" % m)
    return

# as per the metadata file, input and output directories are the arguments
[_, input_dir, output_dir] = sys.argv

metrics=['bcub', 'blanc', 'ceafe', 'ceafm', 'muc']

annotated_docs = {'548f729263219a7b1d2423bdc586969b', 'ea781ee5a57a46b285d834708fee8c0d', '82a1900df6c3b3edb458ea8cfefe3c28', 'c229ce94825fb0d786f448454aaacc73', '440118a03d1f1acb04a69774e6070898', 'f642c7314e06cbbe4d2af32736a00f6d', '3ff14dbe98c6b7d81d908f118d5b75c7', '104db82506283933234d28c49929a9cc', '789d406fbcfd4834e83c047d1a2d655d', '6e7b16705f7de357a2d8313fee0fb72e', '4dc1a52e0e239fd4c96b2d6c08aea9a8', '30883b6ba9273903b93665469350f5f4', '34d13cc0d1db9d8b1a1139aea267826e', 'b02abc23b6f041f41344a0866c6a5d41', '4830fd0aa85c44dac4858a2220733f19', 'c7903fc30c417b3fc97b403619a81fa0', 'd168a447e1cacd6bb64020fd6aa7a09c', '19647c86f3ed1ad94cf6d5b6c3419f5d', 'd1c2083ddb50d4652df34568ad9bb4b6', '841a827f1a6fcb09b4f9c8080d0d1ffa', '084c085e6a47379426a977496ac576c9', '017920da87a5daacd48a426e48aed61e', 'b654dd9c20db958f7cba3b6cff58b7b2', '6c9fa7f335e78ca818125c626d3bc216', 'b5e597eb2b3d8f49b8de2b8d59a4a3fd', '712b5b916c552aeba096516eeee04e46', 'f016114ddb55b3f5c16fea2f8d1f2ec7', '9ff9d0e5bdb9675af4e6e062d21496bb', 'f5e081d0b616c05ba2c77dcc84df443a', '1cc16fb2501c720b7ec248dc48607dc9', '0541fb1b283a2cb0d7d9a1c328ce4635', '1e5419ea2d9cb57b163788a3e4568300', '533dc1a9518e4defd149a1e1c2a40766', '268559a68e96ad450222fc1f3bbbb987', 'bd7e9749d876981b5c1af7b914dbae1d', '5ae549c18a8c71ca742beafb2e14a883', '8cafcf95303727d6460e652787cabb84', 'dfa5ecd718ee3b8158e8ca38dcaa4a2c', '1a45d73a21522536c411807219ed553e', 'e186beddd0f3ffe371d8cb36702be2f7', 'e3a837843344e14130937be552c8d9bf', '748f14771b3febdc874b7827d151b6e0', 'abc4c58e9b7621b10a4732a98dc273b3'}

if __name__=="__main__":
    submission_dir = os.path.join(input_dir, 'res')
    gold_dir = os.path.join(input_dir, 'ref')

    if not os.path.isdir(submission_dir):
        sys.exit("ERROR: The submission directory was not found!")

    if not os.path.isdir(os.path.join(submission_dir, 's1')) and not os.path.isdir(os.path.join(submission_dir, 's2')) and not os.path.isdir(os.path.join(submission_dir, 's3')):
        sys.exit("ERROR: None of the task directories 's1', 's2', 's3' were found!")

    scores={"1":{}, "2":{}, "3":{}}
    for subtask in scores.keys():
        file_name = 'answers.json'
        subtask_submission_dir=os.path.join(submission_dir, 's%s' % subtask)
        subtask_gold_dir=os.path.join(gold_dir, 's%s' % subtask)
        scores[subtask]={'acc': 0.0, 'rmse': 0.0, 'f1': 0.0, 'avg': 0.0, 'answered': 0.0}
        if not os.path.exists(subtask_gold_dir) or not os.path.exists(subtask_submission_dir):
            warn_print("Subtask %s can not be evaluated on any level. \nREASON: The Submission directory s%s is missing." % (subtask, subtask))
            continue
        submission_path = os.path.join(subtask_submission_dir, file_name)
        gold_path = os.path.join(subtask_gold_dir, file_name)
        if os.path.exists(submission_path):
            with open(submission_path, 'r') as submission_file:
                sysdata = json.load(submission_file)
            with open(gold_path) as truth_file:
                golddata = json.load(truth_file)

            gold_docs, gold_incidents, gold_qs = extract_data(golddata, subtask!="1")
            sys_docs, sys_incidents, sys_qs = extract_data(sysdata, subtask!="1", False)
            questions = gold_qs & sys_qs

            for weird_q in sys_qs - gold_qs: # questions that only exist in the system JSON -> these should not occur, so this loop should be empty.
                info_print("The question with ID %s was answered by your system but is does not exist in the gold data." % weird_q)

            scores[subtask]["answered"]=len(questions)*100.0/len(gold_qs)

            # Document-level evaluation
            p, r, f1 = document_evaluation(sys_docs, gold_docs, questions)
            avg_p=compute_avg(p)
            avg_r=compute_avg(r)
            avg_f1=compute_avg(f1)
            scores[subtask]['f1']=100.0*avg_f1

            # Incident-level evaluation
            if subtask!="1":
                inc_acc = accuracy_evaluation(sys_incidents, gold_incidents, questions)
                inc_rmse = rmse_evaluation(sys_incidents, gold_incidents, questions)
                scores[subtask]['acc'] = inc_acc
                scores[subtask]['rmse'] = inc_rmse
        else: # answers.json is missing -> skip document and incident level
            message = "Subtask {2} not evaluated for incident and document level. \nREASON: Submission file '{0}' not found in the directory {1}"
            warn_print(message.format(file_name, subtask, subtask))

        # mention-level evaluation
        conll_subtask_submission_path = os.path.join(subtask_submission_dir, 'docs.conll')
        conll_subtask_gold_path = os.path.join(subtask_gold_dir, 'docs.conll')
        if os.path.exists(conll_subtask_submission_path):
            subtask_output_dir=os.path.join(output_dir, 's%s' % subtask)
            if not os.path.isdir(subtask_output_dir):
                os.mkdir(subtask_output_dir)
            else:
                cmd='rm %s/*' % subtask_output_dir
            filtered_gold_path = filter_documents(conll_subtask_gold_path)
            filtered_submission_path = filter_documents(conll_subtask_submission_path)
            avg=mention_evaluation(filtered_submission_path, filtered_gold_path, subtask_output_dir, metrics, subtask)
            scores[subtask]['avg']=avg
        else:
            warn_print("CoNLL file with annotations not found for subtask %s. Mention-level evaluation can not be performed." % subtask)

# the scores for the leaderboard must be in a file named "scores.txt"
# https://github.com/codalab/codalab-competitions/wiki/User_Building-a-Scoring-Program-for-a-Competition#directory-structure-for-submissions
    with open(os.path.join(output_dir, 'scores.txt'), 'w') as output_file:
        output_msg="s1_doc_f1:{0}\ns1_men_coref_avg:{1}\ns1_answered:{2}\ns2_inc_accuracy:{3}\ns2_inc_rmse:{4}\ns2_doc_f1:{5}\ns2_men_coref_avg:{6}\ns2_answered:{7}\ns3_inc_accuracy:{8}\ns3_inc_rmse:{9}\ns3_doc_f1:{10}\ns3_men_coref_avg:{11}\ns3_answered:{12}"
        output_file.write(output_msg.format(scores["1"]["f1"], scores["1"]["avg"], scores["1"]["answered"], scores["2"]["acc"],scores["2"]["rmse"], scores["2"]["f1"], scores["2"]["avg"], scores["2"]["answered"], scores["3"]["acc"], scores["3"]["rmse"], scores["3"]["f1"], scores["3"]["avg"], scores["3"]["answered"]))
