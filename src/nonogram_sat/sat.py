# Scott Ratchford 2025.07.03

import math
from nonogram import *


class Clause:
    def __init__(self, terms):
        self.terms = terms
        self.variables = []
        self.dupes = 0
        for var in self.terms:
            if abs(var) not in self.variables:
                self.variables.append(abs(var))
                self.variables.sort()   # sort variables in ascending order
            else:
                self.dupes += 1

    def evaluate(self, values):
        varIndicies = [abs(x) - 1 for x in self.terms]
        attemptValues = []
        for i in range(len(values)):    # reduce the values list to only the values that correspond to the variables in this clause
            if(i in varIndicies):
                attemptValues.append(values[i])
        for i, term in enumerate(self.terms):
            if((values[abs(term)-1] and term > 0) or (not values[abs(term)-1] and self.terms[i] < 0)):
                return True
        return False

    def print_with_letters(self):
        s = ""
        for index, term in enumerate(self.terms):
            if(term > 0):
                s += str(chr(term+64))
            else:
                s += "~" + str(chr(abs(term)+64))
            if(index < len(self.terms) - 1):
                s += " v "
        return s 

    def __str__(self):
        s = ""
        for index, term in enumerate(self.terms):
            if(term > 0):
                s += str(term)
            else:
                s += "~" + str(abs(term))
            if(index < len(self.terms) - 1):
                s += " v "
        return s
    
    def __len__(self):
        return len(self.terms)

class SAT:
    def __init__(self):
        self.clauses = []
        self.variables = []
    
    def add_clause(self, clause):
        self.clauses.append(clause)
        for var in clause.terms:
            if abs(var) not in self.variables:
                self.variables.append(abs(var))
                self.variables.sort()   # sort variables in ascending order
    
    def evaluate(self, values):
        for clause in self.clauses:
            if(not clause.evaluate(values)):
                return False
        return True

    def print_with_letters(self):
        s = ""
        for index, clause in enumerate(self.clauses):
            s += "(" + str(clause.print_with_letters()) + ")"
            if(index < len(self.clauses) - 1):
                s += " ^ "
        if(len(s) > 0): return s
        else: return "(empty SAT)"

    def __str__(self):
        s = ""
        for index, clause in enumerate(self.clauses):
            s += "(" + str(clause) + ")"
            if(index < len(self.clauses) - 1):
                s += " ^ "
        return s

    def __len__(self):
        return len(self.clauses)

def sat_from_file(filename) -> SAT:
    try:
        file = open(filename, "r")
        lines = file.readlines()
        file.close()
    except:
        raise Exception("Error reading file " + filename)

    sat = SAT()
    for line in lines[1:-1]:    # skip first and last lines
        terms = [int(x) for x in line.split()]
        sat.add_clause(Clause(terms))
    return sat

def brute_force_sat(sat: SAT) -> list:
    for i in range(int(math.pow(2, len(sat.variables)))):
        values = [bool(int(x)) for x in bin(i)[2:].zfill(len(sat.variables))]
        if(sat.evaluate(values)):
            return values
    return []   # if no combination of values satisfies the SAT

def return_all_sat_solutions(sat: SAT) -> list:
    solutions = []
    for i in range(int(math.pow(2, len(sat.variables)))):
        values = [bool(int(x)) for x in bin(i)[2:].zfill(len(sat.variables))]
        if(sat.evaluate(values)):
            solutions.append(values)
    return solutions

def sat_to_file(sat: SAT, filename: str) -> bool:
    try:
        file = open(filename, "w")
        file.write(str(len(sat.variables)) + "\n")
        for clause in sat.clauses:
            for index, term in enumerate(clause.terms):
                file.write(str(term))
                if(index < len(clause.terms) - 1):
                    file.write(" ") # space between terms, no trailing space
            file.write("\n")
        file.write("$")
        file.close()
        return True
    except:
        return False

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
