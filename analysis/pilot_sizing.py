"""Numbers for the community plan: target segment, pilot metric window, and pilot sizing.

Needs analysis/students_clean.csv. Run in order:
  python3 analysis/clean_data.py
  python3 analysis/cohort_windows.py
  python3 analysis/lesson_dropoff.py
  python3 analysis/pilot_sizing.py
Writes analysis/pilot_sizing_output.txt.
"""
import math
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
DATA = OUT.parent / "data"
SNAPSHOT = pd.Timestamp("2026-09-15 06:00")  # ET, per DATA_DICTIONARY.md
PCT = 0.95  # same window rule as cohort_windows.py
Z_ALPHA = 1.959964  # two-sided alpha = 0.05
Z_POWER = 0.841621  # power = 0.80

pd.set_option("display.width", 250)
d = pd.read_csv(OUT / "students_clean.csv",
                parse_dates=["signup_at", "ev_first_video_at", "ev_course_completed_at", "plan_created_at"])
ev = pd.read_csv(DATA / "lesson_events.csv", parse_dates=["completed_at"])
ev = ev.loc[ev.user_id.isin(d.user_id)]
seats = pd.read_csv(DATA / "seats_by_city.csv")
lines = []


def report(msg=""):
    print(msg)
    lines.append(str(msg))


# ---------------------------------------------------------------- pool (same rule as cohort_windows.py)
fv_to_cc = (d.ev_course_completed_at - d.ev_first_video_at).dt.days.dropna()
cut_cc = SNAPSHOT - pd.Timedelta(days=int(fv_to_cc.quantile(PCT, interpolation="higher")))
d["l5_at"] = d.user_id.map(ev.loc[ev.lesson_number == 5].set_index("user_id").completed_at)
d["fv_to_l5_days"] = (d.l5_at - d.ev_first_video_at).dt.total_seconds() / 86400
d["segment"] = d.ev_first_video & (d.has_training_plan == "yes") & (d.joined_group_chat == "no")
pool = d.loc[d.ev_first_video & (d.ev_first_video_at <= cut_cc)]
report(f"Pool: first video on or before {cut_cc} -> {len(pool)} students")

# ---------------------------------------------------------------- 1. metric window
report()
report("== 1. Days from first video to lesson 5 (pool students who reached lesson 5)")
r = pool.fv_to_l5_days.dropna()
report(f"n={len(r)} " + " ".join(f"p{int(q * 100)}={r.quantile(q):.1f}" for q in [0.5, 0.75, 0.9, 0.95, 0.99])
       + f" max={r.max():.1f}")
for w in [7, 14, 21, 28]:
    report(f"reached lesson 5 within {w} days of first video: {(r <= w).mean():.1%} of those who ever did")
WINDOW = 21
report(f"chosen window: {WINDOW} days")

# ---------------------------------------------------------------- 2. segment
report()
report("== 2. Target segment: first video, training plan = yes, group chat = no")
seg = pool.loc[pool.segment]
stoppers = pool.loc[pool.ev_max_lesson <= 4]
seg_stop = seg.loc[seg.ev_max_lesson <= 4]
report(f"segment in pool: {len(seg)} of {len(pool)} ({len(seg) / len(pool):.1%})")
report(f"segment stoppers (lessons 1-4): {len(seg_stop)} of {len(stoppers)} pool stoppers "
       f"({len(seg_stop) / len(stoppers):.1%})")
base_n = int((seg.fv_to_l5_days <= WINDOW).sum())
baseline = base_n / len(seg)
report(f"segment baseline, reached lesson 5 within {WINDOW} days: {baseline:.1%} ({base_n}/{len(seg)})")
report(f"segment reached lesson 5 ever: {(seg.ev_max_lesson >= 5).mean():.1%} "
       f"({int((seg.ev_max_lesson >= 5).sum())}/{len(seg)})")
report(f"segment city: {seg.city.value_counts().to_dict()}")
report(f"segment preferred_language: {seg.preferred_language.value_counts().to_dict()}")
report(f"segment plan_study_time: {seg.plan_study_time.value_counts().to_dict()}")

plans = pool.loc[pool.has_training_plan == "yes"]
early = ev.merge(plans[["user_id", "plan_created_at"]], on="user_id")
early = early.loc[early.completed_at < early.plan_created_at]
done_at_plan = early.groupby("user_id").lesson_number.max().reindex(plans.user_id).fillna(0)
report(f"plans made before completing lesson 2: {int((done_at_plan < 2).sum())} of {len(plans)} "
       f"({(done_at_plan < 2).mean():.1%})")

