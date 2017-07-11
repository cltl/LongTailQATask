import argparse
import subprocess
import json
from glob import glob
import pickle
import os
from random import shuffle, choice
import sys

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
                print(c1.q_id, c2.q_id)
                print(c1.answer_info['answer_docs'].keys(), c2.answer_info['answer_docs'].keys())
                if choice('01')=='0': # choose c1
                    c2.to_include_in_task=False
                    print("I CHOOSE C1")
                else: # choose c2
                    c1.to_include_in_task=False
                    print("I CHOSE C2")
                    break
    return cands

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Create participant data for SemEval-2018 task 5')
    parser.add_argument('-d', dest='input_folder', required=True, help='all .bin files in this folder will be considered')
    parser.add_argument('-o', dest='output_folder', required=True, help='folder output will be stored')
    args = parser.parse_args()

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
        candidates = pickle.load(open(bin_path, 'rb'))
        all_candidates.update(candidates)

    print(len(all_candidates))

    # load tokenization
    path_cache_tokenization = '%s/tokenization.cache' % args.input_folder
    with open(path_cache_tokenization, 'rb') as infile:
        doc_id2conll = pickle.load(infile)

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
#    new_candidates=deduplicate(candidates)
    new_candidates=candidates

    for candidate in new_candidates:
        # update question and answer dictionaries
        if candidate.to_include_in_task:
            questions[candidate.q_id] = candidate.question()
            answers[candidate.q_id] = candidate.answer_info

            # write to file
            output_path = '%s/system_input/%s.conll' % (args.output_folder, candidate.q_id)
            with open(output_path, 'w') as outfile:
                for a_type, a_row in types_and_rows:
                    for source_url in a_row['incident_sources']:
                        if source_url not in doc_id2conll:
                            continue

                        conll_info = doc_id2conll[source_url]
                        for line in conll_info:
                            outfile.writelines(line)


    question_out_path = '%s/questions.json' % args.output_folder
    with open(question_out_path, 'w') as outfile:
        outfile.write(json.dumps(questions, indent=4, sort_keys=True))

    answers_out_path = '%s/answers.json' % args.output_folder
    with open(answers_out_path, 'w') as outfile:
        outfile.write(json.dumps(answers, indent=4, sort_keys=True))
