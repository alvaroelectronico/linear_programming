"""Exam definitions, one module per course/year.

Each module defines a ``build(variant="A") -> Exam`` factory. Modules are
discovered automatically.
"""

from __future__ import annotations

import importlib
import pkgutil

from exams.models import Exam


def list_exams() -> list[str]:
    """Names of every exam-definition module."""
    return sorted(name for _, name, _ in pkgutil.iter_modules(__path__))


def load_exam(name: str, variant: str = "A") -> Exam:
    """Import exam module ``name`` and call its ``build(variant)`` factory."""
    try:
        module = importlib.import_module(f"{__name__}.{name}")
    except ModuleNotFoundError as exc:
        raise KeyError(
            f"Unknown exam {name!r}. Available: {', '.join(list_exams()) or '(none)'}"
        ) from exc
    return module.build(variant=variant)
