"""Compile generated ``.tex`` files to PDF via latexmk.

PDF output needs a system LaTeX distribution (MiKTeX or TeX Live, which provide
``latexmk`` and ``pdflatex``); it is not a Python dependency. Availability is
checked at runtime so the rest of the tooling works without it.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class LatexNotFoundError(RuntimeError):
    """Raised when latexmk is not available on PATH."""


def latexmk_available() -> bool:
    return shutil.which("latexmk") is not None


def compile_pdf(tex_path: Path, *, keep_going: bool = False) -> Path:
    """Compile ``tex_path`` to a PDF beside it; return the PDF path.

    Args:
        keep_going: best-effort mode for large, heterogeneous documents -- do
            not halt on the first error, and force a PDF if at all possible.
            Use it for the whole-corpus collection; keep it off for exams, where
            a broken problem should stop the build.

    Raises:
        LatexNotFoundError: if latexmk is not installed.
        subprocess.CalledProcessError: if compilation fails (only when
            ``keep_going`` is False).
    """
    tex_path = Path(tex_path)
    if not latexmk_available():
        raise LatexNotFoundError(
            "latexmk was not found on PATH. Install a LaTeX distribution "
            "(MiKTeX or TeX Live, which provide latexmk and pdflatex), or pass "
            "--no-pdf to stop at the .tex file."
        )
    flags = ["-pdf", "-interaction=nonstopmode"]
    flags.append("-f" if keep_going else "-halt-on-error")
    # Run with the bare filename and cwd set to its folder so aux/pdf files land
    # beside the source and Windows drive-letter/space issues are avoided.
    subprocess.run(
        ["latexmk", *flags, tex_path.name],
        cwd=tex_path.parent,
        check=not keep_going,
    )
    pdf_path = tex_path.with_suffix(".pdf")
    if keep_going and not pdf_path.exists():
        raise subprocess.CalledProcessError(1, "latexmk")
    return pdf_path
