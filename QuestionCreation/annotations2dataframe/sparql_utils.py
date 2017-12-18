from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("http://dbpedia.org/sparql")


def get_json_results(sparql_query):
    """
    perform sparql query to dbpedia
    and return json

    :rtype: dict
    :return: json results
    """
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    return results

sparql_query = """
SELECT DISTINCT ?relation ?property
    WHERE {
            <%s> ?relation ?property .
    }
    """


def is_it_a_city(location, debug=False):
    """
    check if location is a city according to dbpedia

    :param str location: starts with https://en.wikipedia.org/wiki/

    :rtype: bool
    :return: True if a city, else False
    """
    dbpedia_link_city = location.replace('https://en.wikipedia.org/wiki/',
                                         'http://dbpedia.org/resource/')

    results = get_json_results(sparql_query % dbpedia_link_city)
    is_city = False

    for result in results["results"]["bindings"]:

        relation = result['relation']['value']
        value = result['property']['value']

        if all([relation == 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type',
                value == 'http://dbpedia.org/ontology/City']):
            is_city = True

        if value in {'http://dbpedia.org/resource/Salem,_Oregon'}:
            is_city = True

    if is_city:
        locations = {'city': dbpedia_link_city}
        if debug:
            print('is a city', dbpedia_link_city)
    else:
        if debug:
            print('not a city', dbpedia_link_city)

    return is_city, dbpedia_link_city




def is_it_a_state(location, debug=False):
    """
    check if location is a state according to dbpedia

    :param str location: starts with https://en.wikipedia.org/wiki/

    :rtype: bool
    :return: True if a city, else False
    """
    dbpedia_link_state = location.replace('https://en.wikipedia.org/wiki/',
                                          'http://dbpedia.org/resource/')

    results = get_json_results(sparql_query % dbpedia_link_state)
    is_state = False

    for result in results["results"]["bindings"]:

        relation = result['relation']['value']
        value = result['property']['value']

        if all([relation == 'http://purl.org/dc/terms/subject',
                value == 'http://dbpedia.org/resource/Category:States_of_the_United_States']):
            is_state = True

    if is_state:
        if debug:
            print('is a state', dbpedia_link_state)
    else:
        if debug:
            print('not a state', dbpedia_link_state)

    return is_state, dbpedia_link_state





def retrieve_state_of_city(city):
    """
    retrieve state of city
    """
    dbpedia_link_city = city.replace('https://en.wikipedia.org/wiki/',
                                     'http://dbpedia.org/resource/')

    results = get_json_results(sparql_query % dbpedia_link_city)
    state = None

    for result in results["results"]["bindings"]:

        relation = result['relation']['value']
        value = result['property']['value']

        if relation == 'http://dbpedia.org/ontology/isPartOf':
            cand_is_state, cand_state = is_it_a_state(value)

            if cand_is_state:
                state = cand_state

    return state

def key_locations(location):
    """

    :param str location:
    :return:
    """
    locations = {'city': '',
                 'state': ''}

    is_city, city = is_it_a_city(location)
    is_state, state = is_it_a_state(location)

    if is_state:
        locations['state'] = state

    elif is_city:
        locations['city'] = city
        state = retrieve_state_of_city(city)
        if state:
            locations['state'] = state

    return locations


def get_label(resource, debug=False):
    """
    get label of resource.

    if no label -> report
    if multiple labels -> report + choose one

    :param str resource: e.g. http://dbpedia.org/resource/Los_Angeles

    :rtype: str
    :return: label (or '')
    """
    sparql_query = """
    SELECT DISTINCT ?value
        WHERE {
                <%s> <http://www.w3.org/2000/01/rdf-schema#label> ?value .
        }
        """

    the_query = sparql_query % resource
    results = get_json_results(the_query)

    candidates = set()
    for result in results["results"]["bindings"]:
        if result['value']['xml:lang'] == 'en':
            label = result['value']['value']
            candidates.add(label)

    if candidates:
        if len(candidates) >= 2:
            if debug:
                print('more than one candidate for %s: %s' % (resource,
                                                              candidates))

        label = candidates.pop()

    else:
        label = None

        if debug:
            print('no candidates for %s' % resource)

    if ',' in label:
        label = label.split(',')[0]

    if '(' in label:
        label = label.split('(')[0]

    return label


assert get_label('http://dbpedia.org/resource/Salem,_Oregon') == 'Salem'
assert get_label('http://dbpedia.org/resource/Los_Angeles') == 'Los Angeles'

assert is_it_a_city('https://en.wikipedia.org/wiki/Los_Angeles', debug=False)[0]
assert not is_it_a_city('http://dbpedia.org/resource/California', debug=False)[0]
assert not is_it_a_state('https://en.wikipedia.org/wiki/Los_Angeles', debug=False)[0]
assert is_it_a_state('http://dbpedia.org/resource/California', debug=False)[0]
assert retrieve_state_of_city('https://en.wikipedia.org/wiki/Los_Angeles') == 'http://dbpedia.org/resource/California'
