"""Plain-text parsing: turn a problem written as text into a Problem.

Accepted format (whitespace is entirely optional)::

    max 3x1 + 4x2
    x1+2x2<=50
    x1+x2>=10

- First non-empty line: ``max``/``min`` (an optional ``z =`` prefix before the
  expression is allowed), followed by a linear expression.
- Remaining non-empty lines: one constraint each, with ``<=``, ``>=`` or ``=``.
- Any letter (or word) is a variable, with an optional numeric subscript:
  ``x1`` and ``x_1`` are the same variable (canonical name ``x_1``).
- Coefficients may be implicit (``x`` is 1, ``-y`` is -1) and may be integers,
  decimals or fractions: ``2.5x``, ``3/2y``.
- Variables and constants may appear on either side of a constraint.
"""

from __future__ import annotations

import re
from fractions import Fraction

from .problem import Constraint, Problem, Sense


class ParseError(ValueError):
    """Raised when the problem text cannot be parsed."""


# One term: optional sign, optional coefficient (int, decimal or a/b fraction),
# optional variable name with an optional numeric subscript.  At least one of
# coefficient/variable must be present (checked in code).
_TERM = re.compile(
    r"(?P<sign>[+-])?"
    r"(?P<coef>\d+(?:\.\d+)?(?:/\d+)?)?"
    r"(?P<var>[A-Za-z]+(?:_?\d+)?)?"
)

_OBJECTIVE = re.compile(
    r"^(?P<goal>max|min)(?:imizar|imize|\.|:)?\s*(?P<expr>.*)$", re.IGNORECASE
)

# Optional "z =" style prefix in the objective expression (e.g. "max z = 3x").
_OBJ_PREFIX = re.compile(r"^[A-Za-z]\w*'?=")


def canonical_var(name: str) -> str:
    """Normalise a variable name: a trailing numeric subscript always gets an
    underscore, so ``x1`` and ``x_1`` both become ``x_1``."""
    match = re.fullmatch(r"([A-Za-z]+)_?(\d+)", name)
    if match:
        return f"{match.group(1)}_{match.group(2)}"
    return name


def _parse_expression(text: str, *, context: str) -> tuple[dict[str, Fraction], Fraction]:
    """Parse a linear expression into (coefficients by variable, constant term)."""
    compact = re.sub(r"\s+", "", text)
    if not compact:
        raise ParseError(f"Empty expression in: {context!r}")

    coeffs: dict[str, Fraction] = {}
    constant = Fraction(0)
    pos = 0
    first = True
    while pos < len(compact):
        match = _TERM.match(compact, pos)
        if not match or match.end() == pos or (match["coef"] is None and match["var"] is None):
            raise ParseError(f"Cannot parse {compact[pos:]!r} in: {context!r}")
        if not first and match["sign"] is None:
            raise ParseError(f"Missing sign before {compact[pos:]!r} in: {context!r}")
        sign = -1 if match["sign"] == "-" else 1
        coef = sign * (Fraction(match["coef"]) if match["coef"] else Fraction(1))
        if match["var"] is None:
            constant += coef
        else:
            name = canonical_var(match["var"])
            coeffs[name] = coeffs.get(name, Fraction(0)) + coef
        pos = match.end()
        first = False
    return coeffs, constant


def _parse_constraint(line: str) -> Constraint:
    for sense in ("<=", ">=", "="):
        if sense in line:
            left, _, right = line.partition(sense)
            break
    else:
        raise ParseError(f"Constraint without <=, >= or =: {line!r}")

    left_coeffs, left_const = _parse_expression(left, context=line)
    right_coeffs, right_const = _parse_expression(right, context=line)
    # Move variables to the left and constants to the right.
    coeffs = dict(left_coeffs)
    for name, value in right_coeffs.items():
        coeffs[name] = coeffs.get(name, Fraction(0)) - value
    rhs = right_const - left_const
    if not coeffs:
        raise ParseError(f"Constraint has no variables: {line!r}")
    return Constraint(coeffs=coeffs, sense=sense, rhs=rhs)  # type: ignore[arg-type]


def parse_problem(text: str) -> Problem:
    """Parse a full problem: objective on the first non-empty line, then one
    constraint per line."""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    if not lines:
        raise ParseError("Empty problem text")

    match = _OBJECTIVE.match(lines[0])
    if not match:
        raise ParseError(f"Objective must start with max/min: {lines[0]!r}")
    goal = match["goal"].lower()
    expr = re.sub(r"\s+", "", match["expr"])
    expr = _OBJ_PREFIX.sub("", expr)  # drop an optional "z =" prefix
    objective, constant = _parse_expression(expr, context=lines[0])
    if constant != 0:
        raise ParseError(f"Constant term not allowed in the objective: {lines[0]!r}")
    if not objective:
        raise ParseError(f"Objective has no variables: {lines[0]!r}")

    constraints = tuple(_parse_constraint(line) for line in lines[1:])
    if not constraints:
        raise ParseError("The problem has no constraints")
    return Problem(goal=goal, objective=objective, constraints=constraints)  # type: ignore[arg-type]
