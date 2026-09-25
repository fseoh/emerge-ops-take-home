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
import pandas as pd

from definitions import OUT, PCT, SNAPSHOT, chi2_p, cutoffs, load_students, p95_days, record, stage_days

d = load_students()
lines = []


def report(msg=""):
    print(msg)
    lines.append(str(msg))


def pct(num, den):
    return f"{num / den:.1%} ({num}/{den})" if den else "n/a (0/0)"


# ---------------------------------------------------------------- time between stages
stages = stage_days(d)  # definitions.py
signup_to_fv = stages["Signup -> First Video"]
fv_to_cc = stages["First Video -> Course Complete"]
cc_to_exam = stages["Course Complete -> Exam taken"]

report("== Days between stages (students who reached the later stage)")
rows = []
for name, s in stages.items():
    s = s.dropna()
    rows.append({
        "step": name, "n": len(s),
        "median": int(s.quantile(0.5, interpolation="higher")),
        "p75": int(s.quantile(0.75, interpolation="higher")),
        "p90": int(s.quantile(0.90, interpolation="higher")),
        "p95": p95_days(s),  # the same number cutoffs() uses
    })
timing = pd.DataFrame(rows).set_index("step")
report(timing.to_string())
report(f"negative durations: signup->FV {(signup_to_fv < 0).sum()}, FV->CC {(fv_to_cc < 0).sum()}, "
       f"CC->exam {(cc_to_exam < 0).sum()}")

# ---------------------------------------------------------------- cutoffs (definitions.py)
cut = cutoffs(d)
cut_fv, cut_cc, cut_p, cut_all = cut["fv"], cut["cc"], cut["p"], cut["all"]

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

# ---------------------------------------------------------------- permit by city
report()
report("== Permit / Course Complete by city (does city matter after the course?)")
report("p from chi-square, approximate. Passed vs not passed (failed, scheduled, or no exam on record).")
for label, g in [(f"course complete on or before {cut_p:%Y-%m-%d} (Permit/CC cutoff)", p_pool),
                 (f"mature cohort: signed up on or before {cut_all:%Y-%m-%d}, course complete",
                  c.loc[c.ev_course_complete])]:
    t = pd.crosstab(g.city, g.permit_passed)
    report(f"{label}: p={chi2_p(t):.2g} | "
           + ", ".join(f"{city} {pct(int(t.loc[city, True]), int(t.loc[city].sum()))}" for city in t.index))

record("cohort_windows", cut_fv=cut_fv, cut_cc=cut_cc, cut_p=cut_p, cut_all=cut_all,
       cc_fv_num=int(cc_pool.ev_course_complete.sum()), cc_fv_den=len(cc_pool))

(OUT / "cohort_windows_output.txt").write_text("\n".join(lines) + "\n")
print(f"\nwrote {OUT / 'cohort_windows_output.txt'}")
