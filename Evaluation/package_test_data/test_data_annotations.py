import subprocess
import os
import json
import pickle
import operator
import pandas
import string

pandas.set_option('display.max_colwidth', -1)

from collections import defaultdict
from collections import Counter

import mwu
from iaa import IAA


# folder rm and mkdir
def reset(input_folder, output_folder):
    """
    remove folder 'input' if it exists and create this structure:
    test_data
        input
            s1
            s2
            s3
        dev_data
            s1
            s2
            s3

    :param str input_folder: path to test_data folder containg both the .json files and the docs.conll files
    :param str output_folder: output folder
    """

    commands = ['rm -rf {output_folder} && mkdir {output_folder}'.format_map(locals()),
                'mkdir -p {output_folder}/input/s1'.format_map(locals()),
                'mkdir -p {output_folder}/input/s2'.format_map(locals()),
                'mkdir -p {output_folder}/input/s3'.format_map(locals()),
                'mkdir -p {output_folder}/dev_data/s1'.format_map(locals()),
                'mkdir -p {output_folder}/dev_data/s2'.format_map(locals()),
                'mkdir -p {output_folder}/dev_data/s3'.format_map(locals()),

                'cp {input_folder}/system_input/docs.conll {output_folder}/input/s1/docs.conll'.format_map(locals()),
                'cp {input_folder}/system_input/docs.conll {output_folder}/input/s2/docs.conll'.format_map(locals()),
                'cp {input_folder}/system_input/docs.conll {output_folder}/input/s3/docs.conll'.format_map(locals()),
                ]

    for command in commands:
        try:
            subprocess.check_output(command, shell=True)
        except subprocess.CalledProcessError as e:
            print(e)


def load_disqualified_docs(path_dis_areum_men,
                           path_dis_ngan_men,
                           debug=False):
    """
    load set of disqualified documents

    :param str path_dis_areum_men: basename will be dis_areum_men.json
    :param str path_dis_ngan_men: basename will be dis_ngan_men.json
    """
    dis_areum = json.load(open(path_dis_areum_men))
    dis_ngan = json.load(open(path_dis_ngan_men))

    disqualified_ngan = set()
    for dis_docs in dis_ngan.values():
        disqualified_ngan.update(dis_docs)

    disqualified_areum = set()
    for dis_docs in dis_areum.values():
        disqualified_areum.update(dis_docs)

    disqualified_docs = disqualified_ngan | disqualified_areum
    overlap = disqualified_ngan & disqualified_areum

    if debug:
        print()
        print('# overlap', len(overlap))
        print('# disqualified ngan', len(disqualified_ngan))
        print('# disqualified areum', len(disqualified_areum))
        print('# disqualified docs', len(disqualified_docs))

    return disqualified_docs

# load conll
def load_conll(conll_path,
               cache_path,
               overwrite=False,
               debug=False):
    """
    load all docs from all conll from all subtasks

    :param str conll_path: one conll file with all documents
    :param str cache_path: path where load_conll will be cached
    :param bool overwrite: if True, reload_conll


    :rtype: tuple
    :return: (subtask2conll, token_id2token)
    """
    if all([os.path.exists(cache_path),
            not overwrite]):
        with open(cache_path, 'rb') as infile:
            subtask2conll, token_id2token = pickle.load(infile)
            if debug:
                print()
                print('load_conll from cache')
                print('num unique docs', len(subtask2conll))
            return subtask2conll, token_id2token

    subtask2conll = dict()
    token_id2token = dict()

    with open(conll_path) as infile:

        doc_id2conll = defaultdict(list)

        for line in infile:

            token_id = None

            if not line.startswith('#'):
                token_id, token, discourse, anno = line.strip().split('\t')
                token_id2token[token_id] = token

            elif line.startswith('#begin document'):
                doc_id = line[17:-3]

            doc_id2conll[doc_id].append((token_id, line))

            if line.startswith('#end document'):
                if doc_id not in subtask2conll:
                    subtask2conll[doc_id] = doc_id2conll[doc_id]


    if debug:
        print()
        print('recomputed load_conll')
        print('num unique docs', len(subtask2conll))

    with open(cache_path, 'wb') as outfile:
        pickle.dump((subtask2conll, token_id2token),
                     outfile)

    return subtask2conll, token_id2token


