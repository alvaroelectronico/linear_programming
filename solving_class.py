from simplex import Simplex
from basic_solution import BasicSolution
import numpy as np
from pyperclip import *
from latex_editing import *
from gurobi_model import GurobiModel


class LP_Problem():

    def __init__(self, num_vars, constraints, objective_function, method='simplex', solve_with_gurobi=True):
        # Atributes of LP_Model objects
        self.method = method
        self.model = Simplex(num_vars, constraints, objective_function, method) # simplex object from Simplex class

        self.c1 = self.model.c1.astype('float') # List with coefficients for the objective_sense function of the first phase
        self.c2 = self.model.c2.astype('float') # List with coefficients for the objective_sense function of the second phase
        self.b = self.model.b.astype('float') # LHS of the constraints
        self.A = self.model.A.astype('float') # Coefficient matrix of the constraints
        self.var_names = self.model.var_names # List with the variable names [`x_1', 'x_2'... 'h_1'...'a_1'...]
        self.num_vars = self.model.num_vars # No. of variables (not including slack or artificial variables
        self.num_s_vars = self.model.num_s_vars # No. of slack variables
        self.num_r_vars = self.model.num_r_vars # No. of artificial variables
        self.num_total_vars = self.num_vars + self.num_s_vars + self.num_r_vars # No. of all variables (including artificial ones)
        self.bases_info = dict()  # a dictionary with a BasicSolutionNT named tuple for every element in bases

        # bases are stored as lists with var. ids
        self.simplex_first_feasible_base = self.model.first_feasible_base # var. ids for the first feasible solution found when
        # solving using the 2-phase method
        # Generating a dictionary with all simplex bases and their correspondint information
        self.sense = self.model.objective_sense
        self.objective_function = self.model.objective_function
        self.constraints = self.model.constraints

        self.solving_bases = list()
        self.solving_basic_solutions = []

        self.wip_bases = list()
        self.wip_basic_solutions = list()

        self.incumbent_base = list()
        self.incumbent_basic_solution = None

        self.gen_solving_basic_solutions()

        # Crear instancia del modelo Gurobi
        # Extraer solo la expresión de la función objetivo
        obj_expr = objective_function[1] if isinstance(objective_function, tuple) else objective_function
        
        if solve_with_gurobi:
            self.gurobi = GurobiModel(
                num_vars=self.num_vars,
                A=self.A,                    # Matriz de coeficientes ya parseada
                b=self.b,                    # Vector de términos independientes
                c=self.c2,                   # Coeficientes de la función objetivo
                var_names=self.var_names[:self.num_vars],  # Nombres de variables originales
                sense=self.sense,
                constraint_sense=self.model.constraint_sense  # Lista con los sentidos de las restricciones
            )


    def gen_basic_solutions(self, bases):
        basic_solutions = list()

        for basic_vars_id in bases:
            basic_solution = BasicSolution(self.model, basic_vars_id)
            basic_solutions.append(basic_solution)
            # self.solving_basic_solutions[i] = basic_solution

        return basic_solutions

    def gen_solving_basic_solutions(self) -> None:
        # Retrieving bases from simplex self.model instance
        self.solving_bases = self.model.all_bases  # list with all bases (ordered as visited) when solving with the Simplex method
        self.solving_basic_solutions = self.gen_basic_solutions(self.solving_bases)

    def formulation_tex(self) -> str:
        """
        formulation_tex generates the latex format string for the original problem formulation
        :return: tex format string
        """
        tex_str = "\\begin{equation}\n\\begin{split}\n"
        if 'min' in self.sense.lower():
            tex_str += "\mbox{min. } z = " + self.objective_function + "\\\\\n"
        else:
            tex_str += "\mbox{max. } z = " + self.objective_function + "\\\\\n"
        tex_str += "s.a.:\\\\\n"
        char_to_replace = {'<=': '\\leq',
                           '>=': '\\geq'}
        for expression in self.constraints:
            # Iterate over all key-value pairs in dictionary
            for key, value in char_to_replace.items():
                # Replace key character with value character in string
                expression = expression.replace(key, value)
            tex_str += expression + "\\\\\n"
        for i in range(1, self.num_vars + 1):
            tex_str += "x_{}".format(i)
            if i != self.num_vars:
                tex_str += ",\\,\\,"
        tex_str += "\geq 0\\\\\n"
        tex_str += "\\end{split}\n\\end{equation}"
        return tex_str

    def formulation_phase1_tex(self) -> str:
        """
        formulation_phase1_tex generates the latex format string for the first phase problem formulation
        :return: tex format string
        """
        tex_str = "\\begin{equation}\n\\begin{split}\n"

        tex_str += "\mbox{max. } z' = "
        for i, j in enumerate(self.c1):
            if j[0] < 0:
                tex_str += fraction_to_tex(array_to_fraction(j)[0]) + self.var_names[i]
            elif j[0] > 0 and i > 0:
                tex_str += " + " + fraction_to_tex(array_to_fraction(j)[0]) + self.var_names[i]
        tex_str += "\\\\\n"
        tex_str += "s.a.:\\\\\n"
        non_neg_tr = ""
        A, b = arrays_to_fraction([self.A, self.b])
        for i in range(self.A.shape[0]):
            for j in range(self.A.shape[1]):
                if A[i][j] > 0 and j > 0:
                    tex_str += "+"
                if A[i][j] != 0:
                    tex_str += fraction_to_tex(A[i][j]) + self.var_names[j]
            tex_str += " = " + fraction_to_tex(b[i][0])
            tex_str += "\\\\\n"
        tex_str += ",\,".join(self.var_names) + "\\geq 0"

        tex_str += "\\end{split}\n\\end{equation}"

        return tex_str

    def _tableau_tex_header(self, with_artificials: bool = True) -> str:
        """
        _tableau_tex_header generates the tex string for the header of a tableau for the corresponding problem
        including the tabular environment opening
        :param with_artificials: True if columns for the artifitial variables are included, False otherwise
        :return: str
        """
        str = "\\begin{center}\n\\begin{tabular}{c|c|"
        if with_artificials:
            str += "c" * self.num_total_vars
        else:
            str += "c" * (self.num_total_vars - self.num_r_vars)
        str += "|}\n"
        str += " & $z$"
        for i in range(self.num_total_vars):
            if i == self.num_vars + self.num_s_vars and not with_artificials:
                break
            str += " & ${}$".format(self.var_names[i])
        str += "\\\\ \n"
        return str

    def _tableau_tex_wrap(self) -> str:
        """
        _tableau_tex_wrap generates the final tableau rows, including the tabular environment closing
        :return: str
        """
        return "\end{tabular}\n\end{center}\n"

    def compose_tableau(self, basic_solutions: list, with_artificials: bool = True, frac_command=True) -> str:
        """
        basic_solutions generates the full tableau for a list of bases
        :param basic_solutions: list with bases (each base is a tuple with the var ids.)
        :return: tex string format with the full tableau
        """
        str = self._tableau_tex_header(with_artificials)
        for base in basic_solutions:
            str += base.tableau_basic_sol_tex(with_artificials=with_artificials, frac_command=frac_command)
            # str += self._tableau_basic_sol_tex(base, with_artificials)
        str += self._tableau_tex_wrap()
        return str

    def solve_with_gurobi(self, print_details=True, print_model=True, as_fractions=True):
        """
        Resuelve el problema usando Gurobi directamente
        """
        print("\n=== Solución usando Gurobi ===")
        return self.gurobi.solve(print_details, print_model, as_fractions)

