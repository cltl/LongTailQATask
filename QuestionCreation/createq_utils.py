import metrics
from classes import Question

def filter_uris(the_uris, event_types):
    """
    remove uris from a certain type
            
    the_uris = ['FR1', '1', 'FR2', '2']
    event_types = ["killing"]
    output -> {'1', '2'}
                            
    the_uris = ['FR1', '1, 'FR2', '2']
    event_types = ["fire_burning"]
    output -> {'FR1', 'FR2'}
    """
    event_type = event_types[0]
                                                    
    if event_type in {'killing', 'injuring'}:
        uris = {uri for uri in the_uris if not uri.startswith('FR')}
                                                                        
    elif event_type == 'fire_burning':
        uris = {uri for uri in the_uris if uri.startswith('FR')}

    elif event_type == 'job_firing':
        uris = {uri for uri in the_uris if uri.startswith('BU')}

    return uris

def extract_gold_confusion_key(confusion_tuple,
                               meanings,
                               event_types):
    """
    extract gold and confusions keys + incident uris for n questions

    :param tuple confusion_tuple: ('location', 'time') |
    ('participant', 'time') | ('location', 'participant')
    :param dict meanings: meaning -> incident uris, e.g.
    for the confusion_tuple ('location', 'time'):
    {(('Mississippi', 'Jackson'), ('10/2016',)): {'688429'},
    (('Georgia', 'Jackson'), ('10/2016',)): {'686312'}}

    :rtype: list
    :return: list of dictionaries with the following keys:
    1. gold_keys
    2. gold_incident_uris
    3. confusion_keys
    4. confusion_incident_uris
    """
    gold_confusion_keys = []

    if 'location' in confusion_tuple:
        location_index = confusion_tuple.index('location')

        loc_meanings = {knowledge_types_key[location_index]
                        for knowledge_types_key in meanings}

        for loc_meaning in loc_meanings:

            question_info = {
                'gold_keys': set(),
                'gold_incident_uris': set(),
                'confusion_keys': set(),
                'confusion_incident_uris': set(),
                'gold_loc_meaning' : loc_meaning
            }

            for knowledge_types_key, incident_uris in meanings.items():

                if loc_meaning in knowledge_types_key:
                    answer_incident_uris = filter_uris(incident_uris, event_types)
                    if answer_incident_uris:
                        question_info['gold_keys'].add(knowledge_types_key)
                        question_info['gold_incident_uris'].update(incident_uris)
                else:
                    question_info['confusion_keys'].add(knowledge_types_key)
                    question_info['confusion_incident_uris'].update(incident_uris)

            if question_info['gold_keys']:
                gold_confusion_keys.append(question_info)

    else:
        question_info = {
            'gold_keys': set(),
            'gold_incident_uris': set(),
            'confusion_keys': set(),
            'confusion_incident_uris': set(),
            'gold_loc_meaning' : None
        }

        for knowledge_types_key, incident_uris in meanings.items():
            answer_incident_uris = filter_uris(incident_uris, event_types)
            if answer_incident_uris:
                question_info['gold_keys'].add(knowledge_types_key)
                question_info['gold_incident_uris'].update(incident_uris)
                gold_confusion_keys.append(question_info)

    return gold_confusion_keys

def event_typing(event_types, df, initial_answer_uris, confusion_uris, debug=False):
    new_answer_uris=set()
    answer_rows=df.query('incident_uri in @initial_answer_uris')

    if debug:
        print(event_types)

    for index,row in answer_rows.iterrows():

        add = False
        
        if 'fire_burning' in event_types and row['incident_uri'].startswith('FR'):
            new_answer_uris.add(row['incident_uri'])
            add = True

        if 'job_firing' in event_types and row['incident_uri'].startswith('BU'):
            new_answer_uris.add(row['incident_uri'])
            add = True

        if 'killing' in event_types and row['num_killed']>0:
            new_answer_uris.add(row['incident_uri'])
            add = True

            if debug:
                print('killing: %s' % row['incident_uri'])

        if 'injuring' in event_types and row['num_injured']>0:
            new_answer_uris.add(row['incident_uri'])
            add = True

            if debug:
                print('injuring: %s' % row['incident_uri'])

        if not add:
            confusion_uris.add(row['incident_uri'])

    if debug:
        input('continue?')
    return new_answer_uris, confusion_uris

