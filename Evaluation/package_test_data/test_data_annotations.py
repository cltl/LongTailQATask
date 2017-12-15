import subprocess
import os
import json
import pickle
import operator
import pandas

from glob import glob
from collections import defaultdict
from collections import Counter
from datetime import datetime

from iaa import IAA


# folder rm and mkdir
def reset():
    """
    remove folder 'input' if it exists and create this structure:
    test_annotations
        input
            s1
            s2
            s3
        dev_data
            s1
            s2
            s3
    """

    commands = ['rm -rf test_annotations',
                'mkdir -p test_annotations/input/s1',
                'mkdir -p test_annotations/input/s2',
                'mkdir -p test_annotations/input/s3',
                'mkdir -p test_annotations/dev_data/s1',
                'mkdir -p test_annotations/dev_data/s2',
                'mkdir -p test_annotations/dev_data/s3',
                ]

    for command in commands:
        try:
            subprocess.check_output(command, shell=True)
        except subprocess.CalledProcessError as e:
            print(e)

# load conll + create q_id2docs
def load_conll(input_dir, cache_path, debug=False):
    """
    load all docs from all conll from all subtasks

    :param str input_dir: directory with all conll files


    :rtype: tuple
    :return: (subtask2conll, q_id2docs, token_id2token)
    """
    if os.path.exists(cache_path):
        with open(cache_path, 'rb') as infile:

            if debug:
                print('load_conll from cache')
            subtask2conll, q_id2docs, token_id2token = pickle.load(infile)
            return subtask2conll, q_id2docs, token_id2token

    subtask2conll = dict()
    q_id2docs = defaultdict(set)
    token_id2token = dict()

    iterable = glob('%s/*.conll' % input_dir)

    for num_conll, conll_path in enumerate(iterable, 1):

        if all([debug,
                num_conll % 100 == 0]):
            print(num_conll, datetime.now())
        with open(conll_path) as infile:

            basename = os.path.basename(conll_path)
            q_id = basename.replace('.conll', '')

            doc_id2conll = defaultdict(list)


            for line in infile:

                token_id = None

                if not line.startswith('#'):
                    token_id, token, discourse, anno = line.strip().split('\t')
                    token_id2token[token_id] = token

                elif line.startswith('#begin document'):
                    doc_id = line[17:-3]
                    q_id2docs[q_id].add(doc_id)

                doc_id2conll[doc_id].append((token_id, line))

                if line.startswith('#end document'):
                    if doc_id not in subtask2conll:
                        subtask2conll[doc_id] = doc_id2conll[doc_id]

    if debug:
        print('num conll files', num_conll)
        print('num unique docs', len(subtask2conll))
        print('num qs', len(q_id2docs))

    if debug:
        print('recomputed load_conll')
    with open(cache_path, 'wb') as outfile:
        pickle.dump((subtask2conll, q_id2docs, token_id2token),
                    outfile)

    return subtask2conll, q_id2docs, token_id2token


def load_mappings_mentions2solution(path_excel_file):
    """
    load solution proposed by Roxane to map mentions to either
    1) delete
    2) map to new event type

    :param str path_to_excel_file: path to excel file
    (now in resources/InputData_annotation_improvement.xlsx)

    :rtype: tuple
    :return: (set of mentions of which annotations should be deleted,
              mapping from mention -> new eventtype)
    """
    delete = set()
    old2new_eventtype = dict()

    df = pandas.read_excel(path_excel_file, sheetname='Sheet3')
    for index, row in df.iterrows():

        if row['auto'] == 'auto':

            category = row['category']
            mention = row['mention'][2:-1]

            if category == 'delete':
                delete.add(mention)

            elif category == 'ETM':
                new_eventtype = row['new_eventtype'].replace("'", "")
                old2new_eventtype[mention] = new_eventtype

    return delete, old2new_eventtype


