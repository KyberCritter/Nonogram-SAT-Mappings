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

debug = False

# cell states used for marking cells in player's grid
class Marking(IntEnum):
    UNKNOWN = -1    # unknown
    EMPTY = 0       # empty
    FILL = 1        # filled
    SPEC = 2        # speculate (O)
    ELIM = 3        # eliminate (X)

# TODO: create formula for calculating cell and padding sizes from screen resolution
class Nonogram:
    def __init__(self, x, y) -> None:
        self.x = x
        self.y = y
        self.grid = np.full((x, y), Marking.UNKNOWN)
        self.correctGrid = np.zeros((x, y))
        self.xClues = [None] * self.x   # list of tuples
        self.yClues = [None] * self.y   # list of tuples
        self.xConfirm = [False] * x # list of booleans indicating status, one for each row
        self.yConfirm = [False] * y # list of booleans indicating status, one for each column

    # randomly generates a puzzle key
    def createPuzzle(self) -> None:
        def generateLine(size):
            line = []
            for i in range(size):
                line.append(random.randint(0, 1))
            return line
        def generateClue(line):
            # https://stackoverflow.com/questions/34443946/count-consecutive-characters
            lineString = ""
            for i in line:
                lineString += str(int(i))
            groups = groupby(lineString)
            result = [(label, sum(1 for _ in group)) for label, group in groups]
            clue = [None] * len(result)
            for index, tuple in enumerate(result):
                if(tuple[0] == "1"):
                    clue[index] = tuple[1]  # set clue to length of lines
            while(None in clue):
                clue.remove(None)
            return clue
        for i in range(self.x):
            self.correctGrid[i] = generateLine(self.y)
        for i in range(self.x):
            self.xClues[i] = generateClue(self.correctGrid[i])
        for i in range(self.y):
            self.yClues[i] = generateClue(self.correctGrid[:, i])

    # generates puzzle key from self.correctGrid
    def findClues(self) -> None:
        def generateClue(line):
            # https://stackoverflow.com/questions/34443946/count-consecutive-characters
            lineString = ""
            for i in line:
                lineString += str(int(i))
            groups = groupby(lineString)
            result = [(label, sum(1 for _ in group)) for label, group in groups]
            clue = [None] * len(result)
            for index, tuple in enumerate(result):
                if(tuple[0] == "1"):
                    clue[index] = tuple[1]  # set clue to length of lines
            while(None in clue):
                clue.remove(None)
            return clue
        for i in range(self.x):
            self.xClues[i] = generateClue(self.correctGrid[i])
        for i in range(self.y):
            self.yClues[i] = generateClue(self.correctGrid[:, i])

    def isValid(self) -> bool:
        for colIndex, row in enumerate(self.correctGrid):
            for rowIndex, cell in enumerate(row):
                if(cell == Marking.FILL and self.grid[colIndex][rowIndex] != 1):
                    return False
                elif(cell != Marking.FILL and self.grid[colIndex][rowIndex] == 1):
                    return False
        return True

    def isValidOther(self, grid: np.array) -> bool:
        for colIndex, row in enumerate(self.correctGrid):
            for rowIndex, cell in enumerate(row):
                if(cell == Marking.FILL and grid[colIndex][rowIndex] != 1):
                    return False
                elif(cell != Marking.FILL and grid[colIndex][rowIndex] == 1):
                    return False
        return True

# Given a line and its clues, returns whether the line is confirmed
# Confirmation is defined as all cells in the line being either Marking.FILL or Marking.ELIM
# This value will be used to determine whether or not to call solve_line() on the line and to determine if the puzzle can be solved any further
# This function does not check if the line is CORRECTLY solved, only if it is full
# Time complexity: O(n) where n is the length of the line
def confirm_line(line) -> bool:
    for cell in line:
        if(cell != Marking.FILL and cell != Marking.ELIM):
            return False
    return True

# Given a line, returns whether the line has Marking.FILL or Marking.ELIM cells
def is_partially_solved(line) -> bool:
    for cell in line:
        if(cell == Marking.FILL or cell == Marking.ELIM):
            return True
    return False