# ---------------------------------------------------------------- 3. monthly volume
report()
report("== 3. New segment students per month (by first-video month, all real students)")
seg_all = d.loc[d.segment]
monthly = seg_all.ev_first_video_at.dt.to_period("M").value_counts().sort_index()
report(monthly.to_string())
full = monthly.loc[monthly.index < SNAPSHOT.to_period("M")]
report(f"full months Mar-Aug: min {full.min()}, median {full.median():.0f}, max {full.max()}")
per_month = int(full.min())  # conservative
report(f"sizing uses {per_month}/month (lowest full month)")

eligible_now = d.loc[d.segment & (d.ev_max_lesson <= 4)
                     & (d.ev_first_video_at > SNAPSHOT - pd.Timedelta(days=WINDOW))]
report(f"eligible at snapshot (segment, lessons 1-4, first video in last {WINDOW} days): {len(eligible_now)}")

# ---------------------------------------------------------------- 4. pilot sizing
report()
report(f"== 4. Minimum detectable effect, intent-to-treat, 50/50 split, alpha 0.05 two-sided, power 0.80")
report(f"baseline (control) rate: {baseline:.1%}")


def mde(p0, n_arm):
    lo, hi = 0.0, 1 - p0
    for _ in range(60):
        delta = (lo + hi) / 2
        p1 = p0 + delta
        need = (Z_ALPHA * math.sqrt(2 * ((p0 + p1) / 2) * (1 - (p0 + p1) / 2) / n_arm)
                + Z_POWER * math.sqrt((p0 * (1 - p0) + p1 * (1 - p1)) / n_arm))
        lo, hi = (delta, hi) if need > delta else (lo, delta)
    return hi


for months in [1, 2, 3, 4]:
    n_arm = per_month * months // 2
    report(f"{months} month(s) of enrollment: {n_arm} per arm -> MDE {mde(baseline, n_arm) * 100:.1f} pts "
           f"(result readable {WINDOW} days after last enrollment)")

report()
report("Alternative population: first video + group chat = no (any plan status)")
wide = pool.loc[pool.ev_first_video & (pool.joined_group_chat == "no")]
wide_base = (wide.fv_to_l5_days <= WINDOW).mean()
wide_monthly = d.loc[d.ev_first_video & (d.joined_group_chat == "no")].ev_first_video_at.dt.to_period("M") \
    .value_counts().sort_index()
wide_per_month = int(wide_monthly.loc[wide_monthly.index < SNAPSHOT.to_period("M")].min())
report(f"in pool: {len(wide)}; baseline within {WINDOW} days: {wide_base:.1%} "
       f"({int((wide.fv_to_l5_days <= WINDOW).sum())}/{len(wide)}); lowest full month: {wide_per_month}")
for months in [1, 2, 3, 4]:
    n_arm = wide_per_month * months // 2
    report(f"{months} month(s): {n_arm} per arm -> MDE {mde(wide_base, n_arm) * 100:.1f} pts")

plan_holders = pool.loc[pool.has_training_plan == "yes"]
reach = plan_holders.groupby("joined_group_chat").apply(lambda g: (g.ev_max_lesson >= 5).mean(),
                                                        include_groups=False)
gap = reach["yes"] - reach["no"]
report()
report("Hypothetical ITT effect = share of treated who join because of outreach x effect of joining.")
report(f"Observed chat gap among plan holders ({reach['yes']:.1%} vs {reach['no']:.1%} = {gap * 100:.1f} pts) "
       f"is an upper bound; it includes self-selection.")
for uptake in [0.10, 0.20, 0.30, 0.50]:
    for share_of_gap in [1.0, 0.5]:
        report(f"  uptake {uptake:.0%}, effect = {share_of_gap:.0%} of observed gap -> ITT "
               f"{uptake * gap * share_of_gap * 100:.1f} pts")

# ---------------------------------------------------------------- 5. seats context
report()
report("== 5. Permits passed to date vs funded seats (period for seats is not stated in the data)")
passed = d.loc[d.permit_passed].groupby("city").size()
report(seats.assign(permits_passed=seats.city.map(passed)).to_string(index=False))

(OUT / "pilot_sizing_output.txt").write_text("\n".join(lines) + "\n")
print(f"\nwrote {OUT / 'pilot_sizing_output.txt'}")