# create new questions.json + save
def update_questions_and_answers_json(subtask, q_id2docs, total_num_docs, add_input_docs_ids=False):
    """
    add key 'input_doc_ids' to json and save it in new folder

    :param str subtask: s1 | s2 | s3
    :param collections.defaultdict q_id2docs: mapping from q_id to input documents for participants
    (output from load_conll function)

    """
    question_json_path = 'v1/input/%s/questions.json' % subtask
    questions = json.load(open(question_json_path))

    answers_json_path = 'v1/dev_data/%s/answers.json' % subtask
    answers = json.load(open(answers_json_path))

    stats_input = {}

    # needed if you want to add the key 'input_doc_ids' to the questions json
    for q_id, q_info in answers.items():

        num_answer_docs = sum([len(docs)
                               for docs in q_info['answer_docs'].values()
                               ])

        confusion_docs = list(q_id2docs[q_id])
        num_confusion_docs = len(confusion_docs)

        num_noise_docs = total_num_docs - (num_confusion_docs + num_answer_docs)

        assert (num_answer_docs + num_confusion_docs + num_noise_docs) == total_num_docs, 'total: %s, answer: %s, confusion: %s, noise: %s' % (total_num_docs,
                                                                                                                                               num_answer_docs,
                                                                                                                                               num_confusion_docs,
                                                                                                                                               num_noise_docs)

        q_stats_info = {
            'answer' : q_info['numerical_answer'],
            'num_answer_docs' : num_answer_docs,
            'num_confunsion_docs' : num_confusion_docs,
            'num_noise_docs' : num_noise_docs
        }

        stats_input[q_id] = q_stats_info

        if add_input_docs_ids:
            questions[q_id]['input_doc_ids'] = list(q_id2docs[q_id])

    output_question_json_path = 'v2/input/%s/questions.json' % subtask

    with open(output_question_json_path, 'w') as outfile:
        json.dump(questions, outfile, indent=4, sort_keys=True)


    # mv answers.json
    command = 'cp v1/dev_data/%s/answers.json v2/dev_data/%s/answers.json' % (subtask, subtask)
    try:
        subprocess.check_output(command, shell=True)
    except subprocess.CalledProcessError as e:
        print(e)

    return stats_input


def mwu_token_list(mwu_ids, inc_id, token_id2token, debug=False):
    """
    given a list of token ids, return the same token ids
    but with missing token ids added,

    e.g. mwu_ids = ['1', '2,', '4'] -> ['1', '2', '3', '4']

    syntax of identifier is 'DOC_ID.SENT_ID.W_ID'
    :param list mwu_ids: e.g.
    ['abc4c58e9b7621b10a4732a98dc273b3.b3.15',
    'abc4c58e9b7621b10a4732a98dc273b3.b3.17',
    'abc4c58e9b7621b10a4732a98dc273b3.b3.18']

    :rtype: list
    :return: list of token ids
    """
    assert len(mwu_ids) >= 2, 'incident_id: %s (token: %s), mwu_ids should be a length 2 at least: %s' % (inc_id,
                                                                                                          token_id2token[mwu_ids[0]],
                                                                                                          mwu_ids)

    new_mwu_ids = []

    first_id = mwu_ids[0]
    doc_id, sent_id, first_token_id = first_id.split('.')

    last_id = mwu_ids[-1]
    doc_id, sent_id, last_token_id = last_id.split('.')

    for w_id in range(int(first_token_id),
                      int(last_token_id) + 1):

        new_id = '{doc_id}.{sent_id}.{w_id}'.format_map(locals())
        new_mwu_ids.append(new_id)

        if debug:
            if new_id not in mwu_ids:
                print()
                print('added', new_id)
                print('old mwu_ids', mwu_ids)

    return new_mwu_ids

