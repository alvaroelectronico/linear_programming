"""Exam-generation application built on top of the :mod:`linprog` library.

Defines a small domain model (:mod:`exams.models`), a problem bank
(:mod:`exams.bank`), per-course exam definitions (:mod:`exams.exams_def`),
LaTeX assembly (:mod:`exams.render`), PDF compilation (:mod:`exams.compile`)
and a command-line interface (:mod:`exams.cli`, exposed as ``lp-exams``).
"""
