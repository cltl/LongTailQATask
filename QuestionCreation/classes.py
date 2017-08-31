import metrics
import datetime
import pickle
import hashlib
import spacy_to_naf
from lxml import etree
from spacy.en import English
from collections import defaultdict
import json
import os

nlp = English()

def get_sources(dataframe):
    """
    extract sources


    :param pandas.core.frame.DataFrame dataframe:

    :rtype: set
    :return: set of archive.org links
    """
    sources = set()
    for index, row in dataframe.iterrows():
        sources.update(row['incident_sources'].keys())
    return sources

def get_dcts(dataframe):
    """
    set of datetime objects

    :param pandas.core.frame.DataFrame dataframe:

    :rtype: list
    :return: list of datetime.date instances
    """
    dcts = []
    for index, row in dataframe.iterrows():
        for date in row['incident_sources'].values():
            if type(date) == datetime.date:
                dcts.append(date)

    dcts = [datetime.datetime(d.year, d.month, d.day)
            for d in dcts]

    return dcts


class Question:
    """
    represents one instance of a question
    with metrics valued computed
    """

    def __init__(self,
                 q_id,
                 confusion_factors,
                 granularity,
                 sf,
                 meanings,
                 gold_loc_meaning,
                 ev_answer,
                 oa_info,
                 answer_df,
                 answer_incident_uris,
                 confusion_df,
                 confusion_incident_uris,
                 subtask,
                 event_types,
                 types_and_rows=None):
        self.confusion_factors = confusion_factors
        self.granularity = granularity
        self.sf = sf
        self.meanings = meanings
        self.gold_loc_meaning = gold_loc_meaning
        self.ev_answer = ev_answer
        self.oa_info = oa_info
        self.answer_df = answer_df
        self.answer_incident_uris = answer_incident_uris
        self.confusion_df = confusion_df
        self.confusion_incident_uris = confusion_incident_uris
        self.to_include_in_task = True
        self.subtask=subtask
        self.event_types=event_types
        self.q_id = '%s-%s' % (self.subtask, q_id)
        self.types_and_rows=types_and_rows

        assert len(self.answer_incident_uris) >= 1, 'no answer incident uris'
        assert len(self.a_sources) >= 1, 'no answer sources'


    def get_question_score(self):
        """
        """
        if self.subtask in {1,2}:
            return self.ev_answer * self.a_avg_num_sources * self.a_avg_date_spread

        elif self.subtask == 3:
            return self.part_numerical_answer * self.a_avg_num_sources * self.a_avg_date_spread

    @property
    def participant_confusion(self):
        return 'participant' in self.confusion_factors

    @property
    def time_confusion(self):
        return 'time' in self.confusion_factors

    @property
    def location_confusion(self):
        return 'location' in self.confusion_factors

    @property
    def num_both_sf_overlap(self):
        return len(self.meanings)

    def question(self, debug=False):

        system_input = {'subtask': self.subtask,
                        'event_types': self.event_types}

        time_chunk = ''
        location_chunk = ''
        participant_chunk = ''
        event_type_dict = {'killing': 'killed',
                           'injuring': 'injured'}

        for index, (confusion_factor, a_sf) in enumerate(zip(self.confusion_factors,
                                                             self.sf)):
            if confusion_factor == 'time':
                time_chunk = 'in %s (%s) ' % (self.sf[index], self.granularity[index])
                system_input['time'] = {self.granularity[index]: self.sf[index]}
            elif confusion_factor == 'location':
                location_chunk = 'in %s (%s) ' % (self.gold_loc_meaning, self.granularity[index])
                gran_level = self.granularity[index]
                all_dbpedia_links = {row['locations'][gran_level]
                                     for index, row in self.answer_df.iterrows()
                                     if gran_level in row['locations']}

                if len(all_dbpedia_links) == 1:
                    the_dbpedia_link = all_dbpedia_links.pop()
                    system_input['location'] = {gran_level: the_dbpedia_link}
                else:
                    print('multiple or no dbpedia options for %s: %s' % (self.q_id, all_dbpedia_links))
                    system_input['location'] = (None, None)
                    self.to_include_in_task = False

            elif confusion_factor == 'participant':
                participant_chunk = 'that involve the name %s (%s) ' % (self.sf[index], self.granularity[index])
                system_input['participant'] = {self.granularity[index]: self.sf[index]}

        if self.subtask==1:
            the_question = 'Which {self.event_types} event happened {time_chunk}{location_chunk}{participant_chunk}?'.format_map(locals())
        elif self.subtask==2:
            the_question = 'How many {self.event_types} events happened {time_chunk}{location_chunk}{participant_chunk}?'.format_map(locals())
        elif self.subtask==3:
            event_types_label = ' OR '.join([event_type_dict[event_type]
                                            for event_type in self.event_types])
            the_question = 'How many people were {event_types_label} {time_chunk}{location_chunk}{participant_chunk}?'.format_map(locals())

        if debug:
            print(the_question)

        self.verbose_question = the_question.strip()

        if self.to_include_in_task:
            system_input['verbose_question'] = self.verbose_question
            return system_input
        else:
            return None

    @property
    def c2s_ratio(self):
        confusion_e = self.confusion_incident_uris
        answer_e = self.answer_incident_uris
        return metrics.get_ratio___confusion_e2answer_e(confusion_e,
                                                        answer_e)

    @property
    def a_sources(self):
        return get_sources(self.answer_df)

    @property
    def a_avg_num_sources(self):
        return len(self.a_sources) / len(self.answer_incident_uris)

    @property
    def num_a_sources(self):
        return len(self.a_sources)

    @property
    def c_sources(self):
        return get_sources(self.confusion_df)

    @property
    def num_c_sources(self):
        return len(self.c_sources)

    @property
    def c_avg_num_sources(self):
        if self.confusion_incident_uris:
            return len(self.c_sources) / len(self.confusion_incident_uris)
        else:
            return 0

    @property
    def a_avg_date_spread(self):
        sources_dcts = get_dcts(self.answer_df)
        metric_value = metrics.get_dct_spread(sources_dcts)
        if not metric_value:
            return 1
        else:
            return metric_value

    @property
    def c_avg_date_spread(self):
        confusion_dcts = get_dcts(self.confusion_df)
        return metrics.get_dct_spread(confusion_dcts)

    def oa(self, confusion_factor):
        try:
            confusion_index = self.confusion_factors.index(confusion_factor)
        except ValueError:
            return 0

        return len({meaning[confusion_index]
                            for meaning in self.meanings})

    @property
    def loc_oa(self):
        return self.oa('location')

    @property
    def time_oa(self):
        return self.oa('time')

    @property
    def gvdb_annotations(self):
        gvdb_objects = set()
        for index, row in self.answer_df.iterrows():
            if row['gvdb_annotation']:
                for archive_org_link, gvdb_annotation in row['gvdb_annotation'].items():
                    gvdb_instance = GVDB(gvdb_annotation)
                    gvdb_objects.add(gvdb_instance)

        return gvdb_objects

    @property
    def num_gvdb_part_annotations(self):
        total = 0
        for gvdb_instance in self.gvdb_annotations:
            total += gvdb_instance.num_victim_annotations
            total += gvdb_instance.num_shooter_annotations

        return total


    def generate_answer_info(self, type_and_row, doc_id2conll, debug=False):
        """
        create one conll file per question, which serves as input file
        for task participants

        :param list type_and_row: list of tuples ('gold' | 'confusion', df row)
        :param dict doc_id2conll: source url -> conll output
        :param bool debug: set to True for debugging
        """
        all_doc_ids = defaultdict(list)
        parts_info = dict()

        self.types_and_rows=type_and_row

        for a_type, a_row in type_and_row:
            for source_url in a_row['incident_sources']:

                if source_url not in doc_id2conll:
                    continue

                if a_type == 'gold':
                    incident_uri = a_row['incident_uri']
                    hash_obj = hashlib.md5(source_url.encode())
                    the_hash = hash_obj.hexdigest()
                    all_doc_ids[incident_uri].append(the_hash)

                    parts_info[incident_uri] = {'num_killed': a_row['num_killed'],
                                                'num_injured': a_row['num_injured'] }

        # validate
        the_question = self.question()

        self.numerical_answer = len(all_doc_ids)

        # min num of answers need
        needed_answers = 1
        if self.subtask == 2:
            needed_answers = 2

        # validate
        if the_question is None:
            self.to_include_in_task = False

        if self.subtask in {1,2}:
            if self.numerical_answer < needed_answers:
                self.to_include_in_task = False

            self.answer_info = {'numerical_answer': self.numerical_answer,
                                'answer_docs': all_doc_ids}

        if self.subtask == 3:
            self.part_numerical_answer = 0

            if 'killing' in self.event_types:
                self.part_numerical_answer += sum([part_info['num_killed']
                                              for part_info in parts_info.values()])
            if 'injuring' in self.event_types:
                self.part_numerical_answer += sum([part_info['num_injured']
                                              for part_info in parts_info.values()])

            self.answer_info = {'numerical_answer': self.part_numerical_answer,
                                'answer_docs': all_doc_ids,
                                'part_info' : parts_info}

