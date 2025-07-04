# Scott Ratchford 2025.07.03

import math
import numpy as np
# from nonogram import *
# from sat import *
import os
import sys

from .nonogram import (
    Marking, generate_clue, read_nonogram, confirm_line, solve_line,
)
from .sat import (
    Clause, SAT, sat_to_file,
)


def brute_force_single_line(line, clues) -> list:
    """Returns every possible solution to the line.
    Used after solve_line() to find all possible solutions.
    Brute force algorithm

    Args:
        line (_type_): _description_
        clues (_type_): _description_

    Returns:
        list: _description_
    """
    possibilities = []
    remainingCells = np.count_nonzero(line == Marking.UNKNOWN)
    if(remainingCells == 0):
        return [line]
    solvedGrid = 0
    for i in reversed(range(int(math.pow(2, remainingCells)))):
        solvedGrid = np.copy(line)
        remainingArray = np.zeros(remainingCells)
        tempStr = str(bin(i))
        tempStr = tempStr.replace("0b", "")
        tempStr = tempStr.zfill(remainingCells)
        for j in range(len(tempStr)):
            remainingArray[j] = int(tempStr[j])
        unknownIndex = 0
        for x, value in np.ndenumerate(solvedGrid):
            if(value == Marking.UNKNOWN):
                solvedGrid[x] = remainingArray[unknownIndex]
                unknownIndex += 1
        if(np.array_equal(generate_clue(solvedGrid), clues)):
            possibilities.append(np.array(solvedGrid))
    
    return possibilities

def clues_to_sat(clues, size) -> list:
    """Returns a list of SAT objects representing the clue in CNF form.
    Clues is a list of integers.
    Size is the size of the row or column.

    Args:
        clues (_type_): _description_
        size (_type_): _description_

    Raises:
        Exception: _description_

    Returns:
        list: _description_
    """
    all_sats = []
    if(sum(clues) + len(clues) - 1 > size):
        raise Exception("Clues do not fit in row/column")
    elif(len(clues) == 0):  # Empty clue
        sat = SAT()
        sat.add_clause(Clause([-1*i for i in range(1, size+1)]))
        return [sat]
    elif(sum(clues) + len(clues) - 1 == size):  # Perfectly fitting clue(s)
        sat = SAT()
        # Add a clause for each clue
        tally = 0
        for index, clue in enumerate(clues):
            clause = Clause([i+1 for i in range(tally, tally+clue)])
            sat.add_clause(clause)
            tally += clue
            if(index < len(clues) - 1):
                sat.add_clause(Clause([-1*(clue + 1)]))
                tally += 1
        return [sat]
    else:
        line = np.full(size, Marking.UNKNOWN)
        line = solve_line(line, clues)
        if(confirm_line(line)):
            sat = SAT()
            # Add a clause for each clue
            tally = 0
            for index, clue in enumerate(clues):
                clause = Clause([i+1 for i in range(tally, tally+clue)])
                sat.add_clause(clause)
                tally += clue
                if(index < len(clues) - 1):
                    sat.add_clause(Clause([-1*(clue + 1)]))
                    tally += 1
            return [sat]
        # generate all possible SATs for the clue (NOT the line)
        line = np.full(size, Marking.UNKNOWN)
        filled_possibilities = brute_force_single_line(line, clues) # list of possible keys for the line
        all_sats = []
        for key_possibility in filled_possibilities:                # convert each possible key to a SAT
            all_sats.append(line_to_sat(key_possibility))

        return all_sats

# Returns a SAT object with a single possibility based on a single line
def line_to_sat(line) -> SAT:
    sat = SAT()
    for index, value in np.ndenumerate(line):
        if(value == Marking.FILL):
            sat.add_clause(Clause([index[0]+1]))
        elif(value == Marking.EMPTY):
            sat.add_clause(Clause([-1*(index[0]+1)]))
    return sat
