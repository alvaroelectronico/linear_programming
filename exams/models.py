"""Domain model for generated problems and exam definitions.

Two ideas:

* An :class:`ExamProblem` is a *generated* linear-programming problem: its
  narrative, its LP spec and what to show in the answer key. Rendering it writes
  two LaTeX *fragments* into the ``ejercicios/`` folder -- ``<id>.tex`` (the
  statement) and ``<id>_sol.tex`` (the worked solution) -- in the same style as
  the hand-written problems already there.
* An :class:`Exam` is an ordered list of *fragment names* (generated ids or the
  base name of a hand-written ``.tex``) plus a course/variant. The exam master
  document ``\\input``s those fragments.
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
    """A generated problem: narrative, LP spec and answer-key options.

    ``statement`` is the narrative (word-problem) LaTeX. When
    ``include_formulation`` is set, the parsed formulation is appended to the
    statement. ``questions`` becomes an ``enumerate`` of tasks. The ``include_*``
    flags below control which sections the worked solution renders.
    """

    id: str
    title: str
    statement: str
    spec: ProblemSpec
    questions: list[str] = field(default_factory=list)
    points: float = 10.0
    include_formulation: bool = True
    statement_label: str | None = None
    include_phase1: bool = True
    include_tableau: bool = True
    include_basis_details: bool = False

    def build_program(self) -> "LinearProgram":
        from linprog import LinearProgram

        return LinearProgram(self.spec.constraints, self.spec.objective, self.spec.method)


@dataclass
class Exam:
    """An ordered set of fragment names assembled into one exam.

    ``items`` are fragment base names: a generated problem's ``id`` or the base
    name of a hand-written ``ejercicios/<name>.tex``.
    """

    id: str
    title: str
    course: str
    year: int
    items: list[str] = field(default_factory=list)
    variant: str = "A"
