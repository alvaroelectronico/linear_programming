"""Regenerate the .tex files: ``python -m ejercicios [id ...]`` (all by default)."""

from __future__ import annotations

import sys

from . import build


def main(argv: list[str] | None = None) -> int:
    names = argv if argv is not None else sys.argv[1:]
    try:
        written = build(names or None)
    except KeyError as error:
        print(error.args[0], file=sys.stderr)
        return 1
    for path in written:
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
