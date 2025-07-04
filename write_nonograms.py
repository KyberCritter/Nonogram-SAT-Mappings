
import sys
from src.nonogram_sat import (
    sat_from_file, brute_force_sat,
    convert_sat_to_nonogram, write_nonogram,
)

if __name__ == "__main__":
    if(len(sys.argv) > 1):
        filename = sys.argv[1]
        try:
            sat = sat_from_file(filename)
        except:
            raise Exception("Error reading file")
    else:
        raise Exception("No filename argument provided")
    
    print(f"SAT: {sat.print_with_letters()}")
    # print("Brute force solution: " + str(brute_force_sat(sat)))
    if(len(brute_force_sat(sat)) > 0):
        print("Satisfiable")
    else:
        print("Not satisfiable")
    # print("All solutions:\n" + str(return_all_sat_solutions(sat)))
    # print("Clue sets: " + str(sat_to_clue_sets(sat)))
    # print("Key sets: " + str(sat_to_key_sets(sat)))
    nonogram = convert_sat_to_nonogram(sat)
    print(f"x_clues: {nonogram.x_clues}")
    print(f"y_clues: {nonogram.y_clues}")
    print(f"Key:\n{nonogram.correct_grid}")

    option = input("Write nonogram to file? (y/n): ")
    if option.lower() == "y":
        filename = input("Enter filename: ")
        print(f"Wrote nonogram to {write_nonogram(nonogram, filename)}")