def load_mappings_mentions2solution(path_excel_file):
    """
    load solution proposed by Roxane to map mentions to either
    1) delete
    2) map to new event type
    3) manually check

    :param str path_to_excel_file: path to excel file
    (now in resources/InputData_annotation_improvement.xlsx)

    :rtype: tuple
    :return: (set of mentions of which annotations should be deleted,
              mapping from mention -> new eventtype),
              mention -> info to manually check
    """
    delete = set()
    old2new_eventtype = dict()
    manual_check = dict()

    df = pandas.read_excel(path_excel_file, sheetname='Sheet3')
    for index, row in df.iterrows():

        category = row['category']
        mention = row['mention'][2:-1]

        if row['auto'] == 'auto':

            if category == 'delete':
                delete.add(mention)

            elif category == 'ETM':
                new_eventtype = row['new_eventtype'].replace("'", "")
                old2new_eventtype[mention] = new_eventtype

        elif row['auto'] == 'manual':
            user = None
            for a_user in [row['ngan'], row['areum']]:
                if a_user == 'Ngan':
                    user = 'ngan'
                elif a_user == 'Areum':
                    user = 'areum'

            old_eventtype = row['old_eventtype'][1:-1].replace("'", "")
            manual_check[mention] = {'eventtype': old_eventtype,
                                 'user': user,
                                 'category' : row['category']
                                 }

    return delete, old2new_eventtype, manual_check


