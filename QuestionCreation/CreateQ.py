import sys
import pandas

import look_up_utils
import createq_utils
import pickle
import argparse

if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Create data for SemEval-2018 task 5')
    parser.add_argument('-d', dest='path_gva_df', required=True, help='path to gva frame (../EventRegistries/GunViolenceArchive/frames/all)')
    parser.add_argument('-e', dest='event_types', required=True, help='event types separated by underscore e.g. killing_injuring')
    parser.add_argument('-s', dest='subtask', required=True, help='1 | 2 | 3')
    parser.add_argument('-o', dest='output_folder', required=True, help='folder where output will be stored')
    args = parser.parse_args()

    # load arguments
    confusion_tuples = [('location', 'time'),
                        ('participant', 'time'),
                        ('location', 'participant')]
    event_types = args.event_types.split('_')
    subtask = int(args.subtask)
    all_candidates = set()
    df = pandas.read_pickle(args.path_gva_df)

    output_path = '%s/%s---%s.bin' % (args.output_folder, args.subtask, args.event_types)

    if subtask not in {1,2,3}:
        print('invalid subtask: %s' % subtask)
        sys.exit()

    print(args.__dict__)

    # set min and max number of incidents
    min_num_answer_incidents = 0
    max_num_answer_incidents = 99999

    if subtask==1:
        min_num_answer_incidents = 1
        max_num_answer_incidents = 1
    elif subtask==2:
        min_num_answer_incidents = 2

    # create questions
    for confusion_tuple in confusion_tuples:
        look_up, parameters2incident_uris = look_up_utils.create_look_up(df,
                                                                     discard_ambiguous_names=True,
                                                                     allowed_incident_years={2017},
                                                                     check_name_in_article=True)

        candidates=createq_utils.lookup_and_merge(look_up,
                                                  parameters2incident_uris,
                                                  confusion_tuple,
                                                  min_num_answer_incidents,
                                                  max_num_answer_incidents,
                                                  subtask,
                                                  event_types,
                                                  df,
                                                  debug=False,
                                                  inspect_one=False,
                                                  set_attr_values=False)
        all_candidates.update(candidates)

        print(confusion_tuple, len(candidates))


    # write to file
    with open(output_path, 'wb') as outfile:
        pickle.dump(all_candidates, outfile)
