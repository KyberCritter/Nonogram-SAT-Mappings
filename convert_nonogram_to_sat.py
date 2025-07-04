
import sys
import os
import math
import numpy as np

from src.nonogram_sat import (
    clues_to_sat, read_nonogram, sat_to_file, Marking
)


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
                nonogram = read_nonogram(filename)
                all_sats = []
                for index, clues in enumerate(nonogram.x_clues):
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
                        nonogram = read_nonogram(filename)
                        all_sats = []
                        for index, clues in enumerate(nonogram.x_clues):
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
                nonogram = read_nonogram(sys.argv[2])
                nonogram.grid = np.full((nonogram.x, nonogram.y), Marking.UNKNOWN)
                print("X Clues: " + str(nonogram.x_clues))
                print("Y Clues: " + str(nonogram.y_clues))
                print("Key:\n" + str(nonogram.correct_grid))
                if(write):
                    try:    # attempt to make a directory for the SATs
                        os.mkdir("./" + str(nonogram.x) + "x" + str(nonogram.y) + "/sats/")
                    except:
                        pass    # directory already exists
                all_sats = []
                for index, clues in enumerate(nonogram.x_clues):
                    potential_sats = clues_to_sat(clues, nonogram.y)
                    all_sats.append(potential_sats)
                    print("X Clue Set " + str(index) + ": " + str(clues))
                    for sat_index, sat in enumerate(potential_sats):
                        print(f"SAT {sat_index}: {sat.print_with_letters()}")
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