# create new questions.json + save
def get_q_stats_info(input_folder, output_folder, subtask, total_num_docs):
    """

    :param str input_folder: output question creation
    :param str output_folder: folder where output will be stored
    :param str subtask: s1 | s2 | s3
    :param int total_num_docs: number of test data documents

    1) load SUBTASK_questions.json
    2) load SUBTASK_answers.json
    3) remove {'3-111371', '3-93518', '3-111370', '3-70', '3-1'}
    4) save
    a) test_data/input/SUBTASK/questions.json
    b) test_data/dev_data/SUBTASK/answers.json

    """
    num_subtask = subtask[1]
    answers_json_path = '{input_folder}/{num_subtask}_answers.json'.format_map(locals())
    questions_json_path = '{input_folder}/{num_subtask}_questions.json'.format_map(locals())

    questions = json.load(open(questions_json_path))
    answers = json.load(open(answers_json_path))

    if subtask == 's3':
        for q_id in {'3-111371', '3-93518', '3-111370', '3-70', '3-1'}:
            del questions[q_id]
            del answers[q_id]

    for q_id, q_info in questions.items():
        q_info['event_type'] = q_info['event_types'][0]
        del q_info['event_types']

    questions_out_path = '{output_folder}/input/{subtask}/questions.json'.format_map(locals())
    answers_out_path = '{output_folder}/dev_data/{subtask}/answers.json'.format_map(locals())

    for json_obj, out_path in [(questions, questions_out_path),
                               (answers, answers_out_path)]:
        with open(out_path, 'w') as outfile:
            json.dump(json_obj, outfile, indent=4, sort_keys=True)

    stats_input = {}
    event_type2q_ids = defaultdict(set)

    for q_id, q_info in answers.items():

        num_answer_docs = sum([len(docs)
                               for docs in q_info['answer_docs'].values()
                               ])


        for inc_id in q_info['answer_docs']:

            if inc_id.startswith('BU'):
                eventtype = 'BU'
            elif inc_id.startswith('FR'):
                eventtype = 'FR'
            elif len(inc_id) <= 6:
                eventtype = 'GVA'
            else:
                eventtype = 'GVA_dummy'

        num_noise_docs = total_num_docs - num_answer_docs

        assert (num_answer_docs + num_noise_docs) == total_num_docs, 'total: %s, answer: %s, noise: %s' % (total_num_docs,
                                                                                                           num_answer_docs,
                                                                                                           num_noise_docs)

        q_stats_info = {
            'answer' : q_info['numerical_answer'],
            'num_answer_docs' : num_answer_docs,
            'num_noise_docs' : num_noise_docs,
            'eventtype' : eventtype
        }

        stats_input[q_id] = q_stats_info

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

        if new_id in token_id2token:
            token = token_id2token[new_id]

            if all([token in string.punctuation,
                    token != '-']):
                print('punctuation in mw', inc_id, new_id, token_id2token[new_id])

        new_mwu_ids.append(new_id)


        if debug:
            if new_id not in mwu_ids:
                print()
                print('added', new_id)
                print('old mwu_ids', mwu_ids)

    # assert that they are all part of the same sentence
    sent_ids = set()
    for w_id in new_mwu_ids:
        doc_id, sent_id, last_token_id = w_id.split('.')
        sent_ids.add(sent_id)

    assert len(sent_ids) == 1, 'mw in more than one sentence: %s' % new_mwu_ids

    return new_mwu_ids, doc_id + '.' + sent_id

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
                         user,
                         manual_check,
                         token_id2token,
                         delete,
                         old2new_eventtype,
                         disqualified_docs,
                         disqualified_incidents={'387194'},
                         debug=False):
    """
    load mention annotations

    :param dict user_annotations: mapping inc_id -> inc_info
    :param str user: supported: 'areum' | 'ngan'
    :param dict manual_check: mapping mention to info to manually check
    :param dict token_id2token: mapping token_id -> token
    :param set delete: mentions of which annotations should be deleted (i.d. ignored)
    :param dict old2new_eventtype: mapping mention -> new eventtype
    :param set disqualified_docs: see output load_disqualified_docs
    :param set disqualified_incidents: default is {'387194'}

    :rtype: dict
    :return: token_id -> annotation info
    """
    token_id2anno = dict()
    vocabulary = defaultdict(int)

    documents_not_in_test_data = set()
    mw2sent_id = defaultdict(list)
    all_mwus = []
    list_of_lists = []
    headers = ['inc_id', 'doc_id', 'mention', 'eventtype', 'category']

    num_anno_from_dis_docs = 0

    for inc_id, inc_info in user_annotations.items():

        if inc_id in disqualified_incidents:

            if debug_value:
                print()
                print(inc_id, 'ignored')
            continue

        if debug >= 2:
            print(inc_id, len(inc_info))

        for token_id, ann_info in inc_info.items():

            doc_id, sent_id, t_id = token_id.split('.')
            if doc_id in disqualified_docs:

                if debug_value >= 2:
                    print(token_id, 'is part of disqualified documents')

                num_anno_from_dis_docs += 1
                continue

            ann_info = assert_ann_info(ann_info)
            event_type = ann_info['eventtype']

            local_token_id2anno = dict()
            all_token_ids_in_test_document = True

            if 'mwu' not in ann_info:
                anno_template = '(%s)'
                local_token_id2anno[token_id] = (inc_id, ann_info, anno_template)

                if [token_id] not in all_mwus:
                    all_mwus.append([token_id])

                if token_id not in token_id2token:
                    a_doc_id = token_id.split('.')[0]
                    documents_not_in_test_data.add(a_doc_id)
                    all_token_ids_in_test_document = False
                else:
                    mention = token_id2token[token_id]

            else:

                try:
                    mwu_ids, sent_id = mwu_token_list(ann_info['mwu'], inc_id, token_id2token, debug=False)
                except AssertionError as e:
                    print(e)
                    continue

                # uncomment to see sentences that have multiple mwu's
                #if sent_id in mw2sent_id:
                #    #print('more than one mwu in sentence: %s' % sent_id)

                if mwu_ids not in all_mwus:
                    all_mwus.append(mwu_ids)
                mw2sent_id[sent_id].append(mwu_ids)

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

                    if token_id not in token_id2token:
                        a_doc_id = token_id.split('.')[0]
                        documents_not_in_test_data.add(a_doc_id)
                        all_token_ids_in_test_document = False
                        continue

                    mention_part = token_id2token[token_id]
                    mention_parts.append(mention_part)

                mention = ' '.join(mention_parts)


            if mention in manual_check:
                man_info = manual_check[mention]

                if all([
                    man_info['user'] == user,
                    man_info['eventtype'] == ann_info['eventtype']
                ]):
                    one_row = [inc_id, doc_id, mention, man_info['eventtype'], man_info['category']]
                    list_of_lists.append(one_row)

            # check if all token_id are in test documents
            if not all_token_ids_in_test_document:
                continue

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


    man_check_df = pandas.DataFrame(list_of_lists, columns=headers)
    out_path = 'manual_checking/%s.xlsx' % user
    man_check_df.to_excel(out_path)

    if debug_value:
        print('missing documents', documents_not_in_test_data)

    if debug_value:
        print('num anno ignored due to being in disqualified docs', num_anno_from_dis_docs)

    return token_id2anno, vocabulary, all_mwus

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


