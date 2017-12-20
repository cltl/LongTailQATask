import json

import validate_utils
from sanity_check import get_docid2title_and_body


if __name__ == '__main__':

    input_dir = 'test_data_gold'

    for subtask in [
                    's1',
                    's2',
                    's3'
                   ]:
        print()
        print('subtask', subtask)
        print()

        question_path = '{input_dir}/input/{subtask}/questions.json'.format_map(locals())
        questions = json.load(open(question_path))

        answers_path = '{input_dir}/dev_data/{subtask}/answers.json'.format_map(locals())
        answers = json.load(open(answers_path))

        num_qs = len(questions)
        num_as = len(answers)

        assert num_qs == num_as # num questions has to be num answers
        assert set(questions) == set(answers) # also same identifiers
        qs_to_delete = set()


        # check answers
        all_answers = validate_utils.get_dict_iterable(answers, ['numerical_answer'])

        event_type_dict = {'killing': 'num_killed',
                           'injuring': 'num_injured',
                           'job_firing': 'num_fired'}

        for q_id, numerical_answer in all_answers:

            if subtask == 's1':
                assert numerical_answer == 1
            if subtask in {'s2', 's3'}:
                assert numerical_answer >= 0


            if subtask in {'s1', 's2'}:
                assert numerical_answer == len(answers[q_id]['answer_docs'])
            elif subtask in {'s3'}:
                eventtype = questions[q_id]['event_type']
                to_look_for = event_type_dict[eventtype]

                part_info_value = sum([part_info[to_look_for]
                                       for part_info in answers[q_id]['part_info'].values()
                                      ])
                assert numerical_answer == part_info_value


        for confusion_param, granularities in [
                                               ('location', ['city', 'state']),
                                               ('time', ['day', 'month', 'year']),
                                               ('participant', ['first', 'last', 'full_name'])
                                               ]:
            for gran in granularities:
                iterable = validate_utils.get_dict_iterable(questions,
                                                            [confusion_param,
                                                            gran],
                                                            debug=True)

                for q_id, item in iterable:

                    if item in {'', None}:
                        qs_to_delete.add(q_id)
                        continue

                    assert item != '', '%s: item: %s (%s %s) is an empty string' % (q_id, item, confusion_param, gran)
                    assert item is not None, '%s: item: %s (%s %s) is None' % (q_id, item, confusion_param, gran)

                    if confusion_param == 'time':
                        validate_utils.time_check(item, gran)

                    elif confusion_param == 'location':
                        validate_utils.loc_check(item)

                    elif confusion_param == 'participant':
                        validate_utils.part_check(item, gran)

        # event types
        iterable_eventtypes = validate_utils.get_dict_iterable(questions,
                                                               ['event_type'],
                                                               debug=True)

        all_eventtypes = set()
        for q_id, the_eventtype in iterable_eventtypes:
            assert the_eventtype != '', '%s: item: %s is an empty string' % (q_id, item)
            assert the_eventtype is not None, '%s: item: %s is None' % (q_id, item)

            if subtask in {'s1', 's2'}:
                assert the_eventtype in {'injuring', 'killing', 'fire_burning', 'job_firing'}
            elif subtask == 's3':
                assert the_eventtype in {'injuring', 'killing', 'job_firing'}


            all_eventtypes.add(the_eventtype)

        if subtask in {'s1', 's2'}:
            assert all_eventtypes == {'injuring', 'killing', 'fire_burning', 'job_firing'}
        elif subtask == 's3':
            assert all_eventtypes == {'injuring', 'killing', 'job_firing'}


        # docs check
        docs_conll_path = '{input_dir}/input/{subtask}/docs.conll'.format_map(locals())
        docid2doc_info = get_docid2title_and_body(docs_conll_path)

        for q_id, answer_info in answers.items():
            for answer_inc, answer_docs in answer_info['answer_docs'].items():
                for answer_doc in answer_docs:
                    assert answer_doc in docid2doc_info


        print('qs to delete', qs_to_delete)