def assert_ann_info(ann_info):
    """
    check for an annotation, e.g.
    {'cardinality': 'UNK', 'eventtype': 'd', 'participants': ['2']}

    1. if no 'participants' -> 'UNK'

    assert:
    B (ALL)
    G (UNK)
    O (UNK)
    S (not explicit, but always NO participants. I think the label is NULL, but please check!)

    :param dict ann_info: e.g. {'cardinality': 'UNK', 'eventtype': 'd', 'participants': ['2']}

    :rtype: dict
    :return: ann_info updated
    """

    # update all missing participant to 'UNK'
    if 'participants' not in ann_info:
        ann_info['participants'] = 'UNK'

    event_type = ann_info['eventtype']

    # HACK replace participants info from Areums for the event label ’s’ to UNK
    if event_type == 's':
        ann_info['participants'] = 'UNK'

    participants = ann_info['participants']


    if event_type == 'b':
        assert participants == 'ALL', 'participants for b should be ALL: %s' % ann_info

    if event_type == 'g':
        assert participants == 'UNK', 'participants for g should be UNK: %s' % ann_info

    if event_type == 'o':
        assert participants == 'UNK', 'participants for o should be UNK: %s' % ann_info

    if event_type == 's':
        assert participants == 'UNK', 'participants for s should be UNK: %s' % ann_info


    return ann_info


# load annotations
def load_men_annotations(user_annotations,
                         token_id2token,
                         delete,
                         old2new_eventtype,
                         debug=False):
    """
    load mention annotations

    :param dict user_annotations: mapping inc_id -> inc_info
    :param dict token_id2token: mapping token_id -> token
    :param set delete: mentions of which annotations should be deleted (i.d. ignored)
    :param dict old2new_eventtype: mapping mention -> new eventtype
    :param str user: supported: 'areum' | 'ngan'

    :rtype: dict
    :return: token_id -> annotation info
    """
    token_id2anno = dict()
    vocabulary = defaultdict(int)

    for inc_id, inc_info in user_annotations.items():
            if debug >= 2:
                print(inc_id, len(inc_info))

            for token_id, ann_info in inc_info.items():

                ann_info = assert_ann_info(ann_info)
                event_type = ann_info['eventtype']

                local_token_id2anno = dict()

                if 'mwu' not in ann_info:
                    anno_template = '(%s)'
                    local_token_id2anno[token_id] = (inc_id, ann_info, anno_template)
                    mention = token_id2token[token_id]

                else:

                    try:
                        mwu_ids = mwu_token_list(ann_info['mwu'], inc_id, token_id2token, debug=False)
                    except AssertionError as e:
                        print(e)
                        continue

                    mw_length = len(mwu_ids)

                    mention_parts = []

                    for index, token_id in enumerate(mwu_ids, 1):

                        if index == 1:
                            anno_template = '(%s'
                        elif index == mw_length:
                            anno_template = '%s)'
                        else:
                            anno_template = '%s'

                        local_token_id2anno[token_id] = (inc_id, ann_info, anno_template)

                        mention_part = token_id2token[token_id]
                        mention_parts.append(mention_part)

                    mention = ' '.join(mention_parts)


                # apply strategies 'delete' and 'emt'
                emt = False

                if mention in delete:

                    if debug >= 2:
                        print()
                        print('delete %s' % mention, local_token_id2anno)

                    continue


                elif all([mention in old2new_eventtype,
                          event_type != 'o']):

                    new_event_type = old2new_eventtype[mention]
                    if event_type != new_event_type:

                        event_type = new_event_type
                        emt = True

                        if debug >= 2:
                            print()
                            print('emt from %s' % mention, local_token_id2anno)

                        for ann_info in local_token_id2anno.values():
                            ann_info[1]['eventtype'] = event_type

                        if debug >= 2:
                            print('emt to %s %s' % (mention, event_type), local_token_id2anno)

                if all([emt,
                        debug >= 2]):
                    print()
                    print(inc_id, 'local token_id2anno', local_token_id2anno)

                token_id2anno.update(local_token_id2anno)
                vocabulary[(mention, event_type)] += 1

    return token_id2anno, vocabulary

