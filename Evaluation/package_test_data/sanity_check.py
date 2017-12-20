import json
import random
import pprint

def get_docid2title_and_body(path_docs_conll):
    """
    load mapping docid 2 its title and body

    :param str path_docs_conll: path to docs.conll file

    :rtype: dict
    :return: mapping docid -> {'title': title, 'body' : body'}
    """
    docid2title_and_body = dict()
    with open(path_docs_conll) as infile:
        for line in infile:

            if line.startswith('#'):
                continue

            token_id, token, discourse, anno = line.strip().split('\t')
            if discourse == 'DCT':
                continue

            doc_id, sent_id, t_id = token_id.split('.')

            if doc_id not in docid2title_and_body:
                docid2title_and_body[doc_id] = {
                    'title' : [],
                    'body': []
                }

            if sent_id.startswith('t'):
                docid2title_and_body[doc_id]['title'].append(token)
            elif sent_id.startswith('b'):
                docid2title_and_body[doc_id]['body'].append(token)

    return docid2title_and_body

def show_info(subtask, title=False, body=False):
    """
    show question info

    :param str subtask: s1 | s2 | s3
    :param bool title: if True, print title
    :param bool body: if True: print body

    :return:
    """
    questions_path = 'test_data_gold/input/{subtask}/questions.json'.format_map(locals())
    answers_path = 'test_data_gold/dev_data/{subtask}/answers.json'.format_map(locals())

    questions = json.load(open(questions_path))
    answers = json.load(open(answers_path))

    q_ids = list(questions.keys())
    q_id_to_inspect = random.choice(q_ids)

    print('q_id', q_id_to_inspect)
    print()
    q = questions[q_id_to_inspect]
    pprint.pprint(q)
    print()
    a = answers[q_id_to_inspect]
    pprint.pprint(a)
    print()

    for answer_inc, answer_docs in a['answer_docs'].items():
        print()
        print('answer incident', answer_inc)
        for answer_doc in answer_docs:

            if title:
                print(' '.join(docid2title_and_body[answer_doc]['title']))
            if body:
                print(' '.join(docid2title_and_body[answer_doc]['body']))

if __name__ == '__main__':

    docid2title_and_body = get_docid2title_and_body('test_data_gold/input/s1/docs.conll')
    subtask = 's2'
    show_info(subtask, title=True, body=False)