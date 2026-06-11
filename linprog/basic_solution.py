"""A basic solution of a linear program and its LaTeX renderings.

Given a basis (a set of basic-variable indices) this computes the textbook
quantities -- ``B``, ``B^{-1}``, substitution rates ``p^B``, reduced costs
``v^B``, dual values ``\\pi^B`` and the objective value -- and can render each
as a LaTeX equation or assemble a full simplex tableau row.
"""

from __future__ import annotations

import numpy as np

from linprog.linalg import inverse
from linprog.parsing import StandardForm
from linprog.reporting.latex import (
    create_equation,
    fraction_to_tex,
    matrix_to_tex,
    operations_to_tex,
)


class BasicSolution:
    # LaTeX formula templates shown alongside the computed values.
    FORM_VB = "V^B = c-c^BB^{-1}A"
    FORM_PI_B = "\\pi^B = c^BB^{-1}"
    FORM_PB = "p^B = B^{-1}A"
    FORM_UB = "u^B=B^{-1}b"
    FORM_ZB_UB = "z^B=c^Bu^B"
    FORM_ZB_X = "z^B=cx"

    def __init__(self, standard_form: StandardForm, basic_vars_id, first_feasible_base=None):
        sf = standard_form
        self.basic_vars_id = basic_vars_id
        self.first_feasible_base = first_feasible_base

        self.A = sf.A
        self.b = sf.b
        self.c1 = sf.c1
        self.c2 = sf.c2
        self.num_vars = sf.num_vars
        self.num_slack_vars = sf.num_slack_vars
        self.num_artificial_vars = sf.num_artificial_vars
        self.total_vars = sf.total_vars
        self.var_names = sf.var_names

        # Basis matrix and the derived textbook quantities.
        self.B = self.A[:, basic_vars_id]
        self.invB = inverse(self.B)
        self.cB = self.c2[basic_vars_id]
        self.piB = np.dot(self.cB.T, self.invB)
        self.pB = np.dot(self.invB, self.A)
        self.uB = np.dot(self.invB, self.b)

        x = [0 for _ in range(self.A.shape[1])]
        for i, value in enumerate(self.uB):
            x[basic_vars_id[i]] = value[0]
        self.xB = np.array([x]).reshape(-1, 1)

        self.vB = self.c2.T - np.dot(self.cB.T, self.pB)
        self.z = np.dot(self.c2.T, self.xB)

        # Phase-1 counterparts.
        self.cB_f1 = self.c1[basic_vars_id]
        self.piB_f1 = np.dot(self.cB_f1.T, self.invB)
        self.vB_f1 = self.c1.T - np.dot(self.cB_f1.T, self.pB)
        self.z_f1 = np.dot(self.c1.T, self.xB)

    # --- full tableau row -------------------------------------------------

    def tableau_basic_sol_tex(self, with_artificials: bool = True, frac_command: bool = True) -> str:
        artificial_column_start = self.num_vars + self.num_slack_vars
        tex = ""

        has_artificial_basic = any(i >= artificial_column_start for i in self.basic_vars_id)
        is_first_feasible_phase2 = (
            self.first_feasible_base is not None
            and set(self.basic_vars_id) == set(self.first_feasible_base)
        )

        # Phase-1 reduced-cost row (only when relevant).
        if has_artificial_basic or is_first_feasible_phase2:
            tex += "Phase 1 & {} ".format(
                fraction_to_tex(-self.z_f1[0][0], use_dollar=True, frac_command=frac_command)
            )
            for i, value in enumerate(self.vB_f1[0]):
                if i == artificial_column_start and not with_artificials:
                    break
                tex += "& {} ".format(
                    fraction_to_tex(value, use_dollar=True, frac_command=frac_command)
                )
            tex += "\\\\ \n"

        # Phase-2 reduced-cost row.
        tex += "Phase 2 & {} ".format(
            fraction_to_tex(-self.z[0][0], use_dollar=True, frac_command=frac_command)
        )
        for i, value in enumerate(self.vB[0]):
            if i == artificial_column_start and not with_artificials:
                break
            tex += "& {} ".format(
                fraction_to_tex(value, use_dollar=True, frac_command=frac_command)
            )
        tex += "\\\\ \n\\hline\n"

        # Substitution-rate rows, one per basic variable.
        for i in range(self.A.shape[0]):
            tex += "${}$".format(self.var_names[self.basic_vars_id[i]])
            tex += " & {} ".format(
                fraction_to_tex(self.uB[i][0], use_dollar=True, frac_command=frac_command)
            )
            for j in range(self.total_vars):
                if j == artificial_column_start and not with_artificials:
                    break
                tex += " & {}".format(
                    fraction_to_tex(self.pB[i][j], use_dollar=True, frac_command=frac_command)
                )
            tex += "\\\\ \n"
        tex += "\\hline\n"
        return tex

    # --- individual quantity equations ------------------------------------

    def _wrap(self, content: str, equation_env: bool) -> str:
        return create_equation(content) if equation_env else content

    def pB_tex(self, formula=True, equation_env=True, with_artificials=False, frac_command=True) -> str:
        tex = self.FORM_PB + " = " if formula else ""
        if with_artificials:
            tex += operations_to_tex([self.invB, self.A, " = ", self.pB], frac_command=frac_command)
        else:
            keep = -self.num_artificial_vars
            tex += operations_to_tex(
                [self.invB, self.A[:, :keep], " = ", self.pB[:, :keep]], frac_command=frac_command
            )
        return self._wrap(tex, equation_env)

    def piB_tex(self, formula=True, equation_env=True, frac_command=True) -> str:
        tex = self.FORM_PI_B + " = " if formula else ""
        tex += operations_to_tex([self.cB.T, self.invB, " = ", self.piB], frac_command=frac_command)
        return self._wrap(tex, equation_env)

    def uB_tex(self, formula=True, equation_env=True, frac_command=True) -> str:
        tex = self.FORM_UB + " = " if formula else ""
        tex += operations_to_tex([self.invB, self.b, " = ", self.uB], frac_command=frac_command)
        return self._wrap(tex, equation_env)

    def zB_uB_tex(self, formula=True, equation_env=True, frac_command=True) -> str:
        tex = self.FORM_ZB_UB + " = " if formula else ""
        tex += operations_to_tex([self.cB.T, self.uB, " = ", self.z], frac_command=frac_command)
        return self._wrap(tex, equation_env)

    def zB_x_tex(self, formula=True, equation_env=True, x_transposed=False, frac_command=True) -> str:
        tex = self.FORM_ZB_X + " = " if formula else ""
        if x_transposed:
            tex += operations_to_tex([self.c2.T, self.xB.T, "^T = ", self.z], frac_command=True)
        else:
            tex += operations_to_tex([self.c2.T, self.xB, " = ", self.z], frac_command=True)
        return self._wrap(tex, equation_env)

    def vB_tex(self, formula=True, equation_env=True, with_artificials=False, frac_command=True) -> str:
        tex = self.FORM_VB + " = " if formula else ""
        if with_artificials:
            tex += operations_to_tex(
                [self.c2.T, " - ", self.cB.T, self.invB, self.A, " = ", self.vB],
                frac_command=frac_command,
            )
        else:
            keep = -self.num_artificial_vars
            tex += operations_to_tex(
                [
                    self.c2[:keep].T, " - ", self.cB.T, self.invB,
                    self.A[:, :keep], " = ", self.vB[:, :keep],
                ],
                frac_command=frac_command,
            )
        return self._wrap(tex, equation_env)

    def invB_tex(self, equation_env=True, frac_command=True) -> str:
        tex = "B^{-1} =" + matrix_to_tex(self.invB, frac_command=frac_command)
        return self._wrap(tex, equation_env)

    def B_tex(self, equation_env=True, frac_command=True) -> str:
        tex = "B =" + matrix_to_tex(self.B, frac_command=frac_command)
        return self._wrap(tex, equation_env)
