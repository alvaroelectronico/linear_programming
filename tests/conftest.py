from fractions import Fraction

import pytest

from linprog import parse_problem

F = Fraction


def normalize(tex: str) -> str:
    """Whitespace/cosmetic-insensitive comparison key for LaTeX fragments:
    drops '$', spaces and blank lines so only structure and numbers matter."""
    lines = []
    for line in tex.splitlines():
        line = line.replace("$", "").replace(" ", "").replace("\t", "")
        if line:
            lines.append(line)
    return "\n".join(lines)


@pytest.fixture
def dos_fases_a():
    # examples/dos_fases_a_sol.tex
    return parse_problem(
        """
        max x_1 + 4x_2
        4x_1 + 2x_2 = 80
        2x_1 + 3x_2 <= 60
        """
    )


@pytest.fixture
def no_factible_a():
    # examples/dos_fases_no_factible_a_sol.tex
    return parse_problem(
        """
        max 3x_1 + 2x_2 + x_3
        2x_1 + 4x_2 + 2x_3 >= 80
        4x_1 + 3x_2 = 60
        x_1 + x_2 + x_3 <= 15
        """
    )


@pytest.fixture
def no_acotado_a():
    # examples/dos_fases_no_acotado_a_sol.tex
    return parse_problem(
        """
        max 3x_1 + 2x_2 + 4x_3
        2x_1 + 4x_2 - 2x_3 >= 20
        x_1 + x_2 - x_3 <= 80
        """
    )


@pytest.fixture
def cargoplan():
    # examples/cargoplan_a_sol.tex (optimal basis (h_1, h_3, x_2), z = 60000)
    return parse_problem(
        """
        max 50x_1 + 40x_2 + 60x_3
        6x_1 + 4x_2 + 8x_3 <= 8000
        3x_1 + 2x_2 + 5x_3 <= 3000
        x_2 + x_3 >= 500
        """
    )


@pytest.fixture
def lemke_min():
    # examples/lemke_sol.tex, after splitting the equality by hand (part 1)
    return parse_problem(
        """
        min 10x_1 + 20x_2 + 30x_3
        4x_1 + 2x_2 + 8x_3 <= 1000
        x_2 + x_3 <= 500
        x_2 + x_3 >= 500
        """
    )
