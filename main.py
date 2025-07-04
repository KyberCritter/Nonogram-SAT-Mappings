

import numpy as np
import sys
import time
import math

from src.nonogram_sat import (
    Nonogram, read_nonogram, heuristic_solve,
    solve_every_puzzle, brute_force_remaining,
    write_nonogram, write_every_puzzle,
)


if __name__ == "__main__":
    # Set debug mode based on the first command line argument
    
    if(len(sys.argv) > 2):
        print(f"Sanity Coefficient: {sys.argv[2]}")

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
    
    option = input("1 for random puzzle, 2 for reading from file, 3 for writing all puzzles of a given size, 4 for solving all puzzles of a given size, 5 for generating a puzzle from a decimal number: ")
    if option == "1":
        x = int(input("Enter x dimension: "))
        y = int(input("Enter y dimension: "))
        nonogram = Nonogram(x, y)
        nonogram.create_puzzle()
    elif option == "2":
        filename = input("Enter filename: ")
        try:
            nonogram = read_nonogram(filename)
        except:
            print("Error: could not read file.")
            sys.exit(-1)

    if option in ("1", "2"):
        print("X clues: " + str(nonogram.x_clues))
        print("Y clues: " + str(nonogram.y_clues))
        print("Key (hidden from heuristic solver):\n" + str(nonogram.correct_grid))
        startTime = time.time()
        heuristic_solve(nonogram)
        endTime = time.time()
        if(nonogram.is_valid()):
            print("Heuristic solution in " + str(endTime - startTime) + " seconds.")
            print(nonogram.grid)
        else:
            print("Heuristic solution failed.")
            print("Heuristic solution attempt:\n" + str(nonogram.grid))
            option_b = ""
            while(option_b != "y" and option_b != "n"):
                option_b = input("Attempt partial brute-force? (y/n): ")
                if option_b == "y":
                    startTime = time.time()
                    brute_force_remaining(nonogram)
                    endTime = time.time()
                    if(nonogram.is_valid()):
                        print("Brute force solution in " + str(endTime - startTime) + " seconds.")
                        print(nonogram.grid)
                    else:
                        print("Brute force solution failed.")
                elif option_b == "n":
                    print("Brute force solution not attempted.")
                else:
                    print("Invalid choice.")
                    sys.exit(-1)
        if option == "1":
            option = input("Write puzzle to file? (y/n): ")
            if option == "y":
                filename = input("Enter filename: ")
                if(write_nonogram(nonogram, filename)):
                    print("Solution written to file.")
                else:
                    print("Error: could not write to file.")
            if option == "n":
                print("Solution not written to file.")
            else:
                print("Invalid input. Select y or n.")
                sys.exit(-1)
    elif option == "3":
        # Write every puzzle of n*m
        x = int(input("Enter x dimension: "))
        y = int(input("Enter y dimension: "))
        print(f"Writing every puzzle that is {x}x{y} to file...")
        num = write_every_puzzle(x, y)
        print(f"Wrote {num} puzzles to file.")
    elif option == "4":
        # Read every puzzle of n*m
        x = int(input("Enter x dimension: "))
        y = int(input("Enter y dimension: "))
        print(f"Solving every puzzle that is {x}x{y}...")
        startTime = time.time()
        solve_every_puzzle(x, y)
        endTime = time.time()
        print(f"Solved every puzzle that is {x}x{y} in {endTime - startTime} seconds.")
    elif option == "5":
        # Generate a puzzle of a given size from a given decimal number
        x = int(input("Enter x dimension: "))
        y = int(input("Enter y dimension: "))
        number = int(input("Enter decimal number: "))
        num_cells = int(math.pow(2, x * y))
        if(number > num_cells):
            print("Error: number too large.")
            sys.exit(-1)
        # generate puzzle from number
        nonogram = Nonogram(x, y)
        key = np.zeros(x * y, dtype=int)
        temp_str = str(bin(number))
        temp_str = temp_str.replace("0b", "")
        temp_str = temp_str.zfill(x * y)
        
        for j in range(len(temp_str)):
            key[j] = int(temp_str[j])
        index = 0
        key = key.reshape((x, y))
        nonogram.correct_grid = np.copy(key)
        # create clues from key
        nonogram.find_clues()
        # # print the puzzle
        print("X clues: " + str(nonogram.x_clues))
        print("Y clues: " + str(nonogram.y_clues))
        print("Key:\n" + str(nonogram.correct_grid))

        option = input("Write puzzle to file? (y/n): ")
        if option == "y":
            filename = input("Enter filename: ")
            if(write_nonogram(nonogram, filename)):
                print("Solution written to file.")
            else:
                print("Error: could not write to file.")
        elif option == "n":
            print("Solution not written to file.")
        else:
            print("Invalid input. Select y or n.")
            sys.exit(-1)
    else:
        print("Exiting program...")
        sys.exit()
