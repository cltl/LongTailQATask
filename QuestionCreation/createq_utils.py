import metrics
from classes import Question


def extract_gold_confusion_key(confusion_tuple,
                               meanings):
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
                    answer_incident_uris = {uri
                                            for uri in incident_uris
                                            if not uri.startswith('FR')} # remove FireRescue1 incidents from gold
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
            answer_incident_uris = {uri
                                    for uri in incident_uris
                                    if not uri.startswith('FR')}  # remove FireRescue1 incidents from gold
            if answer_incident_uris:
                question_info['gold_keys'].add(knowledge_types_key)
                question_info['gold_incident_uris'].update(incident_uris)
                gold_confusion_keys.append(question_info)

    return gold_confusion_keys


def lookup_and_merge(look_up,
                     parameters2incident_uris,
                     confusion_tuple,
                     min_num_answer_incidents,
                     df,
                     debug=False,
                     inspect_one=False,
                     set_attr_values=False):
    """
    create Question instances 
    
    :param dict look_up: see look_up_utils.py
    :param dict parameters2incident_uris: see look_up_utils.py
    :param tuple confusion_tuple: confusion setting, e.g. ('location', 'participant')
    :param int min_num_answer_incidents: threshold for minimum number of incidents that
    match with respect to confusion setting
    :param pandas.core.frame.DataFrame df: gunviolence dataframes
    :param bool debug: set all class properties to debug
    :param bool inspect_one: if True, the first question will be printed to stdout
    :param bool set_attr_values: if True, all property values will be computed
    
    :rtype: set
    :return set of Question class instances (each representing a question)
    """
    all_questions = set()
    q_id = 1

    for granularity in (look_up[confusion_tuple]):
        for sf in look_up[confusion_tuple][granularity]:

            meanings = look_up[confusion_tuple][granularity][sf]
            the_gold_confusion_keys = extract_gold_confusion_key(confusion_tuple, meanings)

            for question_info in the_gold_confusion_keys:

                answer_incident_uris = question_info['gold_incident_uris']
                num_answer_uris = len(question_info['gold_incident_uris'])
                if num_answer_uris >= min_num_answer_incidents:

                    if debug:
                        print()
                        print(question_info)
                        input('continue?')


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
                    confusion_df = df.query('incident_uri in @set_confusion_uris')

                    answer_df = df.query('incident_uri in @answer_incident_uris')

                    q_instance = Question(
                        q_id=q_id,
                        confusion_factors=confusion_tuple,
                        granularity=granularity,
                        sf=sf,
                        meanings=meanings,
                        gold_loc_meaning=question_info['gold_loc_meaning'],
                        answer=len(answer_incident_uris),
                        oa_info=oa,
                        answer_df=answer_df,
                        answer_incident_uris=answer_incident_uris,
                        confusion_df=confusion_df,
                        confusion_incident_uris=set_confusion_uris
                    )

                    if debug:
                        q_instance.debug()

                    if set_attr_values:
                        vars(q_instance)

                    q_id += 1

                    if inspect_one:

                        for attr in [
                            # 'participant_confusion',
                            # 'location_confusion',
                            # 'time_confusion',
                            'q_id',
                            'question',
                            'granularity',
                            'answer_incident_uris',
                            #'confusion_incident_uris',
                            'meanings',
                            'num_both_sf_overlap',
                            'gold_loc_meaning',
                            'a_avg_num_sources',
                            'c_avg_num_sources',
                            #'a_avg_date_spread',
                            #'c_avg_date_spread'
                        ]:
                            print(attr, getattr(q_instance, attr))
                        print(look_up[confusion_tuple][granularity][sf])
                        input('continue?')

                    all_questions.add(q_instance)

    return all_questions
