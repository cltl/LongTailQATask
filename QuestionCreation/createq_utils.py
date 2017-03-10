import metrics
from classes import Question


def lookup_and_merge(look_up,
                     parameters2incident_uris,
                     confusion_tuple,
                     min_num_answer_incidents,
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
    :param pandas.core.frame.DataFrame df: gunviolence dataframes
    :param bool debug: set all class properties to debug
    :param bool inspect_one: if True, the first question will be printed to stdout
    
    :rtype: set
    :return set of Question class instances (each representing a question)
    """
    all_questions = set()
    q_id = 1

    for granularity in (look_up[confusion_tuple]):
        for sf in look_up[confusion_tuple][granularity]:
            num_answer_e = len(look_up[confusion_tuple][granularity][sf])
            if num_answer_e >= min_num_answer_incidents:
                meanings = look_up[confusion_tuple][granularity][sf]

                # obtain answers uris
                # filter out FireRescue incident from answer incident uris
                answer_incident_uris = {answer_incident_uri
                                        for answer_incident_uri in
                                        parameters2incident_uris[confusion_tuple][granularity][sf]
                                        if not answer_incident_uri.startswith('FR')}
            
                
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
                set_confusion_uris = confusion_incident_uris[0] | confusion_incident_uris[1]
                confusion_df = df.query('incident_uri in @set_confusion_uris')

                answer_df = df.query('incident_uri in @answer_incident_uris')

                q_instance = Question(
                    q_id=q_id,
                    confusion_factors=confusion_tuple,
                    granularity=granularity,
                    sf=sf,
                    meanings=meanings,
                    answer=len(answer_incident_uris),
                    oa_info=oa,
                    answer_df=answer_df,
                    answer_incident_uris=answer_incident_uris,
                    confusion_df=confusion_df,
                    confusion_incident_uris=set_confusion_uris
                )
                
                if debug:
                    q_instance.debug()

                q_id += 1

                if inspect_one:
                    for attr in [
                        # 'participant_confusion',
                        # 'location_confusion',
                        # 'time_confusion',
                        'q_id',
                        'question',
                        'answer_incident_uris',
                        'a_avg_num_sources',
                        'c_avg_num_sources',
                        'a_avg_date_spread',
                        'c_avg_date_spread'
                    ]:
                        print(attr, getattr(q_instance, attr))
                    print(look_up[confusion_tuple][granularity][sf])
                    input('continue?')

                all_questions.add(q_instance)

    return all_questions
