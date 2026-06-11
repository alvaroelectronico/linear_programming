"""Domain model for exam problems and exams.

A :class:`ProblemSpec` is the linear program itself (the same strings the
:mod:`linprog` parser accepts). An :class:`ExamProblem` wraps a spec with the
exam-facing narrative and rendering flags. An :class:`Exam` is an ordered set of
problems for a given course/year and variant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from linprog.problem import LinearProgram


@dataclass(frozen=True)
class ProblemSpec:
    """The linear program, expressed exactly as the linprog parser expects."""

    objective: tuple[str, str]
    constraints: list[str]
    method: str = "simplex"


@dataclass
class ExamProblem:
    """A bank problem: its statement, its LP spec and what to show in the key.

    ``statement`` is the narrative (word-problem) LaTeX shown to students. The
    ``include_*`` flags control which sections :func:`render_worked_solution`
    emits in the solution key.
    """

    id: str
    title: str
    statement: str
    spec: ProblemSpec
    points: float = 10.0
    include_formulation: bool = True
    include_phase1: bool = True
    include_tableau: bool = True
    include_basis_details: bool = False

    def build_program(self) -> "LinearProgram":
        from linprog import LinearProgram

        return LinearProgram(self.spec.constraints, self.spec.objective, self.spec.method)


@dataclass
class Exam:
    """An ordered collection of problems for a course/year and variant."""

    id: str
    title: str
    course: str
    year: int
    problems: list[ExamProblem] = field(default_factory=list)
    variant: str = "A"
