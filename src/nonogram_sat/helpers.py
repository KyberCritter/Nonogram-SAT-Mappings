
from itertools import groupby


def generate_clue(line):
    # https://stackoverflow.com/questions/34443946/count-consecutive-characters
    line_string = ""
    for i in line:
        line_string += str(int(i))
    groups = groupby(line_string)
    result = [(label, sum(1 for _ in group)) for label, group in groups]

    clue = [None] * len(result)

    for index, tuple in enumerate(result):
        if(tuple[0] == "1"):
            clue[index] = tuple[1]  # set clue to length of lines

    return [_ for _ in clue if _ is not None]
