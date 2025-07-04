# Scott Ratchford 2025.07.03

import numpy as np

from .sat import (
    SAT, return_all_sat_solutions, brute_force_sat,
)
from .nonogram import (
    Nonogram, Marking,
)
from .helpers import (
    generate_clue,
)

def sat_to_clue_sets(sat: SAT, allowDuplicates=True) -> list:
    solutions = return_all_sat_solutions(sat)
    clueSets = []
    for solution in solutions:
        tempClue = generate_clue(solution)
        if(allowDuplicates):
            clueSets.append(tempClue)
        else:
            if(not tempClue in clueSets):
                clueSets.append(tempClue)
    return clueSets

def sat_to_key_sets(sat: SAT) -> list[list[Marking]]:
    solutions = return_all_sat_solutions(sat)
    key_sets = []
    for solution in solutions:
        key_sets.append([Marking(x) for x in solution])
    return key_sets

def convert_sat_to_nonogram(sat: SAT) -> Nonogram:
    if(not brute_force_sat(sat)):
        raise Exception("SAT is unsatisfiable")
    # create xClues from SAT
    xClues = sat_to_clue_sets(sat, True)    # allow duplicates
    yClues = [] # create yClues from vertical keys of SAT
    correct_grid = np.array(sat_to_key_sets(sat))
    for i in range(correct_grid.shape[1]):
        yClues.append(generate_clue(correct_grid[:, i]))
    # construct nonogram and populate nonogram values before returning
    nonogram = Nonogram(correct_grid.shape[0], correct_grid.shape[1])
    nonogram.x_clues = [tuple(x) for x in xClues]
    nonogram.y_clues = [tuple(y) for y in yClues]
    nonogram.correct_grid = correct_grid

    return nonogram
