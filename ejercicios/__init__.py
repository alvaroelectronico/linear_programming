"""Exercise authoring layer: one Python module per exercise -> .tex files.

An exercise is any ``ejercicios/<id>.py`` (no leading underscore) defining:

    def statement() -> str    # required -> tex/<id>.tex
    def solution() -> str     # optional -> tex/<id>_sol.tex

Both return LaTeX fragments (Spanish exam material) built by interleaving
plain text with `linprog` calls — see ``_plantilla.py`` for a walkthrough.
``python -m ejercicios [id ...]`` regenerates the .tex files that a
hand-maintained ``main.tex`` includes with ``\\input``.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from types import ModuleType

PACKAGE_DIR = Path(__file__).parent
DEFAULT_OUT_DIR = PACKAGE_DIR.parent / "tex"


def join_blocks(*blocks: str | None) -> str:
    """Join LaTeX blocks with blank lines, skipping empty ones."""
    return "\n\n".join(block.strip("\n") for block in blocks if block)


def discover() -> dict[str, ModuleType]:
    """Import every exercise module in this package, keyed by its id.
    Files starting with ``_`` (like the template) are skipped."""
    modules: dict[str, ModuleType] = {}
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        if path.stem.startswith("_"):
            continue
        module = importlib.import_module(f"{__name__}.{path.stem}")
        if callable(getattr(module, "statement", None)):
            modules[path.stem] = module
    return modules


def build(
    names: list[str] | None = None,
    out_dir: Path | str = DEFAULT_OUT_DIR,
) -> list[Path]:
    """Write ``<id>.tex`` (and ``<id>_sol.tex`` when the module defines
    ``solution``) for the given exercise ids — all of them by default.
    Returns the written paths."""
    modules = discover()
    if names is None:
        selected = modules
    else:
        missing = [name for name in names if name not in modules]
        if missing:
            raise KeyError(
                f"Unknown exercise(s): {', '.join(missing)}. "
                f"Available: {', '.join(modules) or '(none)'}"
            )
        selected = {name: modules[name] for name in names}

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, module in selected.items():
        statement_path = out_dir / f"{name}.tex"
        statement_path.write_text(module.statement().rstrip() + "\n", encoding="utf-8")
        written.append(statement_path)
        solution = getattr(module, "solution", None)
        if callable(solution):
            solution_path = out_dir / f"{name}_sol.tex"
            solution_path.write_text(solution().rstrip() + "\n", encoding="utf-8")
            written.append(solution_path)
    return written
