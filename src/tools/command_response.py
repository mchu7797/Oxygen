COMMAND_STATUS_RESPONSE = '''
{chart_title}[{gauge_difficulty}}:
Status: {status}{grade}
{judge_string}
{rank_string}
'''
COMMAND_STATUS_JUDGE_STRING = "Judge: C{cool}, G{good}, B{bad}, M{miss}, CO{max_combo}"
COMMAND_STATUS_RANK_STRING = "Rank: #{rank}"


def make_status_response(
        chart_title,
        gauge_difficulty,
        status,
        grade=None,
        judge=None,
        rank=None
):
    if judge is None:
        judge_string = ''
    else:
        judge_string = COMMAND_STATUS_JUDGE_STRING.format(
            cool=judge['cool'],
            good=judge['good'],
            bad=judge['bad'],
            miss=judge['miss'],
            max_combo=judge['combo'],
        )

    if rank is None:
        rank_string = ''
    else:
        rank_string = COMMAND_STATUS_RANK_STRING.format(rank=rank)

    return COMMAND_STATUS_RESPONSE.format(
        chart_title=chart_title,
        gauge_difficulty=gauge_difficulty,
        status=status,
        grade='' if grade is None else grade,
        judge_string=judge_string,
        rank_string=rank_string
    )
