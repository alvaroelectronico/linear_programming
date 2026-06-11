"""Command-line interface for generating problems and exams (``lp-exams``).

Workflow:

    lp-exams list                          # bank problems + exam definitions
    lp-exams render demo_muebles           # write ejercicios/demo_muebles{,_sol}.tex
    lp-exams collection --pdf              # build exams/coleccion.tex (+ PDF)
    lp-exams exam mcio1_mad1_2627 --pdf    # build exams/examen.tex (+ PDF)

Fragments live in ``exams/ejercicios/``; the collection and exam master
documents live in ``exams/`` and ``\\input`` those fragments, so PDFs are
compiled with the working directory set to ``exams/``.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from exams import render
from exams.bank import list_problems, load_problem
from exams.compile import LatexNotFoundError, compile_pdf
from exams.exams_def import list_exams, load_exam

APP_DIR = Path(__file__).parent
DEFAULT_EJERCICIOS = APP_DIR / "ejercicios"


def _compile(tex_path: Path, *, keep_going: bool = False) -> int:
    try:
        pdf_path = compile_pdf(tex_path, keep_going=keep_going)
    except LatexNotFoundError as exc:
        print(f"PDF not generated: {exc}", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as exc:
        print(
            f"PDF not generated: latexmk failed (exit {exc.returncode}). "
            f"See the .log next to {tex_path}.",
            file=sys.stderr,
        )
        return 2
    print(f"Wrote {pdf_path}")
    return 0


def _cmd_list(_: argparse.Namespace) -> int:
    print("Generated problems (bank):")
    for name in list_problems():
        print(f"  {name}")
    print("Exam definitions:")
    for name in list_exams():
        print(f"  {name}")
    unpaired = render.unpaired_statements(DEFAULT_EJERCICIOS)
    if unpaired:
        print("\nStatements with no matching _sol.tex (excluded from the collection):")
        for name in unpaired:
            print(f"  {name}")
    return 0


def _cmd_render(args: argparse.Namespace) -> int:
    problem = load_problem(args.name)
    statement, solution = render.write_problem_fragments(
        problem, args.ejercicios, frac_command=args.frac
    )
    print(f"Wrote {statement}")
    print(f"Wrote {solution}")
    return 0


def _cmd_collection(args: argparse.Namespace) -> int:
    out_dir = args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    # \input paths are relative to the master's directory (LaTeX uses /).
    prefix = os.path.relpath(args.ejercicios, out_dir).replace(os.sep, "/")
    tex = render.build_collection(args.ejercicios, ejercicios_prefix=prefix)
    out_path = out_dir / "coleccion.tex"
    out_path.write_text(tex, encoding="utf-8")
    print(f"Wrote {out_path}")
    # The whole-corpus collection is heterogeneous: compile best-effort unless
    # the user asks for a strict build.
    return _compile(out_path, keep_going=not args.strict) if args.pdf else 0


def _cmd_exam(args: argparse.Namespace) -> int:
    exam = load_exam(args.name, variant=args.variant)
    tex = render.build_exam(exam, solutions=args.solutions)
    kind = "soluciones" if args.solutions else "examen"
    out_path = args.out / f"{exam.id}_{exam.variant}_{kind}.tex"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(tex, encoding="utf-8")
    print(f"Wrote {out_path}")
    return _compile(out_path) if args.pdf else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lp-exams", description="Generate LP problems and exams.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list bank problems and exam definitions")
    p_list.set_defaults(func=_cmd_list)

    p_render = sub.add_parser("render", help="write a problem's statement + solution fragments")
    p_render.add_argument("name", help="bank problem name")
    p_render.add_argument("--ejercicios", type=Path, default=DEFAULT_EJERCICIOS)
    p_render.add_argument("--frac", dest="frac", action="store_true", default=True)
    p_render.add_argument("--no-frac", dest="frac", action="store_false")
    p_render.set_defaults(func=_cmd_render)

    p_coll = sub.add_parser("collection", help="build the collection master document")
    p_coll.add_argument(
        "--out", type=Path, default=APP_DIR / "coleccion", help="dir for coleccion.tex + PDF"
    )
    p_coll.add_argument("--ejercicios", type=Path, default=DEFAULT_EJERCICIOS)
    p_coll.add_argument("--pdf", action="store_true", help="compile the PDF with latexmk")
    p_coll.add_argument(
        "--strict", action="store_true", help="halt on the first LaTeX error (default: best-effort)"
    )
    p_coll.set_defaults(func=_cmd_collection)

    p_exam = sub.add_parser("exam", help="build an exam master document")
    p_exam.add_argument("name", help="exam definition name")
    p_exam.add_argument("--variant", default="A", help="exam variant (default A)")
    p_exam.add_argument("--solutions", action="store_true", help="append the answer key")
    p_exam.add_argument("--out", type=Path, default=APP_DIR, help="where to write the .tex")
    p_exam.add_argument("--pdf", action="store_true", help="compile the PDF with latexmk")
    p_exam.set_defaults(func=_cmd_exam)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
