
import sys

from src.nonogram_sat import (
    sat_from_file, brute_force_sat,
    return_all_sat_solutions,
)


if __name__ == "__main__":
    # args:
    # 1: filename
    if(len(sys.argv) > 1):
        filename = sys.argv[1]
        try:
            sat = sat_from_file(filename)
        except:
            raise Exception("Error reading file")
    else:
        raise Exception("No filename argument provided")

    print("SAT: " + str(sat))
    print("SAT as letters: " + str(sat.print_with_letters()))
    # print("Variables (" + str(len(sat.variables)) + "): " + str(sat.variables))
    satisfiable = len(brute_force_sat(sat)) > 0
    if(satisfiable):
        print("Satisfiable")
        all_solutions = return_all_sat_solutions(sat)
        print("All " + str(len(all_solutions)) + " solutions:")
        for solution in all_solutions:
            print(solution)
    else:
        print("Not satisfiable")