"""Problem bank.

Each module in this package defines a single ``build() -> ExamProblem`` factory.
Modules are discovered automatically, so dropping in a new ``<topic>.py`` makes
it available to the CLI with no registration step.
"""

from __future__ import annotations

import importlib
import pkgutil

from exams.models import ExamProblem


def list_problems() -> list[str]:
    """Names of every bank module (the part after ``exams.bank.``)."""
    return sorted(name for _, name, _ in pkgutil.iter_modules(__path__))


def load_problem(name: str) -> ExamProblem:
    """Import bank module ``name`` and call its ``build()`` factory."""
    try:
        module = importlib.import_module(f"{__name__}.{name}")
    except ModuleNotFoundError as exc:
        raise KeyError(
            f"Unknown problem {name!r}. Available: {', '.join(list_problems()) or '(none)'}"
        ) from exc
    return module.build()
