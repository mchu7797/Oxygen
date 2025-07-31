COMMAND_STATUS_RESPONSE_EXAMPLE = """
Status : D Failed #62   ············ 89%
Max Combo : 1900
Cool : 4000, Good : 1000, Bad : 11, Miss 189
"""

COMMAND_STATUS_RESPONSE = """
Status: {grade} {status} {rank} {progress} {judge_string}
"""
COMMAND_STATUS_JUDGE_STRING = """
Max Combo: {max_combo}
Cool: {cool}, Good: {good}, Bad: {bad}, Miss: {miss}
"""


def make_status_response(status, progress=None, grade=None, judge=None, rank=None):
    if judge is None:
        judge_string = ""
    else:
        judge_string = COMMAND_STATUS_JUDGE_STRING.format(
            cool=judge["cool"],
            good=judge["good"],
            bad=judge["bad"],
            miss=judge["miss"],
            max_combo=judge["combo"],
        )

    return COMMAND_STATUS_RESPONSE.format(
        status=status,
        progress="" if progress is None else f"{'.' * 14} {progress}%",
        grade="" if grade is None else grade,
        judge_string=judge_string,
        rank="" if rank is None else f"#{rank}",
    )


if __name__ == "__main__":
    print(
        make_status_response(
            grade="D",
            status="Failed",
            progress=89,
            rank=62,
            judge={"cool": 4000, "good": 1000, "bad": 11, "miss": 189, "combo": 1900},
        )
    )