def to_integer(inc_id, anno, debug=False):
    """
    convert an annotation, e.g.
    {'cardinality': 'UNK', 'eventtype': 'd', 'participants': ['2']}

    to an integer.
    :param str inc_id: incident identifier
    :param dict anno: annotation, e.g.
    {'cardinality': 'UNK', 'eventtype': 'd', 'participants': ['2']}

    note: only eventtype and participants are used

    :rtype: tuple
    :return: (inc_id.eventtype.particpants,
              an integer as a string)

    """
    eventtype2full_label = {
        'b': 'bag_of_events',
        'd': 'death',
        'g': 'generic',
        'h': 'hitting',
        'i': 'injuring',
        'm': 'missing',
        'o': 'other',
        's': 'firing_a_gun'
    }

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
        return ('0', '0')
    elif event_type == 'o':
        prefix = '1'
    elif event_type in {'b', 'd', 'h', 'i', 'm', 's'}:
        prefix = '2'
    else:
        assert False, 'event_type %s not in accepted eventtypes' % event_type

    # event types
    event_type_ord = str(ord(event_type))

    # participants
    part_string = ''.join(participants)
    if type(participants) != list:
        part_integer = ''.join([str(ord(char))
                               for char in cardinality])
    else:
        part_integer = part_string

    # to integer
    the_integer = '999'.join([prefix,
                              inc_id,
                              event_type_ord,
                              part_integer
                              ])

    if debug:
        print('prefix', prefix)
        print('event_type', event_type, event_type_ord)
        print('participants', participants, part_string)
        print('integer', the_integer)

    full_label = eventtype2full_label[event_type]
    the_string = '{inc_id}.{full_label}.{part_string}'.format_map(locals())

    for char in the_integer:
        assert type(int(char)) == int

    return the_string, the_integer

