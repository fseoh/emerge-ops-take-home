"""Signup-window cutoffs for funnel rates.

Recent students have not had time to reach later stages, so counting them as
drop-offs understates those stages. For each stage we measure how long students
who reached it took (95th percentile, whole days), then only count students who
have had at least that long before the snapshot.

Needs analysis/students_clean.csv. Run in order:
  python3 analysis/clean_data.py
  python3 analysis/cohort_windows.py
Writes analysis/cohort_windows_output.txt.
"""
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
SNAPSHOT = pd.Timestamp("2026-09-15 06:00")  # ET, per DATA_DICTIONARY.md
PCT = 0.95

d = pd.read_csv(
    OUT / "students_clean.csv",
    parse_dates=["signup_at", "ev_first_video_at", "ev_course_completed_at", "permit_exam_date"],
)
lines = []


def report(msg=""):
    print(msg)
    lines.append(str(msg))


def pct(num, den):
    return f"{num / den:.1%} ({num}/{den})" if den else "n/a (0/0)"


# ---------------------------------------------------------------- time between stages
signup_to_fv = (d.ev_first_video_at - d.signup_at).dt.days
fv_to_cc = (d.ev_course_completed_at - d.ev_first_video_at).dt.days
# permit_exam_date is the most recent attempt, so for 2-attempt students this
# overstates time to first exam. That makes the window longer (conservative).
taken = d.permit_result.isin(["passed", "failed"])
cc_to_exam = (d.permit_exam_date - d.ev_course_completed_at.dt.normalize()).dt.days.where(taken)
signup_to_permit = (d.permit_exam_date - d.signup_at.dt.normalize()).dt.days.where(d.permit_passed)

report("== Days between stages (students who reached the later stage)")
rows = []
for name, s in [
    ("Signup -> First Video", signup_to_fv),
    ("First Video -> Course Complete", fv_to_cc),
    ("Course Complete -> Exam taken", cc_to_exam),
    ("Signup -> Permit passed", signup_to_permit),
]:
    s = s.dropna()
    rows.append({
        "step": name, "n": len(s),
        "median": int(s.quantile(0.5, interpolation="higher")),
        "p75": int(s.quantile(0.75, interpolation="higher")),
        "p90": int(s.quantile(0.90, interpolation="higher")),
        "p95": int(s.quantile(PCT, interpolation="higher")),
    })
timing = pd.DataFrame(rows).set_index("step")
report(timing.to_string())
report(f"negative durations: signup->FV {(signup_to_fv < 0).sum()}, FV->CC {(fv_to_cc < 0).sum()}, "
       f"CC->exam {(cc_to_exam < 0).sum()}")

# ---------------------------------------------------------------- cutoffs
def cutoff(step):
    return SNAPSHOT - pd.Timedelta(days=int(timing.loc[step, "p95"]))


cut_fv = cutoff("Signup -> First Video")
cut_cc = cutoff("First Video -> Course Complete")
cut_p = cutoff("Course Complete -> Exam taken")
cut_all = cutoff("Signup -> Permit passed")

report()
report(f"== Cutoffs (snapshot {SNAPSHOT} minus the {PCT:.0%} window)")
report(f"FV/CA:        signed up on or before        {cut_fv}")
report(f"CC/FV:        first video on or before      {cut_cc}")
report(f"Permit/CC:    course complete on or before  {cut_p}")
report(f"Permit/CA:    signed up on or before        {cut_all}")

# ---------------------------------------------------------------- rates by signup month (raw, no cutoff)
report()
report("== Stage rates by signup month, NO cutoff (shows the time-to-finish problem)")
d["signup_month"] = d.signup_at.dt.to_period("M")
m = d.groupby("signup_month").agg(
    CA=("user_id", "size"), FV=("ev_first_video", "sum"),
    CC=("ev_course_complete", "sum"), Permit=("permit_passed", "sum"),
)
m["FV/CA"] = [pct(r.FV, r.CA) for r in m.itertuples()]
m["CC/FV"] = [pct(r.CC, r.FV) for r in m.itertuples()]
m["Permit/CC"] = [pct(r.Permit, r.CC) for r in m.itertuples()]
report(m.to_string())

# ---------------------------------------------------------------- rates with per-stage cutoffs
report()
report("== Stage rates with per-stage cutoffs (all 3 cities, 3,000 real students)")
fv_pool = d.loc[d.signup_at <= cut_fv]
cc_pool = d.loc[d.ev_first_video & (d.ev_first_video_at <= cut_cc)]
p_pool = d.loc[d.ev_course_complete & (d.ev_course_completed_at <= cut_p)]
all_pool = d.loc[d.signup_at <= cut_all]
report(f"FV/CA      {pct(int(fv_pool.ev_first_video.sum()), len(fv_pool))}  "
       f"signups {fv_pool.signup_at.min():%Y-%m-%d} to {fv_pool.signup_at.max():%Y-%m-%d}; "
       f"excluded {len(d) - len(fv_pool)} newer signups")
report(f"CC/FV      {pct(int(cc_pool.ev_course_complete.sum()), len(cc_pool))}  "
       f"first videos {cc_pool.ev_first_video_at.min():%Y-%m-%d} to {cc_pool.ev_first_video_at.max():%Y-%m-%d}; "
       f"excluded {int(d.ev_first_video.sum()) - len(cc_pool)} newer first videos")
report(f"Permit/CC  {pct(int(p_pool.permit_passed.sum()), len(p_pool))}  "
       f"completions {p_pool.ev_course_completed_at.min():%Y-%m-%d} to {p_pool.ev_course_completed_at.max():%Y-%m-%d}; "
       f"excluded {int(d.ev_course_complete.sum()) - len(p_pool)} newer completions")
report(f"Permit/CA  {pct(int(all_pool.permit_passed.sum()), len(all_pool))}  "
       f"signups {all_pool.signup_at.min():%Y-%m-%d} to {all_pool.signup_at.max():%Y-%m-%d}")

# ---------------------------------------------------------------- mature cohort, whole funnel
report()
report(f"== Mature cohort: signed up on or before {cut_all:%Y-%m-%d} (every stage has had time)")
c = all_pool
ca, fv, cc, p = len(c), int(c.ev_first_video.sum()), int(c.ev_course_complete.sum()), int(c.permit_passed.sum())
report(f"CA {ca} -> FV {fv} -> CC {cc} -> Permit {p}")
report(f"FV/CA {pct(fv, ca)} | CC/FV {pct(cc, fv)} | Permit/CC {pct(p, cc)} | Permit/CA {pct(p, ca)}")
report(f"students lost at each step: CA->FV {ca - fv}, FV->CC {fv - cc}, CC->Permit {cc - p}")
report(f"still pending in this cohort: permit_scheduled {int((c.status == 'permit_scheduled').sum())}, "
       f"course_complete without exam {int((c.status == 'course_complete').sum())}, "
       f"in_progress {int((c.status == 'in_progress').sum())}")

(OUT / "cohort_windows_output.txt").write_text("\n".join(lines) + "\n")
print(f"\nwrote {OUT / 'cohort_windows_output.txt'}")
