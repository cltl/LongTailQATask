import json

from collections import defaultdict
from datetime import datetime

def get_dict_iterable(the_dict, keys, debug=False):
    """

    :param dict the_dict: a dict
    :param list keys: list of keys each index represents a nesting layer


    :rtype: list
    :return: list of tuples (q_id, value)
    """
    iterable = []

    output = defaultdict(int)

    key1, *other_keys = keys
    num_keys = len(keys)

    if num_keys == 2:
        key2 = other_keys[0]

    for q_id, value in the_dict.items():

        strategy = 'out'

        if key1 in value:

            if num_keys == 1:
                the_value = value[key1]
                iterable.append((q_id, the_value))
                strategy = 'in'

            elif num_keys == 2:
                if key2 in value[key1]:
                    the_value = value[key1][key2]
                    iterable.append((q_id, the_value))
                    strategy = 'in'

            # check combinations of confusion and granularities
            if num_keys == 2:

                the_key = list(value[key1].keys())[0]

                if key1 == 'location':
                    assert the_key in {'city', 'state'}
                elif key1 == 'time':
                    assert the_key in {'day', 'month', 'year'}
                elif key1 == 'participant':
                    assert the_key in {'first', 'last', 'full_name'}


        output[strategy] += 1

    if debug:
        values = [value for q_id, value in iterable]
        print()
        print('keys:', keys)
        print('distribution', dict(output))
        print('# empty strings', values.count(''))
        print('# None', values.count(None))

    return sorted(iterable)


a_dict = {'1' : {'a': 'b'},
          '2' : {'a': 'c'}}
assert get_dict_iterable(a_dict, ['a']) == [('1', 'b'), ('2','c')]


def time_check(time_string, granularity):
    """
    given a time string and in a granularity, check if:
    a) can be parsed by datetime

    :raise AssertionError if not a and b

    :param str time_string: '2006' | '11/2006' | '01/11/2006'
    :param str granularity: day month year
    """
    if granularity == 'day':
        dt_obj = datetime.strptime(time_string, '%d/%m/%Y')

    elif granularity == 'month':
        dt_obj = datetime.strptime(time_string, '%m/%Y')

    if granularity == 'year':
        dt_obj = datetime.strptime(time_string, '%Y')


    assert type(dt_obj) == datetime

def loc_check(loc_string):
    """
    check if loc_string is:
    a) a dbpedia link

    :param str loc_string: a dbpedia link
    """
    assert loc_string.startswith('http://dbpedia.org/resource')

def part_check(part_string, granularity):
    """
    check if part_string:
    a) has one part for first and last
    b) has two parts for full_name

    :param str part_string: name of a person
    :param granularity: first | last | full_name
    """

    name_parts = part_string.split()

    if granularity in {'first', 'last'}:
        assert len(name_parts) == 1
    elif granularity  == 'full_name':
        assert len(name_parts) == 2




