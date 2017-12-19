from collections import defaultdict


def get_mw_mismatches(mws_user1, mws_user2, debug=False):
    """

    """
    strategy2freq = defaultdict(int)

    for mw_user1 in mws_user1:

        strategy = 'mismatch'

        for mw_user2 in mws_user2:

            if not any([len(mw_user1) >= 2,
                        len(mw_user2) >= 2]):
                continue

            overlap = set(mw_user1) & set(mw_user2)

            if mw_user1 == mw_user2:
                strategy = 'exact_match'
            elif overlap:
                strategy = 'partial_match'

                if debug >= 2:
                    print()
                    print(mw_user1)
                    print(mw_user2)

        strategy2freq[strategy] += 1

    if debug:
        print()
        print('# mwus', len(mws_user1))
        print('distribution', dict(strategy2freq))