# Calls solve_row() on each line in the grid (vertical and horizontal)
def heuristic_solve(nonogram) -> None:
    sanityCoeff = 1
    if(len(sys.argv) > 2):  # debug must be on
        try:
            sanityCoeff = float(sys.argv[2])
        except:
            sanityCoeff = 1
    sanity = int(sanityCoeff * (nonogram.x + nonogram.y))   # sanity check to prevent infinite loop, 4 tries for each line
    # Find overlap between extremes of clues and fill in before solving lines
    for i in range(nonogram.x):
        overlap = find_extremes_overlap(nonogram.grid[i], nonogram.xClues[i])
        if(is_partially_solved(overlap)):
            nonogram.grid[i] = np.copy(overlap)
            nonogram.xConfirm[i] = confirm_line(nonogram.grid[i])
    for i in range(nonogram.y):
        overlap = find_extremes_overlap(nonogram.grid[:, i], nonogram.yClues[i])
        if(is_partially_solved(overlap)):
            nonogram.grid[:, i] = np.copy(overlap)
            nonogram.yConfirm[i] = confirm_line(nonogram.grid[:, i])

    while(sanity > 0):
        for i in range(nonogram.x):
            if(not nonogram.xConfirm[i]):
                nonogram.grid[i] = solve_line(nonogram.grid[i], nonogram.xClues[i])
                if(not confirm_line(nonogram.grid[i])):
                    nonogram.grid[i] = fill_in_gaps(nonogram.grid[i], nonogram.xClues[i])   # fill in gaps between clues TODO: test
                    sanity -= 1
                else:
                    nonogram.xConfirm[i] = True
        for i in range(nonogram.y):
            if(not nonogram.yConfirm[i]):
                nonogram.grid[:, i] = solve_line(nonogram.grid[:, i], nonogram.yClues[i])
                if(not confirm_line(nonogram.grid[:, i])):
                    nonogram.grid[:, i] = fill_in_gaps(nonogram.grid[:, i], nonogram.yClues[i])   # fill in gaps between clues TODO: test
                    sanity -= 1
                else:
                    nonogram.yConfirm[i] = True
        if(nonogram.isValid()):
            break
        sanity -= 1

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
    
    # Error Case, should never execute
    if(debug):  print("Error: solve_line() failed to solve line: " + str(line) + " with clues: " + str(clues))
    return line

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
    if(sum(nonogram.xClues[0]) > (nonogram.x / 2)): # if more than half of cells on the first row should be filled, brute force 0b1111...111 to 0b0000...000
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
            if(nonogram.isValidOther(solvedGrid)):
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
            if(nonogram.isValidOther(solvedGrid)):
                nonogram.grid = np.copy(solvedGrid)
                return i    # return the number of attempts
    return -1   # Error, no solution found

# Reads a nonogram from a file and returns a Nonogram object
def readNonogram(filename) -> Nonogram:
    file = open(filename, "r")
    lines = file.readlines()
    file.close()
    x, y = int(lines[1].split()[0]), int(lines[1].split()[1])
    nonogram = Nonogram(x, y)
    for i in range(nonogram.x):
        nonogram.xClues[i] = [int(j) for j in lines[i + 2].split()]
        nonogram.xClues[i] = tuple(nonogram.xClues[i])
    for i in range(nonogram.y):
        nonogram.yClues[i] = [int(j) for j in lines[i + nonogram.x + 2].split()]
        nonogram.yClues[i] = tuple(nonogram.yClues[i])
    for i in range(2 + nonogram.x + nonogram.y, len(lines)):
        rows = [int(j) for j in lines[i].split()]
        for j in range(len(rows)):
            if(rows[j] == 1):
                nonogram.correctGrid[i - 2 - nonogram.x - nonogram.y][j] = Marking.FILL
            elif(rows[j] == 0):
                nonogram.correctGrid[i - 2 - nonogram.x - nonogram.y][j] = Marking.EMPTY
    return nonogram

# Writes a nonogram to a file and returns filename if successful, False if not
def writeNonogram(nonogram: Nonogram, filename="nonogram_"+datetime.now().strftime("%Y_%m_%d_%H_%M_%S")+".dat") -> bool:
    try:
        file = open(filename, "x")
    except:
        print("Error: writeNonogram() failed to write to file: " + filename)
        return False
    lines = []
    lines.append("# Randomly generated nonogram, " + filename)
    lines.append(str(nonogram.x) + " " + str(nonogram.y))
    for i in range(len(nonogram.xClues)):
        currLine = ""
        if(nonogram.xClues[i] != None):   # if the line is not empty
            for j in range(len(nonogram.xClues[i])):
                currLine += str(nonogram.xClues[i][j]) + " "
        lines.append(currLine)
    for i in range(len(nonogram.yClues)):   # if the line is not empty
        currLine = ""
        if(nonogram.yClues[i] != None):
            for j in range(len(nonogram.yClues[i])):
                currLine += str(nonogram.yClues[i][j]) + " "
        lines.append(currLine)
    for i in range(len(nonogram.correctGrid)):
        currLine = ""
        for j in range(len(nonogram.correctGrid[i])):
            currLine += str(int(nonogram.correctGrid[i][j])) + " "
        lines.append(currLine)
    for i in range(len(lines)):
        file.write(lines[i])
        file.write("\n")
    file.close()
    if(debug):  print("Nonogram written to file: " + filename)
    return filename