# output conll with and without annotations (same time two files)
def to_conll(output_folder, subtask, subtask2conll, user2token_id2anno, iaa_incidents, setting):
    """
    write one conll file:
    a) test_data/SUBTASK/docs.conll -> with annotations

    :param str output_folder: output folder
    :param str subtask: s1 | s2 | s3
    :param dict subtask2conll: output of load_conll function
    :param dict user2token_id2anno: mapping of user -> output of load_men_annotations function
    :param set iaa_incidents: set of iaa incident identifiers
    :param str setting: corpses_corpus | semeval
    """
    assert setting in {'corpses_corpus', 'semeval'}

    eventtype2full_label = {
        'b': 'bag_of_events',
        'd': 'death',
        'g': 'generic',
        'h': 'hitting',
        'i': 'injuring',
        'm': 'missing',
        'o': 'other',
        's': 'firing_a_gun'
    }
    added = set()
    chains = defaultdict(int)


    incidents = set()
    docs = set()
    type_freq = defaultdict(int)
    eventtype2expression_freq = {}

    anno_output_path = '{output_folder}/dev_data/{subtask}/docs.conll'.format_map(locals())

    mention_parts = []

    with open(anno_output_path, 'w') as outfile_anno:

        for doc_id, conll_info in subtask2conll.items():


            has_annotation = False
            doc_lines = []

            for token_id, line in conll_info:

                written_line = False
                add = False

                if token_id in user2token_id2anno['areum']:
                    inc_id, ann_info, anno_template = user2token_id2anno['areum'][token_id]
                    add = True

                elif token_id in user2token_id2anno['ngan']:
                    inc_id, ann_info, anno_template = user2token_id2anno['ngan'][token_id]
                    if inc_id not in iaa_incidents:
                        add = True

                if add:

                    splitted = line.strip().split('\t')

                    incidents.add(inc_id)
                    docs.add(doc_id)


                    if setting == 'semeval':
                        integer = lump(inc_id, ann_info)
                    elif setting == 'corpses_corpus':
                        anno_string, integer = to_integer(inc_id, ann_info)
                        splitted.append(anno_string)

                    splitted[3] = anno_template % integer

                    assert token_id not in added
                    added.add(token_id)

                    token = splitted[1]

                    if anno_template.endswith(')'): # meaning that this is the end of an expression

                        chains[integer] += 1
                        mention_parts.append(token)

                        full_label = eventtype2full_label[ann_info['eventtype']]
                        type_freq[full_label] += 1

                        mention = ' '.join(mention_parts)

                        if full_label not in eventtype2expression_freq:
                            eventtype2expression_freq[full_label] = defaultdict(int)

                        eventtype2expression_freq[full_label][mention] += 1
                        mention_parts = []
                    else:
                        mention_parts.append(token)

                    #outfile_anno.write('\t'.join(splitted) + '\n')
                    doc_lines.append('\t'.join(splitted) + '\n')
                    has_annotation = True
                    written_line = True

                if not written_line:

                    if all([setting == 'corpses_corpus',
                            not line.startswith('#')]):
                        line = line[:-1] + '\t-\n'

                    #outfile_anno.write(line)
                    doc_lines.append(line)

            if has_annotation:
                for doc_line in doc_lines:
                    outfile_anno.write(doc_line)

    print('num chains', len(chains))
    print('distr', Counter(chains.values()))

    num_mentions = sum(chains.values())

    print('num expressions', num_mentions)

    stats = {'#_incidents': len(incidents),
             '#_docs' : len(docs),
             '#_token_annotations': len(added),
             '#_mentions' : num_mentions,
             '#_clusters': len(chains),
             '#_type_freq': type_freq,
             }
    return added, stats, eventtype2expression_freq

def compute_stats(stats_input, output_path=None, debug=False):
    """
    compute stats:
    a) avg num of gold incidents
    b) avg num of gold docs
    c) 1 to n noise documents

    :param dict stats_input: mapping of q_id ->
    {
            'answer' : q_info['numerical_answer']
            'num_answer_docs' : num_answer_docs,
            'num_noise_docs' : num_noise_docs
        }

    :rtype: dict
    :return:
    """
    stats = dict()

    for metric_name, input_key in [('gold_incidents', 'answer'),
                                   ('gold_docs', 'num_answer_docs'),
                                   ('noise_docs', 'num_noise_docs')
                                   ]:

        the_sum = sum([q_info[input_key]
                       for q_info in stats_input.values()])
        the_avg = the_sum / len(stats_input)

        stats[metric_name] = (the_sum, round(the_avg, 2))


    num_noise_docs_per_gold_document = stats['noise_docs'][0] / stats['gold_docs'][0]
    stats['num_noise_docs_per_gold_document'] = round(num_noise_docs_per_gold_document, 2)

    if debug:
        print()
        print(stats)
        print()
        print('eventtypes distribution')
        distr = Counter([q_info['eventtype']
                        for q_info in stats_input.values()])
        print(distr)


    if output_path:
        with open(output_path, 'w') as outfile:
            json.dump(stats, outfile, indent=4, sort_keys=True)


