from copy import deepcopy
import argparse
import subprocess
import json
from glob import glob
import pickle
import os
from random import shuffle, choice
import sys
from shutil import copyfile
import hashlib
from datetime import datetime
import pandas as pd
import operator
from collections import defaultdict

def load_next_q_ids(all_candidates, num_extra=1000):
    """
    """
    subtask2q_ids = {'1': {'existing': [], 'options': []},
                     '2': {'existing': [], 'options': []},
                     '3': {'existing': [], 'options': []},
                     }
    for a_candidate in all_candidates:
        subtask, q_id = a_candidate.q_id.split('-')
        subtask2q_ids[subtask]['existing'].append(int(q_id))


    for subtask, subtask_info in subtask2q_ids.items():

        if not subtask_info['existing']:
            continue

        highest_q_id = sorted(subtask_info['existing'])[-1]
        for potential_q_id in range(1, sorted(subtask_info['existing'])[-1]):
            if potential_q_id not in subtask_info['existing']:
                subtask2q_ids[subtask]['options'].append('%s-%s' % (subtask, potential_q_id))

        for potential_q_id in range(highest_q_id + 1, highest_q_id + num_extra):
                        subtask2q_ids[subtask]['options'].append('%s-%s' % (subtask, potential_q_id))

    return subtask2q_ids

def next_q_id_v2(subtask2q_ids, subtask):
    print(subtask2q_ids)
    print(subtask2q_ids.keys())
    next_id = subtask2q_ids[subtask]['options'].pop()
    return next_id

def hash_hash(u):
    hash_obj = hashlib.md5(source_url.encode())
    the_hash = hash_obj.hexdigest()
    return the_hash

def one_to_three(all_data):
    divided_data={"1":{}, "2":{}, "3":{}}
    for k in all_data:
        subtask=k[0]
        divided_data[subtask][k]=all_data[k]
    return divided_data

def get_next_s2_id(qid_location):
    with open(qid_location, 'r') as qid_file:
        q_ids=json.load(qid_file)
        return q_ids["2"]+1

def same_answer(a1, a2):
    return all([a1['numerical_answer']==a2['numerical_answer'], a1['answer_docs'].keys()==a2['answer_docs'].keys()])

def deduplicate(cands):
    for c1 in cands:
        if not c1.to_include_in_task:
            continue
        for c2 in cands:
            if c1.q_id==c2.q_id:
                continue
            if c2.to_include_in_task and same_answer(c1.answer_info, c2.answer_info):
                if c1.get_question_score() > c2.get_question_score():
                    c2.to_include_in_task = False
                elif c2.get_question_score() > c1.get_question_score():
                    c1.to_include_in_task = False
                else:
                    c2.to_include_in_task = False # same score -> choose c1

    return cands

def fr_time_key(incident_date):
    """
    convert incident_date to dict (dt_day, dt_month, dt_year)
    """
    dt = datetime.strptime(incident_date, '%B %d, %Y')
    dt_day = dt.strftime("%d/%m/%Y")
    dt_month = dt.strftime("%m/%Y")
    dt_year = dt.strftime("%Y")

    time_dict = {
        'dt_day': dt_day,
        'dt_month': dt_month,
        'dt_year': dt_year
    }

    return time_dict

def find_in_frames(location, l_gran, time, t_gran, evtype):
    if evtype=='fire_burning':
        df=fr
    elif evtype=='job_firing':
        df=bu
    else:
        df=gva
    for index, row in df.iterrows():
        row_date=row['date']
        row_loc=row['locations']
        if not row_date or not row_loc:
            continue
        if evtype in {'killing', 'injuring'}: #gva
            row_date=fr_time_key(row_date)

        if t_gran not in row_date or l_gran not in row_loc:
            continue

        if row_date[t_gran]==time and row_loc[l_gran]==location:
            return True
    return False

def pick_and_shuffle(g, data, how_many=50):
    to_return=set()
    print(len(data))
    for i in range(how_many):
        x=data.pop()
        y=data.pop()
        z=data.pop()
        new_q=(x[0], y[1], z[2])
        print(new_q)
        if new_q in data:
            print('found in questions')
        else:
            if not find_in_frames(new_q[0], g[0], new_q[1], 'dt_' + g[1], new_q[2]):
                print('not found in frames')
                to_return.add(new_q)
            else:
                print('found in frames')
    return to_return

def create_zero_questions(all_candidates, how_many=25):
    qpairs=defaultdict(set)
    location2q=defaultdict(set)
    to_store=defaultdict(set)

    for c in all_candidates:
        if c.to_include_in_task:

            if c.time_confusion and c.location_confusion:
                pair=(c.question()['location'][c.granularity[0]], c.sf[1], c.event_types[0])
                qpairs[c.granularity].add(pair)
                location2q[pair[0]].add(c)
    len_r=0
    for granularity in qpairs.keys():
        print()
        print(granularity)
        print()
        r=pick_and_shuffle(granularity, qpairs[granularity], how_many=how_many)
        to_store[granularity]=r
        print(len(r))
        len_r+=len(r)
    print(len_r)

    return to_store, location2q

