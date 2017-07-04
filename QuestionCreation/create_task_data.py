import argparse
import subprocess
import json
from glob import glob
import pickle
import sys

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



    # convert trial data
    questions = dict()
    answers = dict()

    maximum = 20
    counter = 0
    for candidate in candidates:

        counter += 1
        if counter == maximum:
            break

        dfs = [('gold', candidate.answer_df),
               ('confusion', candidate.confusion_df)
               ]

        output_path = '%s/system_input/%s.conll' % (args.output_folder, candidate.q_id)
        candidate.to_conll_one_file_per_question(dfs, output_path)
        one_question = candidate.question()

        if len(candidate.all_doc_ids) != candidate.answer:
            print('mismatch answer and incidents/documents')

        if all([one_question is not None,
                len(candidate.all_doc_ids) >= 2]):
            questions[candidate.q_id] = one_question
            answers[candidate.q_id] = {'numerical_answer': len(candidate.all_doc_ids),
                                       'answer_docs': candidate.all_doc_ids}

    question_out_path = '%s/questions.json' % args.output_folder
    with open(question_out_path, 'w') as outfile:
        outfile.write(json.dumps(questions, indent=4, sort_keys=True))

    answers_out_path = '%s/answers.json' % args.output_folder
    with open(answers_out_path, 'w') as outfile:
        outfile.write(json.dumps(answers, indent=4, sort_keys=True))