def save_vocab_to_file(vocabulary, output_path):
    """
    save vocabulary to file

    :param dict vocabulary: mapping (mention, eventtype) -> freq
    """
    with open(output_path, 'w') as outfile:
        for key, value in sorted(vocabulary.items(),
                                 reverse=True,
                                 key=operator.itemgetter(1)):
            out_line = '{key}\t{value}'.format_map(locals())
            outfile.write(out_line + '\n')

# lumping function
def lump(inc_id, anno, debug=False):
    """
    convert an annotation, e.g.
    {'cardinality': 'UNK', 'eventtype': 'd', 'participants': ['2']}

    to an integer.

    the eventtypes 'b' and 's' are lumped to 'bs'


    :rtype: str
    :return: an integer as a string


    """
    for key in {'cardinality',
                'eventtype'}:
        assert key in anno, '%s not in anno: %s' % (key, anno)

    event_type = anno['eventtype']
    cardinality = anno['cardinality']
    if 'participants' not in anno:
        participants = 'UNK'
    else:
        participants = anno['participants']

    # prefix
    if event_type == 'g':
        return '0'
    elif event_type == 'o':
        prefix = '1'
    elif event_type in {'b', 'd', 'h', 'i', 'm', 's'}:
        prefix = '2'
    else:
        assert False, 'event_type %s not in accepted eventtypes' % event_type

    # event types
    event_type_ord = str(ord(event_type))
    if event_type in {'b', 's'}:

        if debug:
            print()
            print('before lumping', event_type, cardinality, participants)

        if event_type == 'b':
            assert participants == 'ALL', '{participants} should be ALL with b'.format_map(locals())

            cardinality = 'UNK'
            participants = 'UNK'
            event_type = 'bs'
            event_type_ord = str(ord('b')) + str(ord('s'))

        elif all([event_type == 's',
                  type(participants) != list]):

            cardinality = 'UNK'
            participants = 'UNK'

            event_type = 'bs'
            event_type_ord = str(ord('b')) + str(ord('s'))

        if debug:
            print('after lumping', event_type, cardinality, participants)

    # participants
    part_string = ''.join(participants)
    if type(participants) != list:
        part_string = ''.join([str(ord(char))
                               for char in cardinality])

    # cardinality
    card_ord = ''.join([str(ord(char))
                        for char in cardinality])

    # to integer
    the_integer = '999'.join([prefix,
                              inc_id,
                              card_ord,
                              event_type_ord,
                              part_string
                              ])

    if debug:
        print('prefix', prefix)
        print('cardinality', cardinality, card_ord)
        print('event_type', event_type, event_type_ord)
        print('participants', participants, part_string)
        print('integer', the_integer)

    return the_integer


# output conll with and without annotations (same time two files)
def to_conll(subtask, subtask2conll, token_id2anno):
    """
    write two conll files
    a) v2/dev_data/SUBTASK/docs.conll -> with annotations
    b) v2/input/SUBTASK/docs.conll -> without annotations

    :param dict doc_id2conll: output of load_conll function
    :param dict token_id2anno: output of load_men_annotations function

    """
    added = set()
    chains = defaultdict(int)

    anno_output_path = 'v2/dev_data/%s/docs.conll' % subtask
    no_anno_output_path = 'v2/input/%s/docs.conll' % subtask

    outfile_anno = open(anno_output_path, 'w')
    outfile_no_anno = open(no_anno_output_path, 'w')

    for doc_id, conll_info in subtask2conll.items():

        for token_id, line in conll_info:

            if token_id in token_id2anno:
                inc_id, ann_info, anno_template = token_id2anno[token_id]
                integer = lump(inc_id, ann_info)

                splitted = line.strip().split('\t')
                splitted[3] = anno_template % integer

                outfile_anno.write('\t'.join(splitted) + '\n')

                added.add(token_id)

                chains[anno_template % integer] += 1

            else:
                outfile_anno.write(line)

            outfile_no_anno.write(line)


    outfile_anno.close()
    outfile_no_anno.close()

    print('num chains', len(chains))
    print('distr', Counter(chains.values()))

    return added

