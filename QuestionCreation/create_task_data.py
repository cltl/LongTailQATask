import argparse
import subprocess
import json
from glob import glob
import pickle
import os
from random import shuffle

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
        output_path = '%s/system_input/%s.conll' % (args.output_folder, candidate.q_id)
        candidate.generate_answer_info(types_and_rows, doc_id2conll, output_path, debug=False)

        # update question and answer dictionaries
        if candidate.to_include_in_task:
            questions[candidate.q_id] = candidate.question()
            answers[candidate.q_id] = candidate.answer_info

    question_out_path = '%s/questions.json' % args.output_folder
    with open(question_out_path, 'w') as outfile:
        outfile.write(json.dumps(questions, indent=4, sort_keys=True))

    answers_out_path = '%s/answers.json' % args.output_folder
    with open(answers_out_path, 'w') as outfile:
        outfile.write(json.dumps(answers, indent=4, sort_keys=True))
