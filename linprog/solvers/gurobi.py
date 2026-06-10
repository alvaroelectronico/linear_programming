"""Optional Gurobi backend for cross-checking and sensitivity analysis.

``gurobipy`` is imported lazily so the rest of the package works without Gurobi
installed. Constructing a :class:`GurobiModel` raises a clear error if it is
missing.
"""

from __future__ import annotations

from fractions import Fraction

import numpy as np

from linprog.parsing import StandardForm


def _import_gurobi():
    try:
        import gurobipy as gp
        from gurobipy import GRB
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "Gurobi is required for this backend. Install 'gurobipy' or solve "
            "with the simplex/lemke methods instead."
        ) from exc
    return gp, GRB


class GurobiModel:
    """Build and solve the original LP with Gurobi from already-parsed data."""

    def __init__(self, num_vars, A, b, c, var_names, sense, constraint_senses):
        gp, GRB = _import_gurobi()
        self._gp = gp
        self._GRB = GRB

        self.num_vars = num_vars
        self.A = A
        # c and b may arrive as column vectors; flatten to 1-D for scalar access.
        self.b = np.asarray(b).ravel()
        self.c = np.asarray(c).ravel()
        self.var_names = var_names
        self.sense = sense
        self.constraint_senses = constraint_senses

        self.model = gp.Model()
        self.vars = self.model.addVars(range(num_vars), name="x", lb=0.0)

        objective = gp.LinExpr()
        for j in range(num_vars):
            if self.c[j] != 0:
                objective += float(self.c[j]) * self.vars[j]
        direction = GRB.MAXIMIZE if sense.lower().startswith("max") else GRB.MINIMIZE
        self.model.setObjective(objective, direction)

        self.constrs = []
        for i in range(len(self.b)):
            lhs = gp.LinExpr()
            for j in range(num_vars):
                if A[i][j] != 0:
                    lhs += float(A[i][j]) * self.vars[j]
            rhs = float(self.b[i])
            if constraint_senses[i] == "<=":
                self.constrs.append(self.model.addConstr(lhs <= rhs))
            elif constraint_senses[i] == ">=":
                self.constrs.append(self.model.addConstr(lhs >= rhs))
            else:
                self.constrs.append(self.model.addConstr(lhs == rhs))

    @classmethod
    def from_standard_form(cls, sf: StandardForm) -> "GurobiModel":
        """Construct from a :class:`~linprog.parsing.StandardForm`."""
        return cls(
            num_vars=sf.num_vars,
            A=sf.A,
            b=sf.b,
            c=sf.c2,
            var_names=sf.var_names[: sf.num_vars],
            sense=sf.objective_sense,
            constraint_senses=sf.constraint_senses,
        )

    def solve(self, print_details=True, print_model=True, as_fractions=True) -> bool:
        """Optimize the model; return True iff an optimal solution was found."""
        try:
            if print_model:
                self.print_model()
            self.model.optimize()
            if self.model.status == self._GRB.OPTIMAL:
                if print_details:
                    self.print_solution_details(as_fractions=as_fractions)
                return True
            return False
        except self._gp.GurobiError as exc:
            print(f"Gurobi error: {exc}")
            return False

    # --- result accessors -------------------------------------------------

    def get_solution(self) -> dict[int, float]:
        return {i: self.vars[i - 1].x for i in range(1, self.num_vars + 1)}

    def get_objective_value(self) -> float:
        return self.model.objVal

    def get_reduced_costs(self) -> dict[int, float]:
        return {i: self.vars[i - 1].RC for i in range(1, self.num_vars + 1)}

    def get_dual_values(self) -> list[float]:
        return [constr.pi for constr in self.constrs]

    def get_obj_coefficients_sensitivity(self) -> dict[str, dict]:
        sensitivity = {}
        for i in range(1, self.num_vars + 1):
            var = self.vars[i - 1]
            sensitivity[f"x_{i}"] = {
                "current_value": var.obj,
                "lower_bound": var.SAObjLow,
                "upper_bound": var.SAObjUp,
            }
        return sensitivity

    def get_rhs_sensitivity(self) -> dict[str, dict]:
        sensitivity = {}
        for i, constr in enumerate(self.constrs):
            sensitivity[f"constraint_{i + 1}"] = {
                "current_value": constr.RHS,
                "lower_bound": constr.SARHSLow,
                "upper_bound": constr.SARHSUp,
                "dual_value": constr.pi,
                "slack": constr.slack,
            }
        return sensitivity

    # --- reporting --------------------------------------------------------

    @staticmethod
    def _to_fraction_str(value, tolerance=1e-10) -> str:
        """Format a float as a fraction string, handling infinities and edge cases."""
        try:
            if abs(value) < tolerance:
                return "0"
            if value >= 1e30:
                return "∞"
            if value <= -1e30:
                return "-∞"
            if abs(value) > 1e6:
                return f"{value:.2f}"
            return str(Fraction(value).limit_denominator())
        except (OverflowError, ValueError):
            return f"{value:.4f}"

    def _format(self, value, as_fractions) -> str:
        return self._to_fraction_str(value) if as_fractions else f"{value:.4f}"

    def print_solution_details(self, as_fractions=True) -> None:
        print("\nOptimal solution found:")
        print(f"Objective value: {self._format(self.get_objective_value(), as_fractions)}")

        print("\nVariable values:")
        for i, val in self.get_solution().items():
            print(f"x_{i} = {self._format(val, as_fractions)}")

        print("\nShadow prices (dual values):")
        for i, dual in enumerate(self.get_dual_values(), 1):
            print(f"Constraint {i}: {self._format(dual, as_fractions)}")

        print("\nReduced costs:")
        for var, rc in self.get_reduced_costs().items():
            print(f"x_{var}: {self._format(rc, as_fractions)}")

        print("\nObjective-coefficient sensitivity:")
        for var, data in self.get_obj_coefficients_sensitivity().items():
            print(f"\n{var}:")
            print(f"  Current coefficient: {self._format(data['current_value'], as_fractions)}")
            print(
                f"  Range: [{self._format(data['lower_bound'], as_fractions)}, "
                f"{self._format(data['upper_bound'], as_fractions)}]"
            )

        print("\nRight-hand-side (RHS) sensitivity:")
        for name, data in self.get_rhs_sensitivity().items():
            print(f"\n{name}:")
            print(f"  Current RHS: {self._format(data['current_value'], as_fractions)}")
            print(f"  Shadow price: {self._format(data['dual_value'], as_fractions)}")
            print(f"  Slack: {self._format(data['slack'], as_fractions)}")
            print(
                f"  RHS range: [{self._format(data['lower_bound'], as_fractions)}, "
                f"{self._format(data['upper_bound'], as_fractions)}]"
            )

    def print_model(self) -> None:
        print("\nModel:")
        print("Minimize:" if "min" in self.sense.lower() else "Maximize:")
        print(f"  {self._linear_expr_str(self.c)}")

        print("\nSubject to:")
        for i in range(len(self.b)):
            sense_str = {"=": " = ", "<=": " <= ", ">=": " >= "}[self.constraint_senses[i]]
            row_str = self._linear_expr_str([self.A[i][j] for j in range(self.num_vars)])
            print(f"  {i + 1}. {row_str}{sense_str}{float(self.b[i])}")

        print("\nVariables:")
        print(f"  {', '.join(self.var_names)} >= 0")

    def _linear_expr_str(self, coeffs) -> str:
        """Render a coefficient row as ``2x_1 - x_2`` style text."""
        parts = ""
        for j in range(self.num_vars):
            coeff = coeffs[j]
            if coeff == 0:
                continue
            if parts and coeff > 0:
                parts += " + "
            elif coeff < 0:
                parts += " - "
            magnitude = abs(float(coeff))
            parts += self.var_names[j] if magnitude == 1 else f"{magnitude}{self.var_names[j]}"
        return parts
