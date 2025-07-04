# Scott Ratchford 2023.04.29
import math
import random
import time
from itertools import groupby
import numpy as np
from enum import IntEnum
from datetime import datetime
import os
import sys

from .helpers import generate_clue


class Marking(IntEnum):
    """Cell states used for marking cells in player's grid.
    """
    UNKNOWN = -1    # unknown
    EMPTY = 0       # empty
    FILL = 1        # filled
    SPEC = 2        # speculate (O)
    ELIM = 3        # eliminate (X)

def generate_line(size):
    return [random.randint(0, 1) for i in range(size)]

# TODO: create formula for calculating cell and padding sizes from screen resolution
class Nonogram:
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.grid = np.full((x, y), Marking.UNKNOWN)
        self.correct_grid = np.zeros((x, y))
        self.x_clues = [None] * self.x  # list of tuples
        self.y_clues = [None] * self.y  # list of tuples
        self.x_confirm = [False] * x    # list of booleans indicating status, one for each row
        self.y_confirm = [False] * y    # list of booleans indicating status, one for each column

    def create_puzzle(self) -> None:
        """Randomly generates a puzzle key.
        """
        for i in range(self.x):
            self.correct_grid[i] = generate_line(self.y)
        for i in range(self.x):
            self.x_clues[i] = generate_clue(self.correct_grid[i])
        for i in range(self.y):
            self.y_clues[i] = generate_clue(self.correct_grid[:, i])

    def find_clues(self) -> None:
        """Generates puzzle key from self.correct_grid.
        """
        for i in range(self.x):
            self.x_clues[i] = generate_clue(self.correct_grid[i])
        for i in range(self.y):
            self.y_clues[i] = generate_clue(self.correct_grid[:, i])

    def is_valid(self) -> bool:
        for i_c, row in enumerate(self.correct_grid):
            for i_r, cell in enumerate(row):
                # if (cell == Marking.FILL) + (self.grid[i_c][i_r] != 1) == 1:
                #     return False
                if(cell == Marking.FILL and self.grid[i_c][i_r] != 1):
                    return False
                elif(cell != Marking.FILL and self.grid[i_c][i_r] == 1):
                    return False
        
        return True

    def is_valid_other(self, grid: np.array) -> bool:
        for i_c, row in enumerate(self.correct_grid):
            for i_r, cell in enumerate(row):
                # if (cell == Marking.FILL) + (grid[i_c][i_r] != 1) == 1:
                #     return False
                if(cell == Marking.FILL and grid[i_c][i_r] != 1):
                    return False
                elif(cell != Marking.FILL and grid[i_c][i_r] == 1):
                    return False
        
        return True

# Given a line and its clues, returns whether the line is confirmed
# Confirmation is defined as all cells in the line being either Marking.FILL or Marking.ELIM
# This value will be used to determine whether or not to call solve_line() on the line and to determine if the puzzle can be solved any further
# This function does not check if the line is CORRECTLY solved, only if it is full
# Time complexity: O(n) where n is the length of the line
def confirm_line(line) -> bool:
    return all(cell in (Marking.FILL, Marking.ELIM) for cell in line)

def is_partially_solved(line) -> bool:
    """Given a line, returns whether the
    line has Marking.FILL or Marking.ELIM cells.

    Args:
        line (_type_): _description_

    Returns:
        bool: _description_
    """
    return any(cell in (Marking.FILL, Marking.ELIM) for cell in line)

