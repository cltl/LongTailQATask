import sys
import pandas
from datetime import datetime
import json
from collections import defaultdict

from classes import Question
import classes
import look_up_utils
import createq_utils
from display_utils import display_question

if __name__=="__main__":
    
    df = pandas.read_pickle('../EventRegistries/GunViolenceArchive/frames/all')
    confusion_tuple = ('location', 'time')
    event_types=['killing', 'injuring']
    if len(sys.argv)>1:
        subtask=int(sys.argv[1])
    else:
        subtask=2

    print("Generating questions for subtask %d" % subtask)

    min_num_answer_incidents = 0
    max_num_answer_incidents = 99999
    count_participants=False

    if subtask==1:
        min_num_answer_incidents = 1
        max_num_answer_incidents = 1
    elif subtask==2:
        min_num_answer_incidents = 2
    elif subtask!=3:
        print("Invalid subtask. Exiting now...")
        sys.exit()

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
                                          set_attr_values=True) 

    print(len(candidates))
    print({c.granularity for c in candidates})

    for c in candidates:
        print(c.question(), c.answer)