def compute_avg_confusion_advanced(candidates):
    total_inc_conf=0
    total_doc_conf=0
    included=0
    for c in candidates:
        if c.to_include_in_task:
            for index, c_row in c.confusion_df.iterrows():
                row_docs=0
                for source_url in c_row['incident_sources']:
                    if source_url in doc_id2conll:
                        row_docs+=1
                if row_docs>0:
                    total_inc_conf+=1
                    total_doc_conf+=row_docs
            included+=1
    print('Average document confusion per question', total_doc_conf/included)
    print('Average incident confusion per question', total_inc_conf/included)

def get_top_n_locations(all_candidates, n=10):
    
    locs = defaultdict(int)
    for c in all_candidates:
        if c.to_include_in_task and c.gold_loc_meaning:
            locs[c.gold_loc_meaning]+=1

    sorted_locs=sorted(locs.items(), key=operator.itemgetter(1), reverse=True)
    
    to_return=set()
    for i in range(n):
        to_return.add(sorted_locs[i][0])
    return to_return

def combos_to_remove(all_candidates, to_include):

    d=defaultdict(int)
    for c in all_candidates:
        if c.to_include_in_task:
            d[c.granularity]+=1
    to_remove_combos=[]
    for k, v in d.items():
        if v>to_include*1.5/len(d):
            to_remove_combos.append(k)
            
    return d, to_remove_combos

# load frames
gva=pd.read_pickle('../EventRegistries/GunViolenceArchive/frames/all')
bu=pd.read_pickle('../EventRegistries/BusinessNews/business.pickle')
fr=pd.read_pickle('../EventRegistries/FireRescue1/firerescue_v3.pickle')

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Create participant data for SemEval-2018 task 5')
    parser.add_argument('-d', dest='input_folder', required=True, help='all .bin files in this folder will be considered')
    parser.add_argument('-o', dest='output_folder', required=True, help='folder output will be stored')
    args = parser.parse_args()

   # enrichment parameters for S2
    num_ones=10 # number of questions to move from s1 to s2

    copied_cnt=0

    qid_location="%s/q_id.json" % args.input_folder
    next_id=get_next_s2_id(qid_location)

    # bash commands
    bash_commands = ['rm -rf %s' % args.output_folder,
                     'mkdir -p %s/system_input' % args.output_folder,
                     'mkdir -p %s/system_output' % args.output_folder,
                     'cp ../Installing/setup.sh %s' % args.output_folder]

    for bash_command in bash_commands:
        output = subprocess.check_output(bash_command, shell=True)

    # load all candidates
    all_candidates = set()
    for bin_path in glob(args.input_folder + '/*.bin'):
        print("Reading %s" % bin_path)
        candidates = pickle.load(open(bin_path, 'rb'))
        all_candidates.update(candidates)

    print(len(all_candidates))

    # load tokenization
    path_cache_tokenization = '%s/cache' % args.input_folder
    with open(path_cache_tokenization, 'rb') as infile:
        doc_id2conll, df = pickle.load(infile)


    # convert trial data
    questions = dict()
    answers = dict()

    for candidate in all_candidates:

        types_and_rows = []
        dfs = [('gold', candidate.answer_df),
               ('confusion', candidate.confusion_df)]
        for a_type, a_df in dfs:
            for index, row in a_df.iterrows():
                types_and_rows.append((a_type, row))
        shuffle(types_and_rows)

        # create answer (and validate)
        candidate.generate_answer_info(types_and_rows, doc_id2conll, debug=False)

        #print(candidate.question())
        #print(candidate.answer_info)
        #input('continue?')

    print("now deduplicating. Number of questions before deduplication:")
    print(sum(candidate.to_include_in_task
              for candidate in all_candidates))
    all_candidates=deduplicate(all_candidates)
    print('Number of questions after deduplicating:')
    print(sum(candidate.to_include_in_task
              for candidate in all_candidates))
