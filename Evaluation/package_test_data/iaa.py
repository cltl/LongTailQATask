import pandas
from sklearn.metrics import cohen_kappa_score


def extract_info(user_annotations, identifier):
    """
    extract user annotation for eventtype and participants

    :param dict user_annotations: (inc_id, token_id) -> ann_info
    :param identifier: (inc_id, token_id)
    :return:
    """
    if identifier not in user_annotations:
        return [None, None]

    ann_info = user_annotations[identifier]
    user_export = []
    for key in ['eventtype', 'participants']:
        value = None
        if key in ann_info:
            value = ann_info[key]
        user_export.append(value)
    return user_export


class IAA:
    """
    class to compute Inter Annotator Agreement


    :cvar dict token_id2token: mapping token_id -> token
    :cvar dict annotations: mapping user -> dict containing annotations
    :cvar set accepted incidents: set of incidents for which the iaa will be computed

    """
    def __init__(self,
                 token_id2token,
                 input_annotations,
                 accepted_incidents,
                 stats_output_path):
        self.token_id2token = token_id2token
        self.annotations = self.restructure_annotations(input_annotations,
                                                         accepted_incidents,
                                                         debug=True)
        self.user1, self.anno_user1, \
        self.user2, self.anno_user2, \
        self.anno_df = self.combine_all_in_one_df()

        self.write_stats(stats_output_path)


    def restructure_annotations(self, input_annotations, accepted_incidents, debug=False):
        """
        convert mapping
        from inc_id -> inc_info
        to (inc_id, token_id) -> ann_info

        :param dict annotations: mapping user -> dict containing annotations
        :param set accepted incidents: set of incidents for which the iaa will be computed

        :rtype: dict
        :return: mapping from
        user
            -> (inc_id, token_id)
                -> ann_info
        """
        annotations = dict()

        for user, user_annotations in input_annotations.items():

            if debug:
                print()
                print('user', user)

            new_user_annotations = dict()
            for inc_id, inc_info in user_annotations.items():
                if inc_id in accepted_incidents:
                    for token_id, ann_info in inc_info.items():
                        new_user_annotations[(inc_id, token_id)] = ann_info

            annotations[user] = new_user_annotations

            if debug:
                overlap = accepted_incidents - set(user_annotations.keys())
                assert not overlap, 'these target incidents do not have annotations: %s' % overlap
                print('num annotations', len(new_user_annotations))

        return annotations


    def combine_all_in_one_df(self):
        """
        combine all information from
        a) cvar annotations
        b) cvar token_id2token

        while also comparing the annotations from the annotators

        :rtype:
        :return:
        """
        user1, user2 = self.annotations.keys()
        all_ids = set(self.annotations[user1].keys()) | set(self.annotations[user2].keys())

        annotations_user1 = []
        annotations_user2 = []

        headers = ['inc', 'token_id', 'token',
                   'both_annotated', 'Anno_match',
                   '%s_eventtype' % user1,
                   '%s_part' % user1,
                   '%s_eventtype' % user2,
                   '%s_part' % user2]
        list_of_lists = []
        counter = 0

        for (inc_id, token_id) in sorted(all_ids):

            export_user1 = extract_info(self.annotations[user1],
                                        (inc_id, token_id))

            export_user2 = extract_info(self.annotations[user2],
                                        (inc_id, token_id))

            match = False
            if any([export_user1,
                    export_user2]):
                if export_user1 == export_user2:
                    match = True

            id_match = all([(inc_id, token_id) in self.annotations[user1],
                            (inc_id, token_id) in self.annotations[user2]])

            export = [inc_id, token_id, self.token_id2token[token_id], id_match, match] + export_user1 + export_user2
            list_of_lists.append(export)

            if match:
                annotations_user1.append(counter)
                annotations_user2.append(counter)
                counter += 1
            else:
                annotations_user1.append(counter)
                counter += 1
                annotations_user2.append(counter)
                counter += 1

        anno_df = pandas.DataFrame(list_of_lists, columns=headers)

        return user1, annotations_user1, user2, annotations_user2, anno_df,

    def write_stats(self, output_path):
        """
        compute relevant iaa stats and write to excel file
        """
        user1 = self.annotations[self.user1]
        user2 = self.annotations[self.user2]

        num_annotations_piek = len(user1)
        num_annotations_roxane = len(user2)

        both_annotated = [row['Anno_match']
                          for index, row in self.anno_df.iterrows()
                          if row['both_annotated']]

        num_both_annotated = len(both_annotated)
        agreement = sum(both_annotated)
        kappa = cohen_kappa_score(self.anno_user1, self.anno_user2)

        headers = ['#_annotations_%s' % self.user1,
                   '#_annotations_%s' % self.user2,
                   '#_both_annotated',
                   '#_full_agreement',
                   'cohen_kappa']

        list_of_lists = [[num_annotations_piek, num_annotations_roxane, num_both_annotated, agreement, round(kappa, 2)]]
        stats_df = pandas.DataFrame(list_of_lists, columns=headers)
        stats_df.to_excel(output_path, sheet_name='stats')

        writer = pandas.ExcelWriter(output_path, engine='xlsxwriter')
        self.anno_df.to_excel(writer, sheet_name='annotations')
        stats_df.to_excel(writer, sheet_name='stats')
        writer.save()