# Creates every possible nonogram up to a given size and writes them to files, returning the number of successful writes
def writeEveryPuzzle(x, y):
    try:    # make folder for puzzles, if needed
        os.mkdir("./" + str(x) + "x" + str(y))
    except:
        if(debug): print("Error: writeEveryPuzzle() failed to create directory: " + str(x) + "x" + str(y))
    numCells = x * y
    tempGrid = np.zeros((numCells))
    tally = 0
    for counter in range(int(math.pow(2, numCells))):
        tempGrid = np.zeros((numCells))
        # count in binary
        tempStr = str(bin(counter))
        tempStr = tempStr.replace("0b", "")
        tempStr = tempStr.zfill(numCells)
        # translate the binary string into a nonogram grid
        for j, char in enumerate(tempStr):
            tempGrid[j] = int(char)
        tempGrid = tempGrid.reshape(x, y)
        # write out nonogram
        tempNonogram = Nonogram(x, y)
        tempNonogram.correctGrid = np.copy(tempGrid)
        tempNonogram.findClues()
        try:
            writeNonogram(tempNonogram, "./" + str(x) + "x" + str(y) + "/nonogram_" + str(x) + "x" + str(y) + "_" + str(counter) + ".dat")
        except:
            return False    # in case of error
        tally += 1
    return tally

# Solves every possible nonogram up to a given size (reading them from files), returning the number of successful attempts
# The nonograms must be found in the folder "./AxB/" where A and B are the dimensions of the nonogram
def solveEveryPuzzle(x, y):
    tally = 0
    bruteSuccess = 0
    bruteAttempts = 0
    bruteMiniAttempts = 0
    for counter in range(int(math.pow(2, x * y))):
        nonogram = readNonogram("./" + str(x) + "x" + str(y) + "/nonogram_" + str(x) + "x" + str(y) + "_" + str(counter) + ".dat")
        heuristic_solve(nonogram)
        if(nonogram.isValid()):
            tally += 1
        else:
            bruteAttempts += 1
            attempts = brute_force_remaining(nonogram)
            if(attempts == -1):
                # writeNonogram(nonogram, "./failed/nonogram_" + str(x) + "x" + str(y) + "_" + str(counter) + "_failed.dat")
                if(debug): print("Error: solveEveryPuzzle() failed to solve nonogram: " + str(counter))
            else:
                bruteMiniAttempts += attempts
                bruteSuccess += 1
    if(True):
        print("All methods: " + str(tally + bruteSuccess) + "/" + str(int(math.pow(2, x * y))) + " succeeded.")
        print("Heuristic solve succeeded " + str(tally) + "/" + str(int(math.pow(2, x * y))) + " times.")
        if(bruteAttempts > 0):
            print("Heuristic-brute-force succeeded " + str(bruteSuccess) + "/" + str(bruteAttempts) + " times.")
            print("Average brute-force attempts per non-heuristic puzzle: " + str(bruteMiniAttempts/bruteAttempts))
    return tally

# Counts the number of filled cells based on the clues
def count_clues(nonogram: Nonogram):
    return sum([sum(clue) for clue in nonogram.xClues])