if __name__ == "__main__":
    objective = ("max", "3x_1 + 2x_2 + 1x_3 + 2x_4")
    constraints = [
        "1x_1 + 3x_2 + 0x_3 = 60",
        "2x_1 + 1x_2 + 3x_3 + 1x_4 <= 100",
        "2x_1 + 1x_2 + 1x_3 -5x4 >= 50"
    ]
    problem = LP_Problem(num_vars=4, objective_function=objective, constraints=constraints)

    # Resolver con Gurobi y mostrar detalles
    if not problem.solve_with_gurobi(print_details=True):
        print("No se pudo encontrar una solución óptima")

    problem.gen_solving_basic_solutions()

    copy(problem.solving_basic_solutions[1].zB_uB_tex())
    copy(problem.solving_basic_solutions[1].zB_x_tex(x_transposed=True))


    copy(problem.solving_basic_solutions[0].uB_tex())

    copy(problem.solving_basic_solutions[0].vB_tex(with_artificials=True))
    copy(problem.solving_basic_solutions[0].vB_tex(with_artificials=False))

    copy(problem.solving_basic_solutions[2].piB_tex())
    copy(problem.solving_basic_solutions[2].vB_tex())

    print(problem.formulation_tex())
    print(problem.formulation_phase1_tex())
    print(problem.compose_tableau(problem.solving_basic_solutions))


    copy(problem.formulation_tex())
    copy(problem.formulation_phase1_tex())

    tableau = problem.compose_tableau(problem.solving_bases)
    copy(tableau)

    print("finished")