#    new_candidates=candidates


    top_n=get_top_n_locations(all_candidates, n=20)
    to_include=sum(candidate.to_include_in_task
              for candidate in all_candidates)
    gran_counts, gran_to_remove=combos_to_remove(all_candidates, to_include)

    print('Before removing boring questions:')
    print(gran_counts)
    to_remove=defaultdict(int)
    for c in all_candidates:
        if c.to_include_in_task and 'fire_burning' not in c.event_types and 'job_firing' not in c.event_types:
            if c.gold_loc_meaning in top_n and c.granularity in gran_to_remove:
                if gran_counts[c.granularity]-to_remove[c.granularity]>to_include*1.5/len(gran_counts):
                    to_remove[c.granularity]+=1
                    c.to_include_in_task=False

    print('We removed:')
    print(to_remove)

    print('After removing %d boring questions:' % sum(to_remove.values()))
    for g in gran_counts:
        print(g, gran_counts[g]-to_remove[g])

    # load potential q_ids for zero answer questions
    subtask2q_ids = load_next_q_ids(all_candidates)
    print('is 2 a key in subtask2q_ids', '2' in subtask2q_ids)

    print('Creating zero-answer questions')

    to_store, location2q=create_zero_questions(all_candidates, how_many=50)

    zero_added=0
    q_ids=set()
    for granularity, all_qs in to_store.items():
        for components in all_qs:
            location=components[0]
            if location2q[location]:
                old_q=location2q[location].pop()
                new_q=deepcopy(old_q)

                if not len(subtask2q_ids['2']['options']) and not len(subtask2q_ids['3']['options']):
                    break

                if (zero_added%2==0 or components[2]=='fire_burning') and len(subtask2q_ids['2']['options']):
                    subtask=2
                elif len(subtask2q_ids['3']['options']):
                    subtask=3
                else:
                    continue
                new_q.subtask=subtask
                print('zero question in subtask %d' % subtask) 
                next_id = subtask2q_ids[str(subtask)]['options'].pop()
                # next_id = next_q_id_v2(subtask2q_ids, str(subtask))
                print('id', next_id)
                new_q.q_id = next_id
                q_ids.add(next_id)
                new_q.answer_info['answer_docs']={}
                new_q.answer_info['numerical_answer']=0
                new_q.answer_incident_uris=set()
                new_q.ev_answer=0
                new_q.granularity=granularity
                new_q.event_types=[components[2]]
                new_q.sf=(new_q.sf[0], components[1])
                new_q.answer_df=pd.DataFrame()
                new_q.confusion_df=pd.DataFrame()

                questions[new_q.q_id] = new_q.question()
                answers[new_q.q_id] = new_q.answer_info
                zero_added+=1

    print('%d questions with answer zero added' % zero_added)
    print(q_ids)

    num_added = 0
    maximum = 100000
    debug = False
    all_docs=set() # we store all doc ids relevant for questions here
    for candidate in all_candidates:
        # update question and answer dictionaries
        if candidate.to_include_in_task:
            questions[candidate.q_id] = candidate.question()
            answers[candidate.q_id] = candidate.answer_info

            if debug:
                print(candidate.gold_loc_meaning)
                input('continue?')

            for a_type, a_row in candidate.types_and_rows:
                for source_url in a_row['incident_sources']:
                    if source_url not in doc_id2conll:
                        continue
                    else:
                        all_docs.add(source_url)

            ### Maybe copy the question to S2 ###
            if copied_cnt<num_ones and candidate.subtask==1:
                s1_qid=candidate.q_id
                new_candidate=deepcopy(candidate)
                new_candidate.subtask=2
                #new_candidate.the_question=new_candidate.the_question.replace('Which', 'How many', 1).replace('event', 'events', 1)
                next_id = subtask2q_ids['2']['options'].pop()
                #next_id = next_q_id_v2(subtask2q_ids, '2')
                new_candidate.q_id=next_id
                questions[new_candidate.q_id] = new_candidate.question()
                print("Copying %s to %s..." % (candidate.q_id, new_candidate.q_id))
                answers[new_candidate.q_id] = new_candidate.answer_info

                # remove old question + answer + system input file
                del questions[s1_qid]
                assert s1_qid not in questions, '%s still in questions' % s1_qid
                del answers[s1_qid]
                assert s1_qid not in answers,   '%s still in answers' % s1_qid

                copied_cnt+=1

            ### S2 magic done! ###

            # logging
            num_added += 1
            if num_added == maximum:
                break

    #question_out_path = '%s/questions.json' % args.output_folder
    #with open(question_out_path, 'w') as outfile:
    #    outfile.write(json.dumps(questions, indent=4, sort_keys=True))

    #answers_out_path = '%s/answers.json' % args.output_folder
    #with open(answers_out_path, 'w') as outfile:
    #    outfile.write(json.dumps(answers, indent=4, sort_keys=True))

    # write to file
    output_path = '%s/system_input/docs.conll' % args.output_folder
    with open(output_path, 'w') as outfile:
        for doc_id in all_docs:
            conll_info = doc_id2conll[doc_id]
            for line in conll_info:
                outfile.write(line)

    ### SPLIT INTO THREE SUBTASK JSONS ###

    a=one_to_three(answers)
    print(len(a["1"]), len(a["2"]), len(a["3"]), len(answers))
    q=one_to_three(questions)

    ### Store JSONS per subtask ###

    for x in ["1", "2", "3"]:
        q_outfile='%s/%s_questions.json' % (args.output_folder, x)
        a_outfile='%s/%s_answers.json' % (args.output_folder, x)
        with open(q_outfile, 'w') as wq:
            wq.write(json.dumps(q[x], indent=4, sort_keys=True))

        with open(a_outfile, 'w') as wa:
            wa.write(json.dumps(a[x], indent=4, sort_keys=True))


    compute_avg_confusion_advanced(all_candidates)