if __name__ == "__main__":
    # Set debug mode based on the first command line argument
    debug = False
    if(len(sys.argv) > 1):
        if(sys.argv[1] == "debug"):
            debug = True
    if(debug): print("Debug mode is enabled.")
    if(len(sys.argv) > 2):
        if(debug): print("Sanity Coefficient: " + sys.argv[2])

    # Solve every puzzle test (bounded)
    # x, y = 4, 4
    # incr = 4096
    # i, j = 0, incr - 1
    # while(j <= int(math.pow(2, x * y))):
    #     print("Solving " + str(x) + "x" + str(y) + " puzzles from " + str(i) + " to " + str(j) + "...")
    #     startTime = time.time()
    #     solveEveryPuzzleBounded(x, y, i, j)
    #     endTime = time.time()
    #     print("Solved " + str(x) + "x" + str(y) + " puzzles from " + str(i) + " to " + str(j) + " in " + str(endTime - startTime) + " seconds.")
    #     i += incr
    #     j += incr

    # User input loop
    option = ""
    while(True):
        option = input("1 for random puzzle, 2 for reading from file, 3 for writing all puzzles of a given size, 4 for solving all puzzles of a given size, 5 for generating a puzzle from a decimal number: ")
        if(option == "1"):
            x = int(input("Enter x dimension: "))
            y = int(input("Enter y dimension: "))
            nonogram = Nonogram(x, y)
            nonogram.createPuzzle()
        elif(option == "2"):
            filename = input("Enter filename: ")
            try:
                nonogram = readNonogram(filename)
            except:
                print("Error: could not read file.")
                continue

        if(option == "1" or option == "2"):
            print("X clues: " + str(nonogram.xClues))
            print("Y clues: " + str(nonogram.yClues))
            print("Key (hidden from heuristic solver):\n" + str(nonogram.correctGrid))
            startTime = time.time()
            heuristic_solve(nonogram)
            endTime = time.time()
            if(nonogram.isValid()):
                print("Heuristic solution in " + str(endTime - startTime) + " seconds.")
                print(nonogram.grid)
            else:
                print("Heuristic solution failed.")
                print("Heuristic solution attempt:\n" + str(nonogram.grid))
                optionB = ""
                while(optionB != "y" and optionB != "n"):
                    optionB = input("Attempt partial brute-force? (y/n): ")
                    if(optionB == "y"):
                        startTime = time.time()
                        brute_force_remaining(nonogram)
                        endTime = time.time()
                        if(nonogram.isValid()):
                            print("Brute force solution in " + str(endTime - startTime) + " seconds.")
                            print(nonogram.grid)
                        else:
                            print("Brute force solution failed.")
                    elif(optionB == "n"):
                        print("Brute force solution not attempted.")
            if(option == "1"):
                option = ""
                while(option != "y" and option != "n"):
                    option = input("Write puzzle to file? (y/n): ")
                    if(option == "y"):
                        filename = input("Enter filename: ")
                        if(writeNonogram(nonogram, filename)):
                            print("Solution written to file.")
                        else:
                            print("Error: could not write to file.")
                    elif(option == "n"):
                        print("Solution not written to file.")
                    else:
                        print("Invalid input. Select y or n.")
        elif(option == "3"):
            # Write every puzzle of n*m
            x = int(input("Enter x dimension: "))
            y = int(input("Enter y dimension: "))
            print("Writing every puzzle that is " + str(x) + "x" + str(y) + " to file...")
            print(str(writeEveryPuzzle(x, y)) + " puzzles written to file.")
        elif(option == "4"):
            # Read every puzzle of n*m
            x = int(input("Enter x dimension: "))
            y = int(input("Enter y dimension: "))
            print("Solving every puzzle that is " + str(x) + "x" + str(y) + "...")
            startTime = time.time()
            solveEveryPuzzle(x, y)
            endTime = time.time()
            print("Solved every puzzle that is " + str(x) + "x" + str(y) + " in " + str(endTime - startTime) + " seconds.")
        elif(option == "5"):
            # Generate a puzzle of a given size from a given decimal number
            x = int(input("Enter x dimension: "))
            y = int(input("Enter y dimension: "))
            number = int(input("Enter decimal number: "))
            numCells = int(math.pow(2, x * y))
            if(number > numCells):
                print("Error: number too large.")
                continue
            # generate puzzle from number
            nonogram = Nonogram(x, y)
            key = np.zeros(x * y, dtype=int)
            tempStr = str(bin(number))
            tempStr = tempStr.replace("0b", "")
            tempStr = tempStr.zfill(x * y)
            print(tempStr)  # debug
            for j in range(len(tempStr)):
                key[j] = int(tempStr[j])
            index = 0
            key = key.reshape((x, y))
            nonogram.correctGrid = np.copy(key)
            # create clues from key
            nonogram.findClues()
            # # print the puzzle
            print("X clues: " + str(nonogram.xClues))
            print("Y clues: " + str(nonogram.yClues))
            print("Key:\n" + str(nonogram.correctGrid))
            option = ""
            while(option != "y" and option != "n"):
                option = input("Write puzzle to file? (y/n): ")
                if(option == "y"):
                    filename = input("Enter filename: ")
                    if(writeNonogram(nonogram, filename)):
                        print("Solution written to file.")
                    else:
                        print("Error: could not write to file.")
                elif(option == "n"):
                    print("Solution not written to file.")
                else:
                    print("Invalid input. Select y or n.")
        else:
            print("Exiting program...")
            exit()
