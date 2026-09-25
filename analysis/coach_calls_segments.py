"""Coach calls within the chat-pilot target segment.

How many target-segment students (first video, training plan, not in the chat;
first-video pool, n = 600) never had a coach call? Sizes the overlap between the
chat pilot and any later coach-call test (DATA_NOTES.md, open question 3).

Needs analysis/students_clean.csv (run analysis/clean_data.py first).
Writes analysis/coach_calls_segments_output.txt.
"""
import pandas as pd

from definitions import OUT, add_flags, cc_pool, cutoffs, load_events, load_students, record

d = load_students()
d = add_flags(d, load_events(d))
cut = cutoffs(d)
pool = cc_pool(d, cut)
seg = pool.loc[pool.segment]
lines = []


def report(msg=""):
    print(msg)
    lines.append(str(msg))


def frac(n, total):
    return f"{n}/{total} = {n / total:.1%}" if total else "-"


zero = seg.coach_calls_completed == 0
report(f"Target segment in the CC/FV pool (first video on or before {cut['cc']:%Y-%m-%d}): {len(seg)} students")
report(f"0 coach calls:  {frac(int(zero.sum()), len(seg))}")
report(f">=1 coach call: {frac(int((~zero).sum()), len(seg))}")
report(f"0-call segment students who stopped at lessons 1-4: {int((zero & seg.stopper).sum())} of {int(zero.sum())}")
report()
report("0-call share by highest lesson reached (segment, lessons 1-4 only)")
t = pd.crosstab(seg.loc[seg.stopper].ev_max_lesson.rename("stopped_at"),
                seg.loc[seg.stopper].coach_calls_completed.eq(0).map({True: "0 calls", False: ">=1 call"}))
t["pct_0_calls"] = (t["0 calls"] / t.sum(axis=1) * 100).round(1)
report(t.to_string())

record("coach_calls_segments", segment_n=len(seg), segment_zero_calls=int(zero.sum()))

(OUT / "coach_calls_segments_output.txt").write_text("\n".join(lines) + "\n")
print(f"\nwrote {OUT / 'coach_calls_segments_output.txt'}")
