"""Coach calls among students who finished the course (reached lesson 21).

Two groups:
  1. CC/FV pool: first video on or before the cutoff used in lesson_dropoff.py
  2. All real students (no signup or first-video window)
"Finished" = highest lesson in lesson_events.csv is 21 (ev_max_lesson == 21).

Needs analysis/students_clean.csv (run analysis/clean_data.py first).
Writes analysis/coach_calls_finishers_output.txt.
"""
from definitions import OUT, cc_pool, cutoffs, load_students, record

d = load_students()
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


cut = cutoffs(d)  # definitions.py
cut_cc = cut["cc"]

pool = cc_pool(d, cut)
report(f"Real students: {len(d)} (test accounts excluded by clean_data.py)")
report(f"CC/FV pool: first video on or before {cut_cc} -> {len(pool)} students")
report()
dist(pool.loc[pool.ev_max_lesson == 21], f"1. CC/FV pool (first video <= {cut_cc.date()})")
dist(d.loc[d.ev_max_lesson == 21], "2. All real students, no window")

record("coach_calls_finishers", pool_n=len(pool))

(OUT / "coach_calls_finishers_output.txt").write_text("\n".join(lines) + "\n")
