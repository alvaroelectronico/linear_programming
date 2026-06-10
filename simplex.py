from fractions import Fraction
from warnings import warn
from collections import namedtuple
import numpy as np
# from mpmath.functions.rszeta import coef

BasicSolution = namedtuple(
    "basic_solution", ["B", "cB", "uB", "pB", "piB", "xB", "z", "invB", "VB", "cB_f1", "p1B_f1", "vB_f1", "z_f1"]
)


class Simplex(object):
    def __init__(self, num_vars, constraints, objective_function, method='simplex'):
        """
        num_vars: Number of variables

        equations: A list of strings representing constraints
        each variable should be start with x followed by a underscore
        and a number
        eg of constraints
        ['1x_1 + 2x_2 >= 4', '2x_3 + 3x_1 <= 5', 'x_3 + 3x_2 = 6']
        Note that in x_num, num should not be more than num_vars.
        Also single spaces should be used in expressions.

        objective_function: should be a tuple with first element
        either 'min' or 'max', and second element be the equation
        eg 
        ('min', '2x_1 + 4x_3 + 5x_2')

        For solution finding algorithm uses two-phase simplex method
        """
        self.method = method
        self.num_vars = num_vars
        self.constraints = constraints
        self.objective_sense = objective_function[0]
        self.objective_function = objective_function[1]
        self.constraint_sense = [""]*len(self.constraints)

        # Building all items and info for the simplex method.
        # coeff_matrix: list containing the full matrix:
        # * element 0: list with reduced costs and obj. function value
        # * elements 1 to no. constraints: list with B^(-1)A and B^(-1)
        # r_rows is a list containing the indices of coeff_matrix corresponding to rows with artif. vars.
        # num_s_vars (num_r_vars): no. of slack (artifitial) vars.
        # b: constraints RHS
        # A: A matrix (no. constraints x no. vars)

        self.coeff_matrix = np.array
        self.s_rows = int
        self.r_rows = int
        self.num_r_vars = int
        self.num_r_vars = int
        self.c1 = np.array
        self.c2 = np.array
        self.A = np.array
        self.b = np.array

        # all_solutions is a list with as many namedtuple solutions as iterations of the simplex method
        self.all_bases = list()
        self.first_feasible_base = list()
        self.last_base = list()
        self.is_infeasible = False

        self.solve_model(method=self.method)

    def solve_model(self, method='simplex'):

        self._construct_matrix_from_constraints(method=method)

        if method == 'simplex':
            self._simplex_phase1()
            # TO-DO: stop if problem is infeasible
            if self.is_infeasible:
                self.first_feasible_base = None
                print("Infeasible problem")
            else:
                self.first_feasible_base = self.all_bases[len(self.all_bases) - 1]
                self._simplex_phase2()
                self.optimize_val = self.coeff_matrix[0][-1]
        elif method == 'lemke':
            self._lemke()
        else:
            raise ValueError("The argument 'method' is not accepted.")

    def _construct_matrix_from_constraints(self, method='simplex'):

        if not method in ['simplex', 'lemke']: raise ValueError("Method {} not supported".format(method))

        num_s_vars = 0  # number of slack variables
        num_r_vars = 0  # number of artificial variables

        # Inicializar constraint_sense con el tamaño correcto
        self.constraint_sense = [""] * len(self.constraints)

        if method == 'simplex':
            for i, expression in enumerate(self.constraints):
                if '<=' in expression:
                    self.constraint_sense[i] = '<='
                    num_s_vars += 1
                elif '>=' in expression:
                    self.constraint_sense[i] = '>='
                    num_s_vars += 1
                    num_r_vars += 1
                elif '=' in expression:
                    self.constraint_sense[i] = '='
                    num_r_vars += 1
        else:
            for i, expression in enumerate(self.constraints):
                if '<=' in expression:
                    self.constraint_sense[i] = '<='
                    num_s_vars += 1
                elif '>=' in expression:
                    self.constraint_sense[i] = '>='
                    num_s_vars += 1

        total_vars = self.num_vars + num_s_vars + num_r_vars

        # coeff_matrix has as many rows as constraints + 1 (for the objective_sense funcion)
        # and as many columns as the total no. of vars + 1 (for the value of z and the basic vars.)
        coeff_matrix = [[Fraction("0/1") for i in range(total_vars+1)] for j in range(len(self.constraints)+1)]

        first_s_index = self.num_vars # starting index for slack variables
        first_r_index = self.num_vars + num_s_vars # starting index for artifitial variables
        r_rows = list()  # stores the non-zero index of art. variables
        s_rows = list()  # stores the non-zero index of slack. variable

        # These are counters to modify the objective_sense function for phase according the
        # constraints nature (<=, = or >=)
        count_s_index = first_s_index
        count_r_index = first_r_index

        for i in range(1, len(self.constraints) + 1):
            constraint = self.constraints[i - 1].split(' ')
            for j in range(len(constraint)):
                if '_' in constraint[j]:
                    coeff, index = constraint[j].split('_')
                    if constraint[j - 1] == '-':
                        coeff_matrix[i][int(index) - 1] = -Fraction(coeff[:-1]).limit_denominator()
                    else:
                        coeff_matrix[i][int(index) - 1] = Fraction(coeff[:-1]).limit_denominator()

                elif constraint[j] == '<=':
                    coeff_matrix[i][count_s_index] = Fraction("1/1")  # add surplus variable
                    count_s_index += 1
                    s_rows.append(i)
                elif constraint[j] == '>=':
                    if method == 'simplex':
                        coeff_matrix[i][count_s_index] = Fraction("-1/1")  # slack variable
                        coeff_matrix[i][count_r_index] = Fraction("1/1")   # r variable
                        count_s_index += 1
                        count_r_index += 1
                        s_rows.append(i)
                        r_rows.append(i)
                    else:
                        coeff_matrix[i][count_s_index] = Fraction("-1/1")  # slack variable
                        count_s_index += 1
                        s_rows.append(i)
                elif constraint[j] == '=':
                    if method == 'simplex':
                        coeff_matrix[i][count_r_index] = Fraction("1/1")  # r variable
                        count_r_index += 1
                        r_rows.append(i)
                    else:
                        raise ValueError("Constraints of type = are not supported for the Lemke method")

            coeff_matrix[i][-1] = Fraction(constraint[-1] + "/1")

        # c1 has the OF coefficients for the first phase
        c1 = [Fraction("0/1") for i in range(self.num_vars + num_s_vars)]
        c1.extend([-Fraction("1/1") for i in range(num_r_vars)])

        # c2 has the OF coefficients for the second phase (original problem)
        c2 = [Fraction("0/1") for i in range(total_vars)]
        objective_function_coeffs = self.objective_function.split()
        for i in range(len(objective_function_coeffs)):
            if '_' in objective_function_coeffs[i]:
                coeff, index = objective_function_coeffs[i].split('_')
                if objective_function_coeffs[i - 1] == '-':
                    c2[int(index) - 1] = Fraction("-" +coeff[:-1] + "/1")
                else:
                    c2[int(index) - 1] = Fraction(coeff[:-1] + "/1")

        c1 = np.array(c1).reshape(-1, 1)
        c1 = array_to_fraction(c1)

        c2 = np.array(c2).reshape(-1, 1)
        c2 = array_to_fraction(c2)
        if self.method == 'lemke' and 'min' in self.objective_sense:
            c2 = -c2

        A = [[coeff_matrix[i][j] for j in range(len(coeff_matrix[0])-1)] for i in range(1, len(coeff_matrix))]
        A = np.array(A)
        A = array_to_fraction(A)

        b = [coeff_matrix[i][len(coeff_matrix[0])-1] for i in range(1, len(coeff_matrix))]
        b = np.array(b).reshape(-1,1)
        b = array_to_fraction(b)

        self.coeff_matrix = coeff_matrix
        self.s_rows = s_rows
        self.r_rows = r_rows
        self.num_s_vars = num_s_vars
        self.num_r_vars = num_r_vars
        self.c1 = c1
        self.c2 = c2
        self.A = A
        self.b = b
        self.total_vars = self.num_vars + self.num_s_vars + self.num_r_vars
        # var_names ia A list containing the names
        # x_1...x_{num_vars}, h_1...h_{num_s_vars}, a_1...a_{num_r_vars}
        # to be displayed when tableaux are built
        self.var_names = self._name_variables()

        return 0

    def _simplex_phase1(self):
        # Objective function here is minimize r1+ r2 + r3 + ... + rn

        # first_r_index contains the position of the first artificial variable
        first_r_index = self.num_vars + self.num_s_vars
        count_r_index = first_r_index

        # basic_vars initialized to a list with as many elements as constraints.
        self.basic_vars = [0 for i in range(len(self.coeff_matrix)-1)]

        # Changing first row (index = 0) of coeff_matrix according to the phase 1
        for i in range(first_r_index, len(self.coeff_matrix[0])-1):
            self.coeff_matrix[0][i] = Fraction("-1/1")

        # Computing reduced costs for first base (where slack and art. variables are basic)
        for i in self.r_rows:
            self.coeff_matrix[0] = sum_rows(self.coeff_matrix[0], self.coeff_matrix[i])
            # self.basic_vars[i] = count_r_index
            count_r_index += 1

        # Basic variable indices corresponding to art. variables are stored in basic_vars
        for i in range(len(self.basic_vars)):
            base_column = [Fraction(0, 1)] * len(self.basic_vars)
            # Set the value at position i to 1
            base_column[i] = Fraction(1, 1)
            for j in range(self.total_vars):
                column_a = [row[j] for row in self.coeff_matrix[1:]]
                if base_column == column_a:
                    self.basic_vars[i] = j
                    break

        # Run the simplex iterations
        # Selecting the input variable
        key_column = max_index(self.coeff_matrix[0][:-1])
        # There are candidate input variables if the corresponding reduced cost is > 0
        condition = self.coeff_matrix[0][key_column] > 0
        # The tableau and the current base is stored in tableaux_list and all_bases, respect.
        # self.tableaux_list.append(self.tableau_tex_from_coeff_matrix())
        self.all_bases.append([int(i) for i in self.basic_vars])

        while condition is True:
            # The ouput variable is selected via find_key_row method
            key_row = self._find_key_row_simplex(key_column=key_column)
            # The output var. is replaced with the input var. in basic_vars
            self.basic_vars[key_row - 1] = key_column
            # Getting the value of the pivot
            pivot = self.coeff_matrix[key_row][key_column]
            # Pivoting: dividing the pivot-row by the pivot.
            self._normalize_to_pivot(key_row, pivot)
            # Pivoting: making all values (but the pivot) of the pivot-column 0
            self._make_key_column_zero(key_column, key_row)
            # Selecting the input variable
            key_column = max_index(self.coeff_matrix[0][:-1])
            # There are candidate input variables if the corresponding reduced cost is > 0
            condition = self.coeff_matrix[0][key_column] > 0
            # The bars ids are stored
            self.all_bases.append([int(i) for i in self.basic_vars])

        # If any art. var is basic the problem is infeseasible. No phase 2 required.
        # TO-DO. If all art. vars are 0, the problem is feaseible
        for i in self.basic_vars:
            if i >= first_r_index:
                self.is_infeasible = True

    def _simplex_phase2(self):

        # Replacing element 0 in coeff_matrix (OF coeff. for phase 2).
        self._update_objective_function()

        # Getting reduced
        for row, column in enumerate(self.basic_vars):
            if self.coeff_matrix[0][column] != 0:
                self.coeff_matrix[0] = sum_rows(self.coeff_matrix[0],
                                                multiply_const_row(-self.coeff_matrix[0][column],
                                                                   self.coeff_matrix[row + 1]))

        # Selecting the input variable and checking if there is room for improvement
        # art. vars. are not eligible whenr chosing the input variable
        if 'max' in self.objective_sense.lower():
            key_column = max_index(self.coeff_matrix[0][:self.num_vars + self.num_s_vars])
            condition = self.coeff_matrix[0][key_column] > 0
        else:
            key_column = min_index(self.coeff_matrix[0][:self.num_vars + self.num_s_vars])
            condition = self.coeff_matrix[0][key_column] < 0

        # self.tableaux_list.append(self.tableau_tex_from_coeff_matrix())
        # 9self.all_bases.append([int(i) for i in self.basic_vars[1:]])

        while condition is True:

            key_row = self._find_key_row_simplex(key_column=key_column)
            if key_row == -1: # The problem is unbounded
                break
            self.basic_vars[key_row - 1] = key_column
            pivot = self.coeff_matrix[key_row][key_column]
            self._normalize_to_pivot(key_row, pivot)
            self._make_key_column_zero(key_column, key_row)

            # r vars are not considered for chosing the pivot column
            if 'max' in self.objective_sense.lower():
                key_column = max_index(self.coeff_matrix[0][:self.num_vars + self.num_s_vars])
                condition = self.coeff_matrix[0][key_column] > 0
            else:
                key_column = min_index(self.coeff_matrix[0][:self.num_vars + self.num_s_vars])
                condition = self.coeff_matrix[0][key_column] < 0
            # self.tableaux_list.append(self.tableau_tex_from_coeff_matrix())
            self.all_bases.append([int(i) for i in self.basic_vars])

        solution = {}
        for i, var in enumerate(self.basic_vars):
            if var < self.num_vars:
                solution['x_' + str(var + 1)] = self.coeff_matrix[i + 1][-1]

        for i in range(0, self.num_vars):
            if i not in self.basic_vars:
                solution['x_' + str(i + 1)] = Fraction("0/1")

        self._check_alternate_solution()

        self.solution = solution
        self.last_base = self.all_bases[len(self.all_bases) - 1]

    def _lemke(self):

        # Replacing element 0 in coeff_matrix (OF coeff. for phase 2).
        self._update_objective_function()

        # Checking that c_j >= 0 if minimizing OF and c_j <= 0 if maximizing OF:
        if "max" in self.objective_sense:
            if len([i for i in self.coeff_matrix[0] if i > 0]) > 0:
                raise ValueError("Objective fuction to be maximized with coefficient > 0")
        elif "min" in self.objective_sense:
            if len([i for i in self.coeff_matrix[0] if i < 0]) > 0:
                raise ValueError("Objective fuction to be minimized with coefficient < 0")
            else:
                self.coeff_matrix[0] = [-i for i in self.coeff_matrix[0]]

        # Changing sign off contraints if sense is >=
        for j in range(len(self.constraints)):
            if self.constraint_sense[j] == ">=":
            #self.coeff_matrix = [[-i for i in inner_list] for inner_list in self.coeff_matrix]
                self.coeff_matrix[j + 1] = [-i for i in self.coeff_matrix[j + 1]]

        self.basic_vars = [i for i in range(self.num_vars, self.total_vars)]
        self.all_bases.append([int(i) for i in self.basic_vars])

        self.uB = [inner_list[-1] for inner_list in self.coeff_matrix[1:]]
        key_row = min_index(self.uB) + 1
        condition = any(u < 0 for u in self.uB)

        while condition is True:            
            key_column = self._find_key_column_lemke(key_row=key_row)
            if key_column == -1:  # The problem is infeasible
                raise ValueError("Infeasible problem")
                break
            self.basic_vars[key_row - 1] = key_column
            pivot = self.coeff_matrix[key_row][key_column]
            self._normalize_to_pivot(key_row, pivot)
            self._make_key_column_zero(key_column, key_row)

            self.uB = [inner_list[-1] for inner_list in self.coeff_matrix[1:]]
            key_row = min_index(self.uB) + 1
            condition = any(u < 0 for u in self.uB)            
            self.all_bases.append([int(i) for i in self.basic_vars])

            

        solution = {}
        for i, var in enumerate(self.basic_vars):
            if var < self.num_vars:
                solution['x_' + str(var + 1)] = self.coeff_matrix[i + 1][-1]

        for i in range(0, self.num_vars):
            if i not in self.basic_vars:
                solution['x_' + str(i + 1)] = Fraction("0/1")

        self._check_alternate_solution()

        self.solution = solution
        self.last_base = self.all_bases[len(self.all_bases) - 1]

    def _find_key_row_simplex(self, key_column):
        min_val = float("inf")
        min_i = 0
        for i in range(1, len(self.coeff_matrix)):
            if self.coeff_matrix[i][key_column] > 0:
                val = self.coeff_matrix[i][-1] / self.coeff_matrix[i][key_column]
                if val < min_val:
                    min_val = val
                    min_i = i
        if min_val == float("inf"):
            warn("Unbounded problem")
            return -1
        if min_val == 0:
            warn("Degeneracy")
        return min_i

    def _find_key_column_lemke(self, key_row):
        min_val = float("inf")
        min_j = 0
        for j in range(self.total_vars):
            if self.coeff_matrix[key_row][j] < 0:
                val = self.coeff_matrix[0][j] / self.coeff_matrix[key_row][j]
                if val < min_val:
                    min_val = val
                    min_j = j
        if min_val == float("inf"):
            warn("Unbounded problem")
            return -1
        if min_val == 0:
            warn("Multiple optima")
        return min_j

    def _normalize_to_pivot(self, key_row, pivot):
        for i in range(len(self.coeff_matrix[0])):
            self.coeff_matrix[key_row][i] /= pivot

    def _make_key_column_zero(self, key_column, key_row):
        num_columns = len(self.coeff_matrix[0])
        for i in range(len(self.coeff_matrix)):
            if i != key_row:
                factor = self.coeff_matrix[i][key_column]
                for j in range(num_columns):
                    self.coeff_matrix[i][j] -= self.coeff_matrix[key_row][j] * factor

    def _delete_r_vars(self):
        for i in range(len(self.coeff_matrix)):
            non_r_length = self.num_vars + self.num_s_vars + 1
            length = len(self.coeff_matrix[i])
            while length != non_r_length:
                del self.coeff_matrix[i][non_r_length-1]
                length -= 1

    def _update_objective_function(self):
        self.coeff_matrix[0] = [Fraction("0/1") for i in range(self.total_vars + 1)]
        objective_function_coeffs = self.objective_function.split()
        for i in range(len(objective_function_coeffs)):
            if '_' in objective_function_coeffs[i]:
                coeff, index = objective_function_coeffs[i].split('_')
                if objective_function_coeffs[i-1] == '-':
                    self.coeff_matrix[0][int(index)-1] = Fraction("-" + coeff[:-1] + "/1")
                else:
                    self.coeff_matrix[0][int(index)-1] = Fraction(coeff[:-1] + "/1")

    def _check_alternate_solution(self):
        for i in range(len(self.coeff_matrix[0])):
            if self.coeff_matrix[0][i] and i not in self.basic_vars:
                warn("Alternate Solution exists")
                break

    def _name_variables(self):
        var_names = list()
        for i in range(1, self.num_vars+1):
            var_names.append("x_{}".format(i))
        for i in range(0, self.num_s_vars):
            var_names.append("h_{}".format(self.s_rows[i]))
        for i in range(0, self.num_r_vars):
            var_names.append("a_{}".format(self.r_rows[i]))
        return var_names