def heuristic_solve(nonogram: Nonogram) -> None:
    """Calls solve_row() on each line in the grid (vertical and horizontal)

    Args:
        nonogram (Nonogram): _description_

    Returns:
        _type_: _description_
    """
    sanityCoeff = 1

    if(len(sys.argv) > 2):  # debug must be on
        try:
            sanityCoeff = float(sys.argv[2])
        except:
            sanityCoeff = 1
    sanity = int(sanityCoeff * (nonogram.x + nonogram.y))   # sanity check to prevent infinite loop, 4 tries for each line
    # Find overlap between extremes of clues and fill in before solving lines
    for i in range(nonogram.x):
        overlap = find_extremes_overlap(nonogram.grid[i], nonogram.x_clues[i])
        if(is_partially_solved(overlap)):
            nonogram.grid[i] = np.copy(overlap)
            nonogram.x_confirm[i] = confirm_line(nonogram.grid[i])
    for i in range(nonogram.y):
        overlap = find_extremes_overlap(nonogram.grid[:, i], nonogram.y_clues[i])
        if(is_partially_solved(overlap)):
            nonogram.grid[:, i] = np.copy(overlap)
            nonogram.y_confirm[i] = confirm_line(nonogram.grid[:, i])

    while(sanity > 0):
        for i in range(nonogram.x):
            if(not nonogram.x_confirm[i]):
                nonogram.grid[i] = solve_line(nonogram.grid[i], nonogram.x_clues[i])
                if(not confirm_line(nonogram.grid[i])):
                    nonogram.grid[i] = fill_in_gaps(nonogram.grid[i], nonogram.x_clues[i])   # fill in gaps between clues TODO: test
                    sanity -= 1
                else:
                    nonogram.x_confirm[i] = True
        for i in range(nonogram.y):
            if(not nonogram.y_confirm[i]):
                nonogram.grid[:, i] = solve_line(nonogram.grid[:, i], nonogram.y_clues[i])
                if(not confirm_line(nonogram.grid[:, i])):
                    nonogram.grid[:, i] = fill_in_gaps(nonogram.grid[:, i], nonogram.y_clues[i])   # fill in gaps between clues TODO: test
                    sanity -= 1
                else:
                    nonogram.y_confirm[i] = True
        if(nonogram.is_valid()):
            break
        sanity -= 1
    
    return True

# Solves a line of the grid
# Cases:
#   1. The line is already filled in (all cells are either Marking.FILL or Marking.ELIM)
#   2. The line is trivial to solve
#       2a. If the line is empty, fill in all cells with Marking.ELIM
#       2b. If the line is full, fill in all cells with Marking.FILL
#       2c. If the the clues of the line and the gaps between them add up to the length of the line,
#           fill in the cells with Marking.FILL and gaps between with Marking.ELIM
#   3. There is a filled cell on 1 or 2 ends of the line TODO
#       3a. Extend the run(s) of filled cells to its (their) full size(s) and add Marking.ELIM after the run(s)
#   4. There is at least 1 eliminated cell on 1 or 2 ends of the line
#       4a. Run solve_line() on a smaller copy of the line with the eliminated cells removed
#   5. Nothing new can be determined about the line
def solve_line(line, clues) -> np.array:
    # Case 1 - line already complete
    if(confirm_line(line)):
        return line
    # Case 2a - trivial, empty
    if(len(clues) == 0):
        for i in range(len(line)):
            line[i] = Marking.ELIM
        return line
    # Case 2b - trivial, fill
    if(len(clues) == 1 and clues[0] == len(line)):
        for i in range(len(line)):
            line[i] = Marking.FILL
        return line
    # Case 2c - trivial, mixed
    if(sum(clues) + len(clues) - 1 == len(line)):
        tempLine = []
        for clueIndex, clue in enumerate(clues):
            for i in range(clue):
                tempLine.append(Marking.FILL)
            if(clueIndex < len(clues) - 1): # if this is not the last clue
                tempLine.append(Marking.ELIM)          # space between runs
        return np.array(tempLine)
    # Case 3 - extend runs
    # TODO

    # Case 4 - subline
    startIndex = 0
    endIndex = len(line) - 1
    while(line[startIndex] == Marking.ELIM):
        startIndex += 1
    while(line[endIndex] == Marking.ELIM):
        endIndex -= 1
    if(startIndex == 0 and endIndex == len(line) - 1):
        # nothing else can be done for the line with the current algorithm
        return line
    else:
        # Case 4
        subline = line[startIndex:endIndex+1]
        subline = solve_line(subline, clues)
        tempLine = []
        for i in range(startIndex):
            tempLine.append(line[i])
        for i in range(len(subline)):
            tempLine.append(subline[i])
        for i in range(endIndex+1, len(line)):
            tempLine.append(line[i])
        return np.array(tempLine)
    
# fill in the gaps on solved lines
def fill_in_gaps(line, clues):    
    filledCells = 0
    for cell in line:
        if(cell == Marking.FILL):
            filledCells += 1
    if(filledCells == sum(clues)):  # if the line is already filled in (assumes correct positions for each Marking.FILL)
        # fill in Marking.UNKNOWNs with Marking.ELIM
        for index, cell in enumerate(line):
            if(cell == Marking.UNKNOWN):
                line[index] = Marking.ELIM
        return line
    else:
        # if the line has not been solved (or does not have enough cells filled in to be solved), return the line
        return line

