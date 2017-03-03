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
                 answer,
                 oa_info,
                 answer_df,
                 answer_incident_uris,
                 noise_df,
                 noise_incident_uris):
        self.q_id = q_id
        self.confusion_factors = confusion_factors
        self.granularity = granularity
        self.sf = sf
        self.meanings = meanings
        self.answer = answer
        self.oa_info = oa_info
        self.answer_df = answer_df
        self.answer_incident_uris = answer_incident_uris
        self.noise_df = noise_df
        self.noise_incident_uris = noise_incident_uris

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
    def question(self):
        time_chunk = ''
        location_chunk = ''
        participant_chunk = ''

        for index, (confusion_factor, a_sf) in enumerate(zip(self.confusion_factors,
                                                             self.sf)):
            if confusion_factor == 'time':
                time_chunk = 'in %s ' % self.sf[index]
            elif confusion_factor == 'location':
                location_chunk = 'in %s ' % self.sf[index]
            elif confusion_factor == 'participant':
                participant_chunk = 'that involve %s ' % self.sf[index]

        the_question = 'How many events happened {time_chunk}{location_chunk}{participant_chunk}?'.format_map(locals())
        return the_question

    @property
    def n2s_ratio(self):
        noise_e = self.noise_incident_uris
        answer_e = self.answer_incident_uris
        return metrics.get_ratio___noise_e2answer_e(noise_e,
                                                    answer_e)

    @property
    def a_sources(self):
        return get_sources(self.answer_df)

    @property
    def a_avg_num_sources(self):
        return len(self.a_sources) / len(self.answer_incident_uris)

    @property
    def n_sources(self):
        return get_sources(self.noise_df)

    @property
    def n_avg_num_sources(self):
        if self.noise_incident_uris:
            return len(self.n_sources) / len(self.noise_incident_uris)
        else:
            return 0

    @property
    def a_avg_date_spread(self):
        return sources_date_spread(self.answer_incident_uris)

    @property
    def n_avg_date_spread(self):
        return sources_date_spread(self.noise_incident_uris)
    
    def debug(self):
        for prop in dir(Question):
            if isinstance(getattr(Question, prop), property):
                getattr(self, prop)