def stats2latex(stats, eventtype2expr2freq):
    num_mentions = stats['#_mentions']
    num_incs = stats['#_incidents']
    num_docs = stats['#_docs']
    sentence_one = 'The corpses corpus contains {num_mentions} mentions, referring to {num_incs} incidents.'.format_map(
        locals())
    sentence_two = 'In total, {num_docs} documents contain at least one mention'.format_map(locals())
    sentence_three = 'Table \\ref{tab:typefreq} presents the mention frequency for each event type.'

    df = pandas.DataFrame(sorted(stats['#_type_freq'].items(),
                                 key=lambda x: x[1],
                                 reverse=True),
                          columns=['event type', 'annotation frequency']
                          )

    list_of_lists = []
    headers = ['eventtype', 'most common expressions']
    maximum = 10

    for eventtype in ['death', 'firing_a_gun',
                      'hitting', 'bag_of_events',
                      'injuring', 'other', 'generic', 'missing']:
        expr2freq = eventtype2expression_freq[eventtype]

        for order in [True, False]:
            counter = 0
            info = []
            one_row = []

            if not order:
                eventtype = ''

            for expr, freq in sorted(expr2freq.items(),
                                     key=operator.itemgetter(1),
                                     reverse=order):

                one_expr = '{expr} ({freq})'.format_map(locals())
                info.append(one_expr)

                counter += 1
                if counter == maximum:
                    break

            one_row = [eventtype, ' '.join(info)]

            list_of_lists.append(one_row)

    expr_df = pandas.DataFrame(list_of_lists, columns=headers)

    with open('cache/analysis.tex', 'w') as outfile:
        outfile.write(sentence_one + '\n')
        outfile.write(sentence_two + '\n')
        outfile.write(sentence_three + '\n')

        outfile.write(df.to_latex(index=False))

        outfile.write(expr_df.to_csv(index=False))
        outfile.write(expr_df.to_latex(index=False))

        mentions_div_docs = stats['#_mentions'] / stats['#_docs']
        mentions_div_clustsers = stats['#_mentions'] / stats['#_clusters']



        one_row = ['GVC',
                   'this publication',
                   str(stats['#_docs']),
                   str(stats['#_mentions']),
                   str(round(mentions_div_docs, 2)),
                   str(stats['#_clusters']),
                   str(round(mentions_div_clustsers, 2)),
                   'YES'
                   ]

        one_line = ' & '.join(one_row)
        outfile.write('\n' + one_line + ' \\\\' + '\n')


