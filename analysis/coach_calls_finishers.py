"""Coach calls among students who finished the course (reached lesson 21).

Two groups:
  1. CC/FV pool: first video on or before the cutoff used in lesson_dropoff.py
  2. All real students (no signup or first-video window)
"Finished" = highest lesson in lesson_events.csv is 21 (ev_max_lesson == 21).

Needs analysis/students_clean.csv (run analysis/clean_data.py first).
Writes analysis/coach_calls_finishers_output.txt.
"""
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
SNAPSHOT = pd.Timestamp("2026-09-15 06:00")  # ET, per DATA_DICTIONARY.md
PCT = 0.95  # same window rule as cohort_windows.py / lesson_dropoff.py

d = pd.read_csv(OUT / "students_clean.csv",
                parse_dates=["ev_first_video_at", "ev_course_completed_at"])
lines = []


def report(msg=""):
    print(msg)
    lines.append(str(msg))


def dist(group, label):
    counts = group.coach_calls_completed.value_counts().sort_index()
    report(f"== {label}")
    report(f"finishers (ev_max_lesson == 21): {len(group)}")
    report("coach_calls_completed  students  share")
    for calls, n in counts.items():
        report(f"{calls:>21}  {n:>8}  {n}/{len(group)} = {n / len(group):.1%}")
    report(f"coach_calls_completed == 0: {int((group.coach_calls_completed == 0).sum())} of {len(group)}")
    report()


gap = (d.ev_course_completed_at - d.ev_first_video_at).dt.days.dropna()
cut_cc = SNAPSHOT - pd.Timedelta(days=int(gap.quantile(PCT, interpolation="higher")))

pool = d.loc[d.ev_first_video & (d.ev_first_video_at <= cut_cc)]
report(f"Real students: {len(d)} (test accounts excluded by clean_data.py)")
report(f"CC/FV pool: first video on or before {cut_cc} -> {len(pool)} students")
report()
dist(pool.loc[pool.ev_max_lesson == 21], f"1. CC/FV pool (first video <= {cut_cc.date()})")
dist(d.loc[d.ev_max_lesson == 21], "2. All real students, no window")

(OUT / "coach_calls_finishers_output.txt").write_text("\n".join(lines) + "\n")