# Find the overlap between two extreme solutions from solve_subline
def find_extremes_overlap(line, clues):
    lowExtreme = find_low_extreme_solution(line, clues)
    highExtreme = find_high_extreme_solution(line, clues)
    overlap = []
    for i in range(len(line)):
        if(lowExtreme[i] >= 1 and lowExtreme[i] == highExtreme[i]):
            overlap.append(Marking.FILL)   # cell must be in the solution since it overlaps
        else:
            overlap.append(Marking.UNKNOWN)   # no overlap, cell is unknown
    return np.array(overlap)

# Find a possible solution on the low end of the line
# this function assumes that the subset of the line has a possible solution
# cannot directly be used as a solution because the values do not correspond to the Marking enumeration
def find_low_extreme_solution(line, clues):
    lowExtreme = [Marking.UNKNOWN] * len(line)
    index = 0
    for i, clue in enumerate(clues):    # for each clue
        for j in range(clue):           # fill in the appropriate number of spaces
            lowExtreme[index] = i + 1   # add the clue number to the subline (1-indexed)
            index += 1
        if(i < len(clues) - 1):     # if this is not the last clue
            lowExtreme[index] = 0   # add a space between runs
            index += 1
    return lowExtreme

# Find a possible solution on the high end of the line
# this function assumes that the subset of the line has a possible solution
# cannot directly be used as a solution because the values do not correspond to the Marking enumeration
def find_high_extreme_solution(line, clues):
    highExtreme = [Marking.UNKNOWN] * len(line)
    lowExtreme = find_low_extreme_solution(line, clues)
    lastIndex = 0
    for clue in clues:
        lastIndex += clue + 1   # add the clue and the space between clues
    lastIndex -= 1  # remove trailing space
    highExtreme = highExtreme[0:len(line)-lastIndex] + lowExtreme[0:lastIndex]
    return highExtreme

# Returns every possible solution to the puzzle
# Used after heuristic_solve() to find all possible solutions
# Brute force algorithm
def brute_force_remaining(nonogram: Nonogram) -> int:
    remainingCells = np.count_nonzero(nonogram.grid == Marking.UNKNOWN)
    solvedGrid = 0
    if(sum(nonogram.x_clues[0]) > (nonogram.x / 2)): # if more than half of cells on the first row should be filled, brute force 0b1111...111 to 0b0000...000
        for i in reversed(range(int(math.pow(2, remainingCells)))):
            solvedGrid = np.copy(nonogram.grid)
            remainingArray = np.zeros(remainingCells)
            tempStr = str(bin(i))
            tempStr = tempStr.replace("0b", "")
            tempStr = tempStr.zfill(remainingCells)
            for j in range(len(tempStr)):
                remainingArray[j] = int(tempStr[j])
            unknownIndex = 0
            for (x, y), value in np.ndenumerate(solvedGrid):
                if(value == Marking.UNKNOWN):
                    solvedGrid[x][y] = remainingArray[unknownIndex]
                    unknownIndex += 1
            if(nonogram.is_valid_other(solvedGrid)):
                nonogram.grid = np.copy(solvedGrid)
                return i    # return the number of attempts
    else:
        for i in range(int(math.pow(2, remainingCells))):
            solvedGrid = np.copy(nonogram.grid)
            remainingArray = np.zeros(remainingCells)
            tempStr = str(bin(i))
            tempStr = tempStr.replace("0b", "")
            tempStr = tempStr.zfill(remainingCells)
            for j in range(len(tempStr)):
                remainingArray[j] = int(tempStr[j])
            unknownIndex = 0
            for (x, y), value in np.ndenumerate(solvedGrid):
                if(value == Marking.UNKNOWN):
                    solvedGrid[x][y] = remainingArray[unknownIndex]
                    unknownIndex += 1
            if(nonogram.is_valid_other(solvedGrid)):
                nonogram.grid = np.copy(solvedGrid)
                return i    # return the number of attempts
    return -1   # Error, no solution found

# Reads a nonogram from a file and returns a Nonogram object
def read_nonogram(filename) -> Nonogram:
    file = open(filename, "r")
    lines = file.readlines()
    file.close()
    x, y = int(lines[1].split()[0]), int(lines[1].split()[1])
    nonogram = Nonogram(x, y)
    for i in range(nonogram.x):
        nonogram.x_clues[i] = [int(j) for j in lines[i + 2].split()]
        nonogram.x_clues[i] = tuple(nonogram.x_clues[i])
    for i in range(nonogram.y):
        nonogram.y_clues[i] = [int(j) for j in lines[i + nonogram.x + 2].split()]
        nonogram.y_clues[i] = tuple(nonogram.y_clues[i])
    for i in range(2 + nonogram.x + nonogram.y, len(lines)):
        rows = [int(j) for j in lines[i].split()]
        for j in range(len(rows)):
            if(rows[j] == 1):
                nonogram.correct_grid[i - 2 - nonogram.x - nonogram.y][j] = Marking.FILL
            elif(rows[j] == 0):
                nonogram.correct_grid[i - 2 - nonogram.x - nonogram.y][j] = Marking.EMPTY
    return nonogram

