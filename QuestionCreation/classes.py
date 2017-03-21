import json
import metrics
from datetime import datetime
from statistics import mean
from glob import glob


def sources_date_spread(set_of_uris):
    """

    :param set_of_uris:
    :return:
    """
    date_spreads = []
    for incident_uri in set_of_uris:
        dates = set()
        path = '../EventRegistries/GunViolence/the_violent_corpus/%s/*.json' % incident_uri
        for json_file in glob(path):
            document = json.load(open(json_file))
            try:
                dates.add(datetime.strptime(document['dct'], '%a, %d %b %Y %H:%M:%S GMT'))
            except ValueError:  # NODATE documents
                pass
        date_spreads.append(metrics.get_dct_spread(dates))

    mean_date_spreads = -1
    if date_spreads:
        mean_date_spreads = mean(date_spreads)

    return mean_date_spreads

def get_sources(dataframe):
    """

    :param dataframe:
    :return:
    """
    sources = set()
    for index, row in dataframe.iterrows():
        sources.add(row['source_url'])
        sources.update(row['incident_sources'])
    return sources


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
    def c_sources(self):
        return get_sources(self.confusion_df)

    @property
    def c_avg_num_sources(self):
        if self.confusion_incident_uris:
            return len(self.c_sources) / len(self.confusion_incident_uris)
        else:
            return 0

    #@property
    #def a_avg_date_spread(self):
    #    return sources_date_spread(self.answer_incident_uris)

    #@property
    #def c_avg_date_spread(self):
    #    return sources_date_spread(self.confusion_incident_uris)

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

    def debug(self):
        for prop in dir(Question):
            if isinstance(getattr(Question, prop), property):
                getattr(self, prop)

