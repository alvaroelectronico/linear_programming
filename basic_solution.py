from inverse import inverse
import numpy as np
from latex_editing import *



class BasicSolution():

    FORM_VB = "V^B = c-c^BB^{-1}A"
    FORM_piB = "\pi^B = c^BB^{-1}"
    FORM_pB = "p^B = B^{-1}A"
    FORM_uB = "u^B=B^{-1}b"
    FORM_zB_uB = "z^B=c^Bu^B"
    FORM_zB_x = "z^B=cx"

    def __init__(self, lp_model, basic_vars_id):

        # self.lp_model = lp_model
        self.basic_vars_id = basic_vars_id
        self.A = lp_model.A
        self.c2 = lp_model.c2
        self.c1 = lp_model.c1
        self.b = lp_model.b
        self.num_r_vars = lp_model.num_r_vars


        self.B = self.A[:, basic_vars_id]
        self.cB = self.c2[basic_vars_id]
        self.invB = inverse(self.B)
        self.piB = np.dot(self.cB.T, self.invB)
        self.pB = np.dot(self.invB, self.A)
        self.uB = np.dot(self.invB, self.b)
        self.xB = [0 for i in range(self.A.shape[1])]
        for i, val in enumerate(self.uB):
            self.xB[basic_vars_id[i]] = val[0]
        self.xB = np.array([self.xB]).reshape(-1,1)
        self.vB = self.c2.T - np.dot(self.cB.T, self.pB)

        self.cB_f1 = self.c1[basic_vars_id]
        self.piB_f1 = np.dot(self.cB_f1.T, self.invB)
        self.vB_f1 = self.c1.T - np.dot(self.cB_f1.T, self.pB)

        self.z_f1 = np.dot(self.c1.T, self.xB)
        self.z = np.dot(self.c2.T, self.xB)

        self.num_vars = lp_model.num_vars
        self.num_s_vars = lp_model.num_s_vars
        self.num_r_vars = lp_model.num_r_vars 
        self.num_total_vars = lp_model.num_vars + lp_model.num_s_vars + lp_model.num_r_vars

        # Asignar first_feasible_base solo si existe en lp_model
        try:
            if hasattr(lp_model, 'first_feasible_base'):
                self.simplex_first_feasible_base = lp_model.first_feasible_base
        except AttributeError:
            pass  # No hacer nada si no existe el atributo

        self.var_names = lp_model.var_names

        self.tableau_tex = ""

        # base_info = BasicSolutionNT(*arrays_to_fraction(base_info))

    def tableau_basic_sol_tex(self, with_artificials: bool = True, frac_command: bool = True):

        str = ""

        # OF and reduced costs for phase 1 if they apply (there are artificial variables or it is the first
        # feasible base for the second phase).
        artificial_variables_exist = len([i for i in self.basic_vars_id if i >= self.num_vars + self.num_s_vars]) > 0
        is_fist_feasible_sol_phase2 = False
        try:
            if self.simplex_first_feasible_base != None:
                is_fist_feasible_sol_phase2 = set(self.basic_vars_id) == set(self.simplex_first_feasible_base)
        except AttributeError:
            pass  # No hacer nada si no existe el atributo

        if artificial_variables_exist or is_fist_feasible_sol_phase2:
            str += "Phase 1 & {} ".format(fraction_to_tex(-self.z_f1[0][0], use_dolar=True, frac_command=frac_command))
            for i, value in enumerate(self.vB_f1[0]):
                if i == self.num_vars + self.num_s_vars and not with_artificials:
                    break
                str += "& {} ".format(fraction_to_tex(value, use_dolar=True, frac_command=frac_command))
            str += "\\\\ \n"

        # OF and reduced costs for phase 2
        str += "Phase 2 & {} ".format(fraction_to_tex(-self.z[0][0], use_dolar=True, frac_command=frac_command))
        for i, n in enumerate(self.vB[0]):
            if i == self.num_vars + self.num_s_vars and not with_artificials:
                break
            str += "& {} ".format(fraction_to_tex(n, use_dolar=True, frac_command=frac_command))
        str += "\\\\ \n"

        # Horizontal line to seprate reduced cost from the rest of the table
        str += "\hline\n"

        # Rows for subtitution rates
        for i in range(0, self.A.shape[0]):
            str += "${}$".format(self.var_names[self.basic_vars_id[i]])
            str += " & {} ".format(fraction_to_tex(self.uB[i][0], frac_command=frac_command))
            for j in range(0, self.num_total_vars):
                if j == self.num_vars + self.num_s_vars and not with_artificials:
                    break
                str += " & {}".format(fraction_to_tex(self.pB[i][j], use_dolar=True, frac_command=frac_command))
            str += "\\\\ \n"
        str += "\hline\n"
        return str

    def pB_tex(self, formula = True, equation_env=True, with_artificials=False, frac_command=True):
        str = ""

        if formula:
            str += self.FORM_pB + " = "

        if with_artificials:
            str += operations_to_tex([self.invB, self.A, " = ", self.pB], frac_command=frac_command)
        else:
            str += operations_to_tex([self.invB, self.A[:, :-self.num_r_vars], " = ", self.pB[:, :-self.num_r_vars]]
                                     ,frac_command=frac_command)

        if equation_env:
            str = create_equation(str)
        return str

    def piB_tex(self, formula=True, equation_env=True, frac_command=True):
        str = ""

        if formula:
            str += self.FORM_piB + " = "

        str += operations_to_tex([self.cB.T, self.invB, " = ", self.piB], frac_command=frac_command)

        if equation_env:
            str = create_equation(str)
        return str

    def uB_tex(self, formula=True, equation_env=True, frac_command=True):
        str = ""

        if formula:
            str += self.FORM_uB + " = "

        str += operations_to_tex([self.invB, self.b, " = ", self.uB], frac_command=frac_command)

        if equation_env:
            str = create_equation(str)
        return str

    def zB_uB_tex(self, formula=True, equation_env=True, frac_command=True):
        str = ""

        if formula:
            str += self.FORM_zB_uB + " = "

        str += operations_to_tex([self.cB.T, self.uB, " = ", self.z], frac_command=frac_command)

        if equation_env:
            str = create_equation(str)
        return str

    def zB_x_tex(self, formula=True, equation_env=True, x_transposed=False, frac_command=True):
        str = ""

        if formula:
            str += self.FORM_zB_x + " = "

        if x_transposed:
            str += operations_to_tex([self.c2.T, self.xB.T, "^T = ", self.z], frac_command=True)
        else:
            str += operations_to_tex([self.c2.T, self.xB, " = ", self.z], frac_command=True)

        if equation_env:
            str = create_equation(str)
        return str

    def vB_tex(self, formula=True, equation_env=True, with_artificials=False, frac_command=True):
        str = ""

        if formula:
            str += self.FORM_VB + " = "

        if with_artificials:
            str += operations_to_tex([self.c2.T, " - ", self.cB.T, self.invB, self.A, " = ", self.vB],
                                     frac_command=frac_command)
        else:
            str += operations_to_tex([self.c2[:-self.num_r_vars].T, " - ", self.cB.T, self.invB,
                                     self.A[:, :-self.num_r_vars], " = ", self.vB[:, :-self.num_r_vars]],
                                     frac_command=frac_command)

        if equation_env:
            str = create_equation(str)
        return str

    def invB_tex(self, equation_env=True, frac_command=True):
        str = "B^{-1} ="
        str += matrix_to_tex(self.invB, frac_command=frac_command)
        if equation_env:
            str = create_equation(str)
        return str

    def B_tex(self, equation_env=True, frac_command=True):
        str = "B ="
        str += matrix_to_tex(self.B, frac_command=frac_command)
        if equation_env:
            str = create_equation(str)
        return str