# Writes a nonogram to a file and returns filename if successful, False if not
def write_nonogram(nonogram: Nonogram, filename: str | None = None) -> bool:
    if filename is None:
        filename = f"nonogram_{datetime.now().strftime("%Y_%m_%d_%H_%M_%S")}.dat"

    try:
        file = open(filename, "x")
    except:
        print("Error: writeNonogram() failed to write to file: " + filename)
        return False
    
    lines = []
    lines.append(f"# Randomly generated nonogram, {filename}")
    lines.append(f"{nonogram.x} {nonogram.y}")

    for i in range(len(nonogram.x_clues)):
        currLine = ""
        if(nonogram.x_clues[i] != None):   # if the line is not empty
            for j in range(len(nonogram.x_clues[i])):
                currLine += str(nonogram.x_clues[i][j]) + " "
        lines.append(currLine)
    for i in range(len(nonogram.y_clues)):   # if the line is not empty
        currLine = ""
        if(nonogram.y_clues[i] != None):
            for j in range(len(nonogram.y_clues[i])):
                currLine += str(nonogram.y_clues[i][j]) + " "
        lines.append(currLine)
    for i in range(len(nonogram.correct_grid)):
        currLine = ""
        for j in range(len(nonogram.correct_grid[i])):
            currLine += str(int(nonogram.correct_grid[i][j])) + " "
        lines.append(currLine)
    for i in range(len(lines)):
        file.write(lines[i])
        file.write("\n")
    file.close()
    
    return filename

# Creates every possible nonogram up to a given size and writes them to files, returning the number of successful writes
def write_every_puzzle(x, y):
    new_path = os.path.join(os.getcwd(), f"{x}x{y}")
    try:    # make folder for puzzles, if needed
        os.mkdir(new_path)
    except:
        raise Exception(f"write_every_puzzle() failed to create directory to {new_path}")
    
    num_cells = x * y
    temp_grid = np.zeros((num_cells))
    tally = 0

    for counter in range(int(math.pow(2, num_cells))):
        temp_grid = np.zeros((num_cells))
        # count in binary
        temp_str = str(bin(counter))
        temp_str = temp_str.replace("0b", "")
        temp_str = temp_str.zfill(num_cells)
        # translate the binary string into a nonogram grid
        for j, char in enumerate(temp_str):
            temp_grid[j] = int(char)
        temp_grid = temp_grid.reshape(x, y)
        # write out nonogram
        temp_nonogram = Nonogram(x, y)
        temp_nonogram.correct_grid = np.copy(temp_grid)
        temp_nonogram.find_clues()

        write_nonogram(os.path.join(new_path, f"nonogram_{x}x{y}_{counter}.dat"))
        
        tally += 1
    
    return tally

# Solves every possible nonogram up to a given size (reading them from files), returning the number of successful attempts
# The nonograms must be found in the folder "./AxB/" where A and B are the dimensions of the nonogram
def solve_every_puzzle(x, y):
    tally = 0
    brute_success = 0
    brute_attempts = 0
    brute_mini_attempts = 0

    num_puzzles = int(math.pow(2, x * y))

    for counter in range(num_puzzles):
        size = f"{x}x{y}"
        nonogram = read_nonogram(os.path.join(os.getcwd(), size, f"nonogram_{size}_{counter}.dat"))
        heuristic_solve(nonogram)
        if nonogram.is_valid():
            tally += 1
        else:
            brute_attempts += 1
            attempts = brute_force_remaining(nonogram)
            if attempts == -1:
                raise Exception(f"Error: solve_every_puzzle() failed to solve nonogram {counter}")
            else:
                brute_mini_attempts += attempts
                brute_success += 1

    print(f"All methods: {tally + brute_success}/{num_puzzles} succeeded.")
    print(f"Heuristic solve succeeded {tally}/{num_puzzles} times.")

    if brute_attempts > 0:
        print(f"Heuristic-brute-force succeeded {brute_success}/{brute_attempts} times.")
        print(f"Average brute-force attempts per non-heuristic puzzle: {brute_mini_attempts/brute_attempts}")

    return tally

# Counts the number of filled cells based on the clues
def count_clues(nonogram: Nonogram):
    return sum([sum(clue) for clue in nonogram.x_clues])
