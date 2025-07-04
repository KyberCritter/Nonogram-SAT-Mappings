# Scott Ratchford 2025.07.03

import math
import numpy as np
from nonogram import *
from sat import *
import os


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

# Returns every possible solution to the line
# Used after solve_line() to find all possible solutions
# Brute force algorithm
def brute_force_single_line(line, clues) -> list:
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
        if(np.array_equal(generateClue(solvedGrid), clues)):
            possibilities.append(np.array(solvedGrid))
    return possibilities

# Returns a list of SAT objects representing the clue in CNF form
# clues is a list of integers
# size is the size of the row or column
def clues_to_sat(clues, size) -> list:
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
            all_sats.append(line_to_sat(key_possibility, len(line)))

        return all_sats

# Returns a SAT object with a single possibility based on the key of a single line
def line_to_sat(line, key) -> SAT:
    sat = SAT()
    for index, value in np.ndenumerate(line):
        if(value == Marking.FILL):
            sat.add_clause(Clause([index[0]+1]))
        elif(value == Marking.EMPTY):
            sat.add_clause(Clause([-1*(index[0]+1)]))
    return sat

if __name__ == "__main__":
    # args:
    # 1: (write: True or False)
    # 2: "of" or "upto" or filename
    # 3: x (if "of" or "upto")
    # 4: y (if "of" or "upto")
    
    # write to file or not
    if(sys.argv[1].lower() == "true" or sys.argv[1] == "1" or sys.argv[1].lower() == "t" or sys.argv[1].lower() == "y" or sys.argv[1].lower() == "yes"):
        write = True
    else:
        write = False

    if(len(sys.argv) > 2):
        # read of nonograms of size x by y
        if(sys.argv[2] == "of"):
            if(len(sys.argv) < 4):
                raise Exception("Did not provide both x and y arguments")
            x = int(sys.argv[3])
            y = int(sys.argv[4])
            if(write):
                try:    # attempt to make a directory for the SATs
                    os.mkdir("./" + str(x) + "x" + str(y) + "/sats/")
                except:
                    pass    # directory already exists
            for i in range(int(math.pow(2, x * y))):
                filename = "./" + str(x) + "x" + str(y) + "/nonogram_" + str(x) + "x" + str(y) + "_" + str(i) + ".dat"
                nonogram = readNonogram(filename)
                all_sats = []
                for index, clues in enumerate(nonogram.xClues):
                    potential_sats = clues_to_sat(clues, nonogram.y)
                    all_sats.append(potential_sats)
                if(len(all_sats) < 0):
                    print("No SATs found for " + filename)
                    exit()
                else:
                    if(write):
                        path = "./" + str(x) + "x" + str(y) + "/sats/"
                        try:    # attempt to make a directory for the SATs
                            os.mkdir(str.split(path, "/")[-1])
                            os.mkdir(path)
                        except:
                            pass    # directory already exists
                        for sat_set_index, sat_set in enumerate(all_sats):
                            for sat_index, sat in enumerate(sat_set):
                                # sat_filename = path + "sat" + str(sat_set_index) + "_" + str(sat_index) + "_from_" + filename
                                sat_filename = path + "sat_" + str(sat_set_index) + "_" + str(sat_index) + "_from_" + str.split(filename, "/")[-1]
                                if(sat_to_file(sat, sat_filename)):
                                    print("Wrote SAT to " + sat_filename)
                                else:
                                    print("Failed to write SAT to " + sat_filename)
            print("Found a SAT for all nonograms of size " + str(x) + "x" + str(y) + ".")
            filename = sys.argv[2]
        elif(sys.argv[2] == "upto"):
            if(len(sys.argv) < 4):
                raise Exception("Did not provide both x and y arguments")
            i = int(sys.argv[3])
            j = int(sys.argv[4])
            for x in range(1, i+1):
                for y in range(x, j+1):
                    if(write):
                        try:    # attempt to make a directory for the SATs
                            os.mkdir("./" + str(x) + "x" + str(y) + "/sats/")
                        except:
                            pass    # directory already exists
                    for i in range(int(math.pow(2, x * y))):
                        filename = "./" + str(x) + "x" + str(y) + "/nonogram_" + str(x) + "x" + str(y) + "_" + str(i) + ".dat"
                        nonogram = readNonogram(filename)
                        all_sats = []
                        for index, clues in enumerate(nonogram.xClues):
                            potential_sats = clues_to_sat(clues, nonogram.y)
                            all_sats.append(potential_sats)
                        if(len(all_sats) < 0):
                            print("No SATs found for " + filename)
                            exit()
                        else:
                            if(write):  # write SATs to file
                                path = "./" + str(nonogram.x) + "x" + str(nonogram.y) + "/sats/"
                                try:    # attempt to make a directory for the SATs
                                    os.mkdir(str.split(path)[1])
                                    os.mkdir(path)
                                except:
                                    pass    # directory already exists
                                for sat_set_index, sat_set in enumerate(all_sats):
                                    for sat_index, sat in enumerate(sat_set):
                                        # sat_filename = path + "sat" + str(sat_set_index) + "_" + str(sat_index) + "_from_" + filename
                                        sat_filename = path + "sat_" + str(sat_set_index) + "_" + str(sat_index) + "_from_" + str.split(filename, "/")[-1]
                                        if(sat_to_file(sat, sat_filename)):
                                            print("Wrote SAT to " + sat_filename)
                                        else:
                                            print("Failed to write SAT to " + sat_filename)
                    print("Found a SAT for all nonograms of size " + str(x) + "x" + str(y) + ".")
        else:
            try:
                nonogram = readNonogram(sys.argv[2])
                nonogram.grid = np.full((nonogram.x, nonogram.y), Marking.UNKNOWN)
                print("X Clues: " + str(nonogram.xClues))
                print("Y Clues: " + str(nonogram.yClues))
                print("Key:\n" + str(nonogram.correctGrid))
                if(write):
                    try:    # attempt to make a directory for the SATs
                        os.mkdir("./" + str(nonogram.x) + "x" + str(nonogram.y) + "/sats/")
                    except:
                        pass    # directory already exists
                all_sats = []
                for index, clues in enumerate(nonogram.xClues):
                    potential_sats = clues_to_sat(clues, nonogram.y)
                    all_sats.append(potential_sats)
                    print("X Clue Set " + str(index) + ": " + str(clues))
                    for sat_index, sat in enumerate(potential_sats):
                        print("SAT " + str(sat_index) + ": " + str(sat.print_with_letters()))
                    if(write):  # write SATs to file
                        path = "./" + str(nonogram.x) + "x" + str(nonogram.y) + "/sats/"
                        try:    # attempt to make a directory for the SATs
                            os.mkdir(str.split(path, "/")[1])
                            os.mkdir(path)
                        except:
                            pass    # directory already exists
                        for sat_set_index, sat_set in enumerate(all_sats):
                            for sat_index, sat in enumerate(sat_set):
                                # sat_filename = path + "sat" + str(sat_set_index) + "_" + str(sat_index) + "_from_" + sys.argv[2]
                                sat_filename = path + "sat_" + str(sat_set_index) + "_" + str(sat_index) + "_from_" + str.split(sys.argv[2], "/")[-1]
                                if(sat_to_file(sat, sat_filename)):
                                    print("Wrote SAT to " + sat_filename)
                                else:
                                    print("Failed to write SAT to " + sat_filename)
            except:
                raise Exception("Error reading file")
    else:
        raise Exception("No filename argument provided")

    # the program could be extended further
    # this would solve the immediately obvious clues (or perhaps even run heuristic_solve() on nonogram)
    # then it would generate a SAT for the remaining cells (and perhaps solve it with a SAT solver)

    # os.mkdir("./2x3/sats/")