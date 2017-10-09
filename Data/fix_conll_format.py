import os 
from glob import glob
from collections import defaultdict
from datetime import datetime

def fix_conll(input_path, debug=False):
    """
    fix conll files wrt
    1. token identifiers of title and first sentence of BODY were the same
    2. reset token identifier at zero at the start of each sentence
    
    NOTE: input path is overwritten
    """
    num_output_lines = 0
    num_docs = 0
    unique_ids = defaultdict(int)
    one_time_reset = True

    with open(input_path) as infile:
        lines = infile.readlines()

        with open(input_path, 'w') as outfile:

            for line in lines:

                # set default value for output value
                output_line = None

                # reset counters at start of document
                if line.startswith('#begin document'):
                    prev_sent_id = 1
                    output_line = line
                    num_docs += 1

                elif line.startswith('#end document'):
                    output_line = line
                    
                elif 'DCT' in line:
                    output_line = line
                    identifier, token, dsc, anno = line.strip().split('\t')
                    unique_ids[identifier] += 1

                else:
                    identifier, token, dsc, anno = line.strip().split('\t')
                    
                    if all([debug,
                            anno != '-']):
                        print(anno)
                        
                    doc_id, sent_id, old_token_id = identifier.split('.')

                    # reset token_id to 0
                    if all([dsc == 'BODY',
                            one_time_reset]):
                         token_id = 0
                         one_time_reset = False
                    elif prev_sent_id != sent_id:
                        token_id = 0
                    else:
                        token_id += 1

                    prev_sent_id = sent_id

                    if dsc == 'BODY':
                          output_sent_id = 'b%s' % sent_id
                    elif dsc == 'TITLE':
                          output_sent_id = 't%s' % sent_id
                    else:
                        raise ValueError('line without # or DCT or TITLE or BODY: %s' % line)
                          
                    new_identifier = '.'.join([doc_id, output_sent_id, str(token_id)])
                    output_line = '\t'.join([new_identifier, token, dsc, anno]) + '\n'
                    unique_ids[new_identifier] += 1
                    

                if output_line is None:
                    raise ValueError('no output line created: %s' % line) 

                outfile.write(output_line)
                num_output_lines += 1

        for unique_id, freq in unique_ids.items():
            if freq >= 2:
                raise AssertionError('id occurs more than once %s freq %s' % (unique_id, freq))
                
        new_num_lines = len(unique_ids) + (num_docs * 2)
        assert len(lines) == num_output_lines, 'not equal inlines and outlines: %s vs %s' % (len(lines), num_output_lines)
        assert len(lines) == new_num_lines, 'not equal lines based on ids: old_num_lines %s num_output_lines %s ids %s num_docs %s' % (len(lines), num_output_lines, len(unique_ids), num_docs)

count = 1
for folder in ['dev_data', 'input']:
    for subtask in ['s1', 's2', 's3']:
        folder_path = os.path.join('trial_data_v2', folder, subtask, 'CONLL')
        if os.path.exists(folder_path):
            for input_path in glob(folder_path + '/*.conll'):
                print(count, datetime.now(), input_path)
                fix_conll(input_path, debug=True)

                count += 1
        else:
            print('folder path does not exist: %s' % folder_path)