class GVDB:
    """
    compute stats about gun violence database annotation
    """

    def __init__(self, gvdb_info):
        self.gvdb_info = gvdb_info

    @property
    def city(self):
        value = self.gvdb_info['date-and-time']['city']['value']
        city = None
        if value:
            city = value

        return city

    @property
    def date(self):
        value = self.gvdb_info['date-and-time']['date']

        date = None
        if value:
            date = datetime.datetime.strptime(value, '%Y-%m-%d')

        return date

    @property
    def state(self):
        value = self.gvdb_info['date-and-time']['state']

        state = None
        if value:
            state = value

        return state

    def num_part_annotations(self, key):
        num_annotations = 0
        for victim_annotation in self.gvdb_info[key]:

            for category, annotation in victim_annotation.items():
                if type(annotation) == dict:
                    if annotation['startIndex'] != -1:
                        num_annotations += 1

        return num_annotations

    @property
    def num_victim_annotations(self):
        return self.num_part_annotations('victim-section')

    @property
    def num_shooter_annotations(self):
        return self.num_part_annotations('shooter-section')


class NewsItem:

    def __init__(self, title='',
                 content='',
                 dct='', id=None,
                 uri=''):
        self.title=title
        self.content=content
        self.dct=dct
        self.id=id
        self.uri=uri

    def toJSON(self, targetFile):
        pickle.dump(self, open(targetFile, 'wb'))