if __name__ == '__main__':

    # call functions
    debug_value = 1

    # reset directories
    input_folder = '/home/filten/LongTailQATask/QuestionCreation/gva_fr_bu_output'
    output_folder = 'corpses_corpus'
    setting = 'corpses_corpus' # corpses_corpus | semeval

    reset(input_folder, output_folder)

    # load disqualified docs
    disqualified_docs = load_disqualified_docs('resources/dis_areum_men.json',
                                               'resources/dis_ngan_men.json',
                                               debug=debug_value)

    # main loop
    all_added = set()

    # load mentions solutions proposed by Roxane
    delete, \
    old2new_eventtype, \
    manual_check = load_mappings_mentions2solution('resources/InputData_annotation_improvement.xlsx')

    input_path = '{input_folder}/system_input/docs.conll'.format_map(locals())
    cache_path = 'cache/conll.bin'
    subtask2conll,\
    token_id2token = load_conll(input_path,
                                cache_path,
                                overwrite=False,
                                debug=debug_value)
    total_num_docs = len(subtask2conll)

    anno_paths = [('areum', 'resources/ann_areum_men.json', 'output/vocab_areum.txt'),
                  ('ngan', 'resources/ann_ngan_men.json', 'output/vocab_ngan.txt')]

    input_annotations = dict()
    user2token_id2anno = dict()
    for user, input_path, output_path in anno_paths:

        user_annotations = json.load(open(input_path))
        input_annotations[user] = user_annotations

        token_id2anno, vocabulary, all_mwus = load_men_annotations(user_annotations,
                                                                   user,
                                                                   manual_check,
                                                                   token_id2token,
                                                                   delete,
                                                                   old2new_eventtype,
                                                                   disqualified_docs,
                                                                   debug=debug_value)

        user2token_id2anno[user] = token_id2anno

        with open('cache/%s.mw' % user , 'wb') as outfile:
            pickle.dump(all_mwus, outfile)

        save_vocab_to_file(vocabulary, output_path)

    # compute IAA
    accepted_incidents = {'578238', '492366', '571210', '512274', '501412',
                          '525119', '548991', '517905', '512877', '566863'}
    stats_output_path = 'output/iaa_week5.xlsx'

    IAA(token_id2token, input_annotations, accepted_incidents, stats_output_path)

    for subtask in [
                    's1',
                    's2',
                    's3'
                    ]:

        if debug_value:
            print()
            print('subtask', subtask)

        stats_input = get_q_stats_info(input_folder,
                                       output_folder,
                                       subtask,
                                       total_num_docs)

        stats_output_path = '{output_folder}/dev_data/{subtask}/stats.json'.format_map(locals())
        compute_stats(stats_input, output_path=None, debug=True)

        if subtask == 's1':
            added, \
            anno_stats, \
            eventtype2expression_freq = to_conll(output_folder,
                                                 subtask,
                                                 subtask2conll,
                                                 user2token_id2anno,
                                                 accepted_incidents,
                                                 setting)

            print(anno_stats)
            stats2latex(anno_stats, eventtype2expression_freq)


            all_added.update(added)
        else:
            command = 'cp {output_folder}/dev_data/s1/docs.conll {output_folder}/dev_data/{subtask}/docs.conll'.format_map(locals())
            try:
                subprocess.check_output(command, shell=True)
            except subprocess.CalledProcessError as e:
                print(e)



    missing = set(token_id2anno) - all_added
    print('added', len(all_added))
    print('missing', len(missing))
    print(missing)

    if debug_value:
        pass
        #print()
        #print('MW loose checking info')
        #mws_areum = pickle.load(open('cache/areum.mw', 'rb'))
        #mws_ngan = pickle.load(open('cache/ngan.mw', 'rb'))
        #mws_areum_not_in_mws_ngan = mwu.get_mw_mismatches(mws_areum, mws_ngan, debug=debug_value)
        #mws_ngan_not_in_mws_areum = mwu.get_mw_mismatches(mws_ngan, mws_areum, debug=debug_value)

    # create test data for participants (hence without gold data)
    commands = ['rm -rf {output_folder}_gold'.format_map(locals()),
                'cp -r {output_folder} {output_folder}_gold'.format_map(locals()),
                'rm -r {output_folder}/dev_data'.format_map(locals()),
                'cp resources/README.md {output_folder}'.format_map(locals()),
                'cp resources/README_gold.md {output_folder}_gold'.format_map(locals())]

    for command in commands:
        try:
            subprocess.check_output(command, shell=True)
        except subprocess.CalledProcessError as e:
            print(e)

