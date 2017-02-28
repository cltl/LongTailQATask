class Candidate:
    """
    class containing a description of a question candidate
    """

    def __init__(self, confusion_factors,
                granularity, 
                sf, meanings, 
                num_answer_e=-1, 
                answer_incident_uris=[], 
                noise_incident_uris=[],
		oa_list=None,
                answer=-1, n2s_ratio=-1, 
                a_avg_num_sources=-1, 
                n_avg_num_sources=-1, 
                a_sources=[],
                n_sources=[],
                dct_spread=-1,
                qid=-1):
        self.confusion_factors=confusion_factors
        part=confusion_factors.index('participant') if 'participant' in confusion_factors else -1
        time=confusion_factors.index('time') if 'time' in confusion_factors else -1
        loc=confusion_factors.index('location') if 'location' in confusion_factors else -1
        self.question="How many events happened %s%s%s?" % ("in %s " % sf[time] if time>-1 else "", "in %s " % sf[loc] if loc>-1 else "", "that involve %s " % sf[part] if part>-1 else "")
        self.qid=qid
        self.answer=answer
        self.n2s_ratio=n2s_ratio
        self.oa_list=oa_list
        self.a_avg_num_sources=a_avg_num_sources
        self.n_avg_num_sources=n_avg_num_sources
        self.granularity=granularity 
        self.sf=sf 
        self.meanings=meanings 
        self.num_answer_e=num_answer_e 
        self.answer_incident_uris=answer_incident_uris 
        self.noise_incident_uris=noise_incident_uris
        self.a_sources=a_sources
        self.n_sources=n_sources
        self.dct_spread=dct_spread
