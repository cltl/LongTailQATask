import subprocess

# output_folder
out_dir = 'GunViolenceCorpus'

# input file
input_path = 'corpses_corpus_gold/dev_data/s1/docs.conll'
verbose_path = '{out_dir}/verbose.conll'.format_map(locals())
system_input_path = '{out_dir}/system_input.conll'.format_map(locals())
gold_path = '{out_dir}/gold.conll'.format_map(locals())

# create system input and gold
with open(input_path, 'r') as infile:

    system_file = open(system_input_path, 'w')
    gold_file = open(gold_path, 'w')
    verbose_file = open(verbose_path, 'w')

    for line in infile:

        if line.startswith('#'):
            system_file.write(line)
            gold_file.write(line)

        else:
            token_id, token, discourse, integer, verbose = line.strip().split('\t')

            for label, file in [('system', system_file),
                                ('gold', gold_file),
                                ('verbose', verbose_file)]:

                if label == 'system':
                    one_row = [token_id, token, discourse, '-']
                elif label == 'gold':
                    one_row = [token_id, token, discourse, integer]
                elif label == 'verbose':
                    one_row = [token_id, token, discourse, verbose, integer]

                file.write('\t'.join(one_row) + '\n')

    system_file.close()
    gold_file.close()
    verbose_file.close()



