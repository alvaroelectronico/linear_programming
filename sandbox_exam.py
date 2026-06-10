from old_code.old_problem_class import *
from pyperclip import *

# from problem_class import *

objective = ('maximize', '- 12x_1 - 2x_2 + 1x_3')
constraints = ['3x_1 + 2x_2 + 1x_3 >= 3',
               '4x_1 + 1x_2 - 1x_3 >= 4']

problem = LP_Model(num_vars=3, objective_function=objective, constraints=constraints)
print(problem.formulation_phase1_tex())

copy(problem.compose_tableau(problem.simplex_bases, with_artificials=True))

copy(problem.compose_tableau(problem.simplex_bases, with_artificials=False))
copy(problem.compose_tableau(problem.simplex_bases, with_artificials=False))
#
#
# print(problem.compose_tableau([problem.solving_bases[0]]))
#
#
#
# problem.solving_bases
# problem.gen_all_bases_info()
# problem.bases_info.keys()
# problem.bases_info[2, 3, 6, 7].pB
#
# # array_to_fraction(problem.)
#
# print(matrix_to_tex(array_to_fraction(problem.c2)))
#
#
#
#
#
# basic_solution_to_fraction(problem.bases_info[2, 3, 6, 7])
