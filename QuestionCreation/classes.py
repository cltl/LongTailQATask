import metrics
import datetime
import pickle
import hashlib
import spacy_to_naf
from lxml import etree
from spacy.en import English
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


def text2conll(output_path, doc_id, text):
    """
    use spacy to output text (tokenized) in conll

    :param str output_folder: output folder
    :param str doc_id: document identifier
    :param str text: content (either title or context of news article)
    """
    doc = spacy_to_naf.text_to_NAF(text, nlp)

    with open(output_path, 'w') as outfile:
        for wf_el in doc.xpath('text/wf'):
            sent_id = wf_el.get('sent')
            token_id = wf_el.get('id')
            id_ = f'd{doc_id}.s{sent_id}.{token_id}'

            info = [id_, wf_el.get('offset'), wf_el.get('length')]
            outfile.write('\t'.join(info) + '\n')


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
                 answer,
                 oa_info,
                 answer_df,
                 answer_incident_uris,
                 confusion_df,
                 confusion_incident_uris):
        self.q_id = q_id
        self.confusion_factors = confusion_factors
        self.granularity = granularity
        self.sf = sf
        self.meanings = meanings
        self.gold_loc_meaning = gold_loc_meaning
        self.answer = answer
        self.oa_info = oa_info
        self.answer_df = answer_df
        self.answer_incident_uris = answer_incident_uris
        self.confusion_df = confusion_df
        self.confusion_incident_uris = confusion_incident_uris

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

    @property
    def question(self):
        time_chunk = ''
        location_chunk = ''
        participant_chunk = ''
        event_type = 'killing AND injuring'

        for index, (confusion_factor, a_sf) in enumerate(zip(self.confusion_factors,
                                                             self.sf)):
            if confusion_factor == 'time':
                time_chunk = 'in %s (%s) ' % (self.sf[index], self.granularity[index])
            elif confusion_factor == 'location':
                location_chunk = 'in %s (%s) ' % (self.gold_loc_meaning, self.granularity[index])
            elif confusion_factor == 'participant':
                participant_chunk = 'that involve the name %s (%s) ' % (self.sf[index], self.granularity[index])

        the_question = 'How many {event_type} events happened {time_chunk}{location_chunk}{participant_chunk}?'.format_map(locals())
        return the_question.strip()

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
        return metrics.get_dct_spread(sources_dcts)

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

    def to_conll(self, a_df, output_folder, debug=False):
        """
        given a pandas dataframe, convert articles to conll

        :param pandas.core.frame.DataFrame a_df: 
        :param str output_folder: the output folder
        """
        news_article_template = '../EventRegistries/GunViolenceArchive/the_violent_corpus/{incident_uri}/{the_hash}.json'
        path_doc_id2article = f'{output_folder}/pre/doc_id2article_url.json'

        if not os.path.exists(path_doc_id2article):
            doc_id2article = dict()
        else:
            doc_id2article = json.load(open(path_doc_id2article))


        for index, row in a_df.iterrows():

            # load news sources
            news_article_objs = set()
            for source_url in row['incident_sources']:
                hash_obj = hashlib.md5(source_url.encode())
                the_hash = hash_obj.hexdigest()
                incident_uri = row['incident_uri']

                path = news_article_template.format_map(locals())

                try:
                    with open(path, 'rb') as infile:
                        news_article_obj = pickle.load(infile)
                        news_article_objs.add(news_article_obj)

                        phase = 'pre'
                        doc_id = the_hash

                        content_type = 'body'
                        output_path = f'{output_folder}/{phase}/{doc_id}.{content_type}.conll'
                        text2conll(output_path, the_hash, news_article_obj.content)

                        content_type = 'title'
                        output_path = f'{output_folder}/{phase}/{doc_id}.{content_type}.conll'
                        text2conll(output_path, the_hash, news_article_obj.title)

                        content_type = 'dct'
                        phase = 'post'
                        output_path = f'{output_folder}/{phase}/{doc_id}.{content_type}.conll'
                        with open(output_path, 'w') as outfile:
                            outfile.write(str(news_article_obj.dct))

                        doc_id2article[the_hash] = source_url

                        hash_obj = hashlib.md5(news_article_obj.content.encode())
                        content_hash = hash_obj.hexdigest()

                        hash_obj = hashlib.md5(news_article_obj.title.encode())
                        title_hash = hash_obj.hexdigest()

                        content_type = 'checksum'
                        phase = 'pre'
                        output_path = f'{output_folder}/{phase}/{doc_id}.{content_type}.conll'

                        checksum_info = {'title': title_hash,
                                         'body': content_hash}

                        with open(output_path, 'w') as outfile:
                            json.dump(checksum_info, outfile)


                        if debug:
                            break

                except FileNotFoundError:
                    continue

        with open(path_doc_id2article, 'w') as outfile:
            json.dump(doc_id2article, outfile)


    def set_all_attributes(self):
        vars(self)


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
