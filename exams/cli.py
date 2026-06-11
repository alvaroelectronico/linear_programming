"""Command-line interface for generating exams (entry point ``lp-exams``).

Examples::

    lp-exams list
    lp-exams problem mueblespro --solution --no-pdf
    lp-exams exam mcio1_mad1_2627 --variant A --solutions
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from exams import render
from exams.bank import list_problems, load_problem
from exams.compile import LatexNotFoundError, compile_pdf
from exams.exams_def import list_exams, load_exam

DEFAULT_OUT = Path("exams/build")


def _write_and_maybe_compile(tex: str, stem: str, out_dir: Path, make_pdf: bool) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    tex_path = out_dir / f"{stem}.tex"
    tex_path.write_text(tex, encoding="utf-8")
    print(f"Wrote {tex_path}")
    if not make_pdf:
        return 0
    try:
        pdf_path = compile_pdf(tex_path)
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
    print("Problems:")
    for name in list_problems():
        print(f"  {name}")
    print("Exams:")
    for name in list_exams():
        print(f"  {name}")
    return 0


def _cmd_problem(args: argparse.Namespace) -> int:
    problem = load_problem(args.name)
    tex = render.render_problem_document(
        problem, solution=args.solution, frac_command=args.frac
    )
    suffix = "_solution" if args.solution else ""
    return _write_and_maybe_compile(tex, f"{problem.id}{suffix}", args.out, not args.no_pdf)


def _cmd_exam(args: argparse.Namespace) -> int:
    exam = load_exam(args.name, variant=args.variant)
    tex = render.render_exam_document(exam, solutions=args.solutions, frac_command=args.frac)
    kind = "solutions" if args.solutions else "exam"
    stem = f"{exam.id}_{exam.variant}_{kind}"
    return _write_and_maybe_compile(tex, stem, args.out, not args.no_pdf)


def _add_common_output_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory")
    parser.add_argument("--no-pdf", action="store_true", help="write .tex only; skip PDF")
    parser.add_argument(
        "--frac", dest="frac", action="store_true", default=True,
        help="render \\frac{a}{b} (default)",
    )
    parser.add_argument(
        "--no-frac", dest="frac", action="store_false", help="render a/b instead of \\frac",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lp-exams", description="Generate LP exams.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list bank problems and exam definitions")
    p_list.set_defaults(func=_cmd_list)

    p_problem = sub.add_parser("problem", help="render a single bank problem")
    p_problem.add_argument("name", help="bank problem name")
    p_problem.add_argument(
        "--solution", action="store_true", help="include the worked solution"
    )
    _add_common_output_flags(p_problem)
    p_problem.set_defaults(func=_cmd_problem)

    p_exam = sub.add_parser("exam", help="render a full exam")
    p_exam.add_argument("name", help="exam definition name")
    p_exam.add_argument("--variant", default="A", help="exam variant (default A)")
    p_exam.add_argument(
        "--solutions", action="store_true", help="render the answer key instead of the blank exam"
    )
    _add_common_output_flags(p_exam)
    p_exam.set_defaults(func=_cmd_exam)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