def lookup_and_merge(look_up,
                     q_id,
                     parameters2incident_uris,
                     confusion_tuple,
                     min_num_answer_incidents,
                     max_num_answer_incidents,
                     subtask,
                     event_types,
                     df,
                     debug=False,
                     inspect_one=False):
    """
    create Question instances 
    
    :param dict look_up: see look_up_utils.py
    :param dict parameters2incident_uris: see look_up_utils.py
    :param tuple confusion_tuple: confusion setting, e.g. ('location', 'participant')
    :param int min_num_answer_incidents: threshold for minimum number of incidents that
    match with respect to confusion setting
    :param int max_num_answer_incidents: threshold for maximum number of incidents that
    match with respect to confusion setting
    :param bool count_participants: whether to count the participants. True for S3
    :param pandas.core.frame.DataFrame df: gunviolence dataframes
    :param bool debug: set all class properties to debug
    :param bool inspect_one: if True, the first question will be printed to stdout
    :param bool set_attr_values: if True, all property values will be computed
    
    :rtype: set
    :return set of Question class instances (each representing a question)
    """
    all_questions = set()

    for granularity in (look_up[confusion_tuple]):
        for sf in look_up[confusion_tuple][granularity]:
            meanings = look_up[confusion_tuple][granularity][sf]
            the_gold_confusion_keys = extract_gold_confusion_key(confusion_tuple, meanings, event_types)
            for question_info in the_gold_confusion_keys:

                answer_incident_uris = question_info['gold_incident_uris']
                num_answer_uris = len(question_info['gold_incident_uris'])
                if debug:
                    print()
                    print(granularity, sf)
                    print(num_answer_uris)
                    print(meanings)
                if num_answer_uris == 0:
                    print()
                    print('zero answer')
                    print('q_id', q_id)
                    print(confusion_tuple)
                    print(granularity)
                    print(sf)
                    print(meanings)
                    print(question_info['gold_loc_meangin'])


                    # TODO: update q_id

                    #q_instance = Question(
                    #    q_id=q_id,
                    #    confusion_factors=confusion_tuple,
                    #    granularity=granularity,
                    #    sf=sf,
                    #    meanings=meanings,
                    #    gold_loc_meaning=question_info['gold_loc_meaning'],
                    #   ev_answer=len(answer_incident_uris),
                    #    oa_info=oa,
                    #    answer_df=answer_df,
                    #    answer_incident_uris=answer_incident_uris,
                    #    confusion_df=confusion_df,
                    #    confusion_incident_uris=set_confusion_uris,
                    #    subtask=subtask,
                    #    event_types=event_types
                    #)

                    input('continue?')
                    


                if num_answer_uris >= min_num_answer_incidents and num_answer_uris<=max_num_answer_incidents:

                    if debug:
                        print()
                        print(question_info)


                    # obtain confusion uris
                    total_incident_uris = {0: set(), 1: set()}
                    confusion_incident_uris = {0: set(), 1: set()}
                    oa = {0: set(), 1: set()}

                    # total_incident_uris_part=set()
                    for index in [0, 1]:
                        confusion = confusion_tuple[index]
                        all_meanings = look_up[(confusion,)][(granularity[index],)][(sf[index],)]
                        oa[index] = metrics.get_observed_ambiguity(all_meanings)
                        for set_of_m in all_meanings.values():
                            total_incident_uris[index].update(set_of_m)
                        confusion_incident_uris[index] = total_incident_uris[index] - answer_incident_uris

                    # create confusion df and answer df
                    set_confusion_uris = question_info['confusion_incident_uris'] | confusion_incident_uris[0] | confusion_incident_uris[1]
                    
                    if debug:
                        print()
                        print(answer_incident_uris)
                        print(confusion_incident_uris)

                    answer_incident_uris, set_confusion_uris = event_typing(event_types, df, answer_incident_uris, set_confusion_uris, debug=False)
                    num_answer_uris = len(answer_incident_uris)

                    # filter confusion uris on event type

                    # remove fr from confusion uris if event_type in {injuring, killing}:
                    if event_types[0] in {'killing', 'injuring'}:
                        set_confusion_uris = filter_uris(set_confusion_uris, event_types)

                    if debug:
                        print()
                        print('answer', answer_incident_uris)
                        print('confusion', set_confusion_uris)
                        input('continue?')

                    if num_answer_uris < min_num_answer_incidents or num_answer_uris > max_num_answer_incidents:
                        continue
      
                    if not set_confusion_uris:
                        continue
 
                    confusion_df = df.query('incident_uri in @set_confusion_uris')
                    answer_df = df.query('incident_uri in @answer_incident_uris')

                    q_instance = Question(
                        q_id=q_id,
                        confusion_factors=confusion_tuple,
                        granularity=granularity,
                        sf=sf,
                        meanings=meanings,
                        gold_loc_meaning=question_info['gold_loc_meaning'],
                        ev_answer=len(answer_incident_uris),
                        oa_info=oa,
                        answer_df=answer_df,
                        answer_incident_uris=answer_incident_uris,
                        confusion_df=confusion_df,
                        confusion_incident_uris=set_confusion_uris,
                        subtask=subtask,
                        event_types=event_types
                    )


                    q_id += 1

                    if inspect_one:

                        for attr in [
                            'participant_confusion',
                            'location_confusion',
                            'time_confusion',
                            'q_id',
                            'question',
                            'granularity',
                            'answer_incident_uris',
                            'event_types',
                            #'confusion_incident_uris',
                            'meanings',
                            #'num_both_sf_overlap',
                            'gold_loc_meaning',
                            'a_avg_num_sources',
                            'c_avg_num_sources',
                            'a_avg_date_spread',
                            'c_avg_date_spread',
                            #'question_score'
                        ]:
                            print(attr, getattr(q_instance, attr))
                        input('continue?')

                    all_questions.add(q_instance)

    return q_id, all_questions