def compute_stats(stats_input, output_path=None, debug=False):
    """
    compute stats:
    a) avg num of gold incidents
    b) avg num of gold docs
    c) 1 to n confusion documents
    d) 1 to n noise documents

    :param dict stats_input: mapping of q_id ->
    {
            'answer' : q_info['numerical_answer']
            'num_answer_docs' : num_answer_docs,
            'num_confunsion_docs' : num_confusion_docs,
            'num_noise_docs' : num_noise_docs
        }

    :rtype: dict
    :return:
    """
    stats = dict()

    for metric_name, input_key in [('gold_incidents', 'answer'),
                                   ('gold_docs', 'num_answer_docs'),
                                   ('confusion_docs', 'num_confunsion_docs'),
                                   ('noise_docs', 'num_noise_docs')
                                   ]:

        the_sum = sum([q_info[input_key]
                       for q_info in stats_input.values()])
        the_avg = the_sum / len(stats_input)

        stats[metric_name] = (the_sum, round(the_avg, 2))


    num_confusion_docs_per_gold_document = stats['confusion_docs'][0] / stats['gold_docs'][0]
    num_noise_docs_per_gold_document = stats['noise_docs'][0] / stats['gold_docs'][0]

    stats['num_confusion_docs_per_gold_document'] = round(num_confusion_docs_per_gold_document, 2)
    stats['num_noise_docs_per_gold_document'] = round(num_noise_docs_per_gold_document, 2)

    if debug:
        print(stats)

    if output_path:
        with open(output_path, 'w') as outfile:
            json.dump(stats, outfile, indent=4, sort_keys=True)


if __name__ == '__main__':

    # TODO: 2). Multiword token overlap: allow for a minimal token overlap and not a full token overlap. So: “turned the gun” and “turned the gun on” would be fully equivalent. The current IAA calculation is very strict on this.


    # call functions
    debug_value = 0

    # reset directories
    reset()

    # main loop
    all_added = set()

    # load mentions solutions proposed by Roxane
    delete, old2new_eventtype = load_mappings_mentions2solution('resources/InputData_annotation_improvement.xlsx')

    input_dir = '/home/filten/LongTailAnnotation/test_data2/CONLL'
    cache_path = 'cache/conll.bin'
    subtask2conll,\
    q_id2docs,\
    token_id2token = load_conll(input_dir,
                                cache_path,
                                debug=debug_value)
    total_num_docs = len(subtask2conll)


    anno_paths = [('areum', 'resources/ann_areum_men.json', 'output/vocab_areum.txt'),
                  ('ngan', 'resources/ann_ngan_men.json', 'output/vocab_ngan.txt')]
    input_annotations = dict()
    for user, input_path, output_path in anno_paths:

        user_annotations = json.load(open(input_path))
        input_annotations[user] = user_annotations

        token_id2anno, vocabulary = load_men_annotations(user_annotations,
                                                         token_id2token,
                                                         delete,
                                                         old2new_eventtype,
                                                         debug=debug_value)

        save_vocab_to_file(vocabulary, output_path)


    # compute IAA
    accepted_incidents = {'578238', '492366', '571210', '512274', '501412',
                          '525119', '548991', '517905', '512877', '566863'}
    stats_output_path = 'output/iaa_week5.xlsx'

    IAA(token_id2token, input_annotations, accepted_incidents, stats_output_path)

    for subtask in [
                    #'s1',
                    #'s2',
                    #'s3'
                    ]:

        if debug_value:
            print()
            print('subtask', subtask)

        #stats_input = update_questions_and_answers_json(subtask,
        #                                                q_id2docs,
        #                                                total_num_docs,
        #                                                add_input_docs_ids=False)

        #stats_output_path = 'v2/dev_data/%s/stats.json' % subtask

        #compute_stats(stats_input, output_path=None, debug=True)

        #added = to_conll(subtask, subtask2conll, token_id2anno)

        #all_added.update(added)


    #missing = set(token_id2anno) - all_added
    #print('added', len(all_added))
    #print('missing', len(missing))
    #print(missing)