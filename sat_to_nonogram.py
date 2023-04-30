# Scott Ratchford 2023.04.29
import numpy as np
from nonogram import *
from sat import *

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

def sat_to_clue_sets(sat: SAT, allowDuplicates=True) -> list:
    solutions = return_all_sat_solutions(sat)
    clueSets = []
    for solution in solutions:
        tempClue = generateClue(solution)
        if(allowDuplicates):
            clueSets.append(tempClue)
        else:
            if(not tempClue in clueSets):
                clueSets.append(tempClue)
    return clueSets

def sat_to_key_sets(sat: SAT) -> list:
    solutions = return_all_sat_solutions(sat)
    keySets = []
    for solution in solutions:
        keySets.append([Marking(x) for x in solution])
    return keySets

def sat_to_nonogram(sat: SAT) -> Nonogram:
    if(not brute_force_sat(sat)):
        raise Exception("SAT is unsatisfiable")
    # create xClues from SAT
    xClues = sat_to_clue_sets(sat, True)    # allow duplicates
    yClues = [] # create yClues from vertical keys of SAT
    correctGrid = np.array(sat_to_key_sets(sat))
    for i in range(correctGrid.shape[1]):
        yClues.append(generateClue(correctGrid[:, i]))
    # construct nonogram and populate nonogram values before returning
    nonogram = Nonogram(correctGrid.shape[0], correctGrid.shape[1])
    nonogram.xClues = [tuple(x) for x in xClues]
    nonogram.yClues = [tuple(y) for y in yClues]
    nonogram.correctGrid = correctGrid

    return nonogram

if __name__ == "__main__":
    if(len(sys.argv) > 1):
        filename = sys.argv[1]
        try:
            sat = sat_from_file(filename)
        except:
            raise Exception("Error reading file")
    else:
        raise Exception("No filename argument provided")
    
    print("SAT: " + str(sat.print_with_letters()))
    # print("Brute force solution: " + str(brute_force_sat(sat)))
    if(len(brute_force_sat(sat)) > 0):
        print("Satisfiable")
    else:
        print("Not satisfiable")
    # print("All solutions:\n" + str(return_all_sat_solutions(sat)))
    # print("Clue sets: " + str(sat_to_clue_sets(sat)))
    # print("Key sets: " + str(sat_to_key_sets(sat)))
    nonogram = sat_to_nonogram(sat)
    print("xClues: " + str(nonogram.xClues))
    print("yClues: " + str(nonogram.yClues))
    print("Key:\n" + str(nonogram.correctGrid))

    option = input("Write nonogram to file? (y/n): ")
    if(option.lower() == "y"):
        filename = input("Enter filename: ")
        print("Wrote nonogram to " + str(writeNonogram(nonogram, filename)))