def sum_rows(row1, row2):
    row_sum = [0 for i in range(len(row1))]
    for i in range(len(row1)):
        row_sum[i] = row1[i] + row2[i]
    return row_sum

def max_index(row):
    max_i = 0
    for i in range(0, len(row)):
        if row[i] > row[max_i]:
            max_i = i
    return max_i

def multiply_const_row(const, row):
    mul_row = []
    for i in row:
        mul_row.append(const*i)
    return mul_row

def min_index(row):
    min_i = 0
    for i in range(0, len(row)):
        if row[min_i] > row[i]:
            min_i = i
    return min_i

def array_to_fraction(arr):
    to_fraction = lambda t: Fraction(t).limit_denominator()
    vfunc = np.vectorize(to_fraction)
    return vfunc(arr)


if __name__== "__main__":
    # A Model
    objectiveA = ("min", "3x_1 + 2x_2")
    constraintsA = [
        "2x_1 + 4x_2 >= 80",
        "4x_1 + 3x_2 <= 60"
    ]
    problemA = Simplex(num_vars=2, constraints=constraintsA, objective_function=objectiveA, method='lemke')
    problemA.solve_model()

    # problem.gen_solving_basic_solutions()
    # opt_basic_sol = problem.solving_basic_solutions[-1]

    print("done")
