"""
Definitions:
1. answer event: event that is part of the answer to a question
2. noise event: event that is NOT part of the answer to a question

Which metrics are relevant for which category:
1. get_ratio___noise_e2answer_e
    * Time
    * Location
    * Participant

2. get_observed_ambiguity
    * Time
    * Location
    * Participant

3. get_num_docs_per_event
    * [?] Time
    * Meta

4. get_dct_spread
    * Time
"""


def get_ratio___noise_e2answer_e(noise_e, answer_e):
    """
    compute ratio between noise events and answer events,
    e.g. noise_e / answer_e

    if answer_e is an empty set, the function will return 0
    if there is an overlap between noise_e and answer_e, an Exception will be raise

    :param set noise_e: set of noise event identifiers
    :param set answer_e: set of answer event identifiers

    :rtype: float
    :return: ratio between noise events and answer events
    """
    overlap = noise_e & answer_e
    if overlap:
        raise Exception('overlap between noise_e and answer_e: %s' % overlap)

    ratio_noise2answer = 0
    if answer_e:
        ratio_noise2answer = len(noise_e) / len(answer_e)

    return ratio_noise2answer


def get_observed_ambiguity(meanings):
    """
    compute number of unique answer meanings

    :param set sf2meanings: set of answer surface forms with meanings

    :rtype: int
    :return: number of unique answer meanings
    """
    return len(meanings)


def get_num_docs_per_event(answer_d, answer_e):
    """
    compute number average number of documents per answer event

    :param set answer_d: set of document identifiers
    :param set answer_e: set of answer event identifiers

    if answer_e is an empty set, the function will return 0

    :rtype: float
    :return: average number of documents per answer event
    """
    num_docs_per_event = 0

    if answer_e:
        num_docs_per_event = len(answer_d) / len(answer_e)

    return num_docs_per_event


def get_dct_spread(dcts):
    """
    computes number of days between the earliest and latest document creation time

    :param set dcts: set of datetime.datetime objects, e.g. example of one object is
    datetime.datetime(2016, 10, 1) representing 1st of October 2016

    :rtype: int
    :return: number of days between the earliest and latest document creation time
    """
    dct_spread = 0

    if dcts:
        earliest_dct = min(dcts)
        latest_dct = max(dcts)
        diff = latest_dct - earliest_dct
        dct_spread = diff.days

    return dct_spread




