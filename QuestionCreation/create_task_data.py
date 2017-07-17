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

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Create participant data for SemEval-2018 task 5')
    parser.add_argument('-d', dest='input_folder', required=True, help='all .bin files in this folder will be considered')
    parser.add_argument('-o', dest='output_folder', required=True, help='folder output will be stored')
    args = parser.parse_args()

    # enrichment parameters for S2
    num_zeros=10 # number of questions to draw from S1 but remove the answer docs
    num_ones=10 # number of questions to copy from s1 to s2

    copy_total=num_zeros+num_ones
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

    print("now deduplicating")
    print(sum(candidate.to_include_in_task
              for candidate in all_candidates))
    all_candidates=deduplicate(all_candidates)
    print('after deduplicating')
    print(sum(candidate.to_include_in_task
              for candidate in all_candidates))
#    new_candidates=candidates

    print("deduplication done. storing")

    num_added = 0
    maximum = 100000
    debug = False
    for candidate in all_candidates:
        # update question and answer dictionaries
        if candidate.to_include_in_task:
            questions[candidate.q_id] = candidate.question()
            answers[candidate.q_id] = candidate.answer_info

            if debug:
                print(candidate.gold_loc_meaning)
                input('continue?')

            # write to file
            output_path = '%s/system_input/%s.conll' % (args.output_folder, candidate.q_id)
            with open(output_path, 'w') as outfile:
                for a_type, a_row in candidate.types_and_rows:
                    for source_url in a_row['incident_sources']:
                        if source_url not in doc_id2conll:
                            continue

                        conll_info = doc_id2conll[source_url]
                        for line in conll_info:
                            outfile.write(line)

            ### Maybe copy the question to S2 ###
            if copied_cnt<copy_total and candidate.subtask==1: 
                s1_qid=candidate.q_id
                new_candidate=deepcopy(candidate)
                new_candidate.subtask=2
                #new_candidate.the_question=new_candidate.the_question.replace('Which', 'How many', 1).replace('event', 'events', 1)
                new_candidate.q_id='2-%d' % next_id
                questions[new_candidate.q_id] = new_candidate.question()
                print("Copying %s to %s..." % (candidate.q_id, new_candidate.q_id))
                src=output_path
                dst='%s/system_input/%s.conll' % (args.output_folder, new_candidate.q_id)

                if copied_cnt<num_zeros: # copy but modify the answer to 0
                    print("... but modifying the answer to 0")
                    with open(dst, 'w') as outfile:
                        for a_type, a_row in new_candidate.types_and_rows:
                            for source_url in a_row['incident_sources']:
                                if source_url not in doc_id2conll or source_url in new_candidate.answer_incident_uris:
                                    continue
                                conll_info = doc_id2conll[source_url]
                                for line in conll_info:
                                    outfile.write(line)
                    new_candidate.answer_info["answer_docs"]={}
                    new_candidate.answer_info["numerical_answer"]=0
                    new_candidate.answer_incident_uris=set()
                    new_candidate.ev_answer=0
                else:
                    print("... keeping the answer the same")
                    copyfile(src, dst)
                answers[new_candidate.q_id] = new_candidate.answer_info

                next_id+=1
                copied_cnt+=1
            ### S2 magic done! ###

            # logging
            num_added += 1
            if num_added == maximum:
                break

    question_out_path = '%s/questions.json' % args.output_folder
    with open(question_out_path, 'w') as outfile:
        outfile.write(json.dumps(questions, indent=4, sort_keys=True))

    answers_out_path = '%s/answers.json' % args.output_folder
    with open(answers_out_path, 'w') as outfile:
        outfile.write(json.dumps(answers, indent=4, sort_keys=True))

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
