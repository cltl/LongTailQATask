from collections import defaultdict




def clean_annotation(annotation):
    """
    clean brackets from annotation

    :param str annotation: (INT | INT) | (INT)

    :rtype: str
    :return: string without brackets
    """
    table = {ord('('): '',
             ord(')'): ''}

    cleaned = annotation.translate(table)

    return cleaned

assert clean_annotation('(1)') == '1'
assert clean_annotation('(1') == '1'
assert clean_annotation('1)') == '1'
assert clean_annotation('1') == '1'


input_path = 'test_data_gold/dev_data/s1/docs.conll'

id_2mentions = defaultdict(set)
mention_parts = []
doc_ids = set()

with open(input_path) as infile:
    for line in infile:

        if any([line.startswith('#'),
                '.DCT\t' in line]):
            continue

        full_id, token, discourse, anno = line.strip().split('\t')
        doc_id, sent_id, t_id = full_id.split('.')


        if anno != '-':
            doc_ids.add(doc_id)

            id_ = clean_annotation(anno)

            if all([anno.startswith('('),
                    anno.endswith(')')]):
                the_mention_as_string = token
                id_2mentions[id_].add(the_mention_as_string)

            # start
            elif anno.startswith('('):
                mention_parts.append(token)

            # middle part
            elif anno == id_:
                mention_parts.append(token)

            # end
            elif anno.endswith(')'):
                mention_parts.append(token)
                the_mention_as_string = ' '.join(mention_parts)
                id_2mentions[id_].add(the_mention_as_string)
                mention_parts = []



with open('output/reference_sets.tsv', 'w') as outfile:

    headers = ['instance_id', 'reference_set']
    outfile.write('\t'.join(headers) + '\n')

    for key, value in id_2mentions.items():

        one_row = key + '\t' + '\t'.join(value)
        outfile.write(one_row + '\n')

print('num docs with annotation in test data: %s' % len(doc_ids))
