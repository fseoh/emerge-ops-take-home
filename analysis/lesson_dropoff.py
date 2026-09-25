"""Where students stall between First Video and Course Complete.

Pool: students whose first video is old enough to have finished the course
(the CC/FV pool from cohort_windows.py). The Jun-19 signup cohort is shown
alongside in table 1 for comparison.

Needs analysis/students_clean.csv. Run in order:
  python3 analysis/clean_data.py
  python3 analysis/cohort_windows.py   (not required, but cutoffs should match)
  python3 analysis/lesson_dropoff.py
Writes analysis/lesson_dropoff_output.txt.
"""
import math

import pandas as pd

from definitions import (DATA, OUT, SNAPSHOT, add_flags, cc_pool, chi2_p, cutoffs, load_events,
                         load_students, record)

pd.set_option("display.width", 250)
d = load_students()
ev = load_events(d)  # real students only
d = add_flags(d, ev)
lessons = pd.read_csv(DATA / "lessons.csv").set_index("lesson_number")
lines = []


def report(msg=""):
    print(msg)
    lines.append(str(msg))


# ---------------------------------------------------------------- pools (definitions.py)
cut = cutoffs(d)
cut_cc, cut_all = cut["cc"], cut["all"]

pool = cc_pool(d, cut)
cohort = d.loc[d.ev_first_video & (d.signup_at <= cut_all)]
report(f"Pool: first video on or before {cut_cc} -> {len(pool)} students")
report(f"Comparison: signed up on or before {cut_all} and watched first video -> {len(cohort)} students")
report("Includes withdrawn students (withdrawing is a drop-off). Test accounts already excluded.")

# ---------------------------------------------------------------- 1. highest lesson reached
report()
report("== 1. Highest lesson reached per lesson_events.csv (21 = finished)")
report("stop_rate = stopped at N / reached N")
rows = []
for n in range(1, 22):
    stopped = pool.loc[pool.ev_max_lesson == n]
    reached = int((pool.ev_max_lesson >= n).sum())
    rows.append({
        "lesson": n,
        "video_min": lessons.loc[n, "video_minutes"],
        "stopped": len(stopped),
        "pct_of_pool": f"{len(stopped) / len(pool):.1%}",
        "reached": reached,
        "stop_rate": f"{len(stopped) / reached:.1%}" if n < 21 else "-",
        "in_progress": int((stopped.status == "in_progress").sum()),
        "withdrawn": int((stopped.status == "withdrawn").sum()),
        "stopped_jun19_cohort": int((cohort.ev_max_lesson == n).sum()),
    })
report(pd.DataFrame(rows).set_index("lesson").to_string())

not_done = pool.loc[pool.ev_max_lesson < 21]
early = not_done.loc[not_done.stopper]
reached5 = pool.loc[pool.reached_5]
report(f"non-finishers: {len(not_done)}; stopped at lessons 1-4: {len(early)} ({len(early) / len(not_done):.1%})")
report(f"reached lesson 5: {len(reached5)}; of those finished: {int((reached5.ev_max_lesson == 21).sum())} "
       f"({(reached5.ev_max_lesson == 21).mean():.1%})")
c_not_done = cohort.loc[cohort.ev_max_lesson < 21]
report(f"Jun-19 cohort: non-finishers {len(c_not_done)}; stopped at 1-4: "
       f"{int(c_not_done.stopper.sum())}")

# ---------------------------------------------------------------- 2. days since last lesson for stallers
report()
report("== 2. Stopped at N (never completed N+1): days since last lesson completion, as of snapshot")
report("last completion uses the latest event timestamp (not last_lesson_completed_at; see DATA_NOTES flag 3)")
nd = not_done.assign(
    days_since=(SNAPSHOT - not_done.ev_last_completed_at).dt.total_seconds() / 86400,
    seen_14d=(SNAPSHOT - not_done.last_seen_at) <= pd.Timedelta(days=14),
)
t2 = nd.groupby("ev_max_lesson").agg(
    n=("user_id", "size"),
    median_days=("days_since", "median"),
    max_days=("days_since", "max"),
    min_days=("days_since", "min"),
    seen_last_14d=("seen_14d", "sum"),
).round(1)
t2.index.name = "stopped_at"
report(t2.to_string())
report(f"stopped at 1-4: most recent lesson was {early.pipe(lambda x: (SNAPSHOT - x.ev_last_completed_at).dt.total_seconds().min() / 86400):.1f} days ago; "
       f"seen in last 14 days: {int(nd.loc[nd.stopper, 'seen_14d'].sum())}")
report(f"all non-finishers seen in last 14 days: {int(nd.seen_14d.sum())}")

# ---------------------------------------------------------------- 3. gaps between consecutive lessons
report()
report("== 3. Days between consecutive lesson completions (pool)")
e = ev.loc[ev.user_id.isin(pool.user_id)].sort_values(["user_id", "lesson_number"])
e["gap_days"] = (e.completed_at - e.groupby("user_id").completed_at.shift()).dt.total_seconds() / 86400
g = e.loc[e.lesson_number > 1]
t3 = g.groupby("lesson_number").gap_days.agg(
    n="count",
    median="median",
    p75=lambda x: x.quantile(0.75),
    negative=lambda x: int((x < 0).sum()),
)
t3["median_excl_negative"] = g.loc[g.gap_days >= 0].groupby("lesson_number").gap_days.median()
t3 = t3.round(2)
t3.index = [f"{i - 1}->{i}" for i in t3.index]
report(t3.to_string())
report("negative gaps = lesson 2 timestamped before lesson 1 (DATA_NOTES flag 2)")

# ---------------------------------------------------------------- 4. coach calls among lesson 1-4 stoppers
report()
report("== 4. Stopped at lessons 1-4: had a coach call or not (call dates are not in the data)")
t4 = pd.crosstab(early.ev_max_lesson.rename("stopped_at"), early.coach_calls_completed > 0)
t4.columns = ["0 calls" if not c else ">=1 call" for c in t4.columns]
t4["pct_with_call"] = (t4[">=1 call"] / t4.sum(axis=1) * 100).round(1)
report(t4.to_string())
with_call = early.loc[early.coach_calls_completed > 0]
report(f"had >=1 call and still stopped at 1-4: {len(with_call)} of {len(early)} "
       f"({len(with_call) / len(early):.1%}); status {with_call.status.value_counts().to_dict()}")

# ---------------------------------------------------------------- 5. training plan x group chat
report()
report("== 5. Training plan x group chat: share reaching lesson 5+ (pool)")
report("joined_group_chat is yes/no only; no join date exists, so order vs. progress is unknown")
t5 = pool.groupby(["has_training_plan", "joined_group_chat"]).reached_5.agg(n="size", reached_5="sum")
t5["stopped_1_4"] = t5.n - t5.reached_5
t5["pct_of_pool"] = (t5.n / len(pool) * 100).round(1)
t5["pct_reached_5"] = (t5.reached_5 / t5.n * 100).round(1)
report(t5.to_string())
plans = pool.loc[pool.has_training_plan == "yes"].copy()
report(f"plan holders: {len(plans)}; plan created before first video: "
       f"{int((plans.plan_created_at <= plans.ev_first_video_at).sum())}; "
       f"median hours signup -> plan: "
       f"{((plans.plan_created_at - plans.signup_at).dt.total_seconds() / 3600).median():.2f}")
before_plan = ev.merge(plans[["user_id", "plan_created_at"]], on="user_id")
before_plan = before_plan.loc[before_plan.completed_at < before_plan.plan_created_at]
done_at_plan = before_plan.groupby("user_id").lesson_number.max().reindex(plans.user_id).fillna(0)
report(f"lessons already done when plan was created: {done_at_plan.value_counts().sort_index().astype(int).to_dict()}")

plan_rate = pool.groupby("has_training_plan").reached_5.agg(n="size", reached_5="sum")
plan_rate["pct_reached_5"] = (plan_rate.reached_5 / plan_rate.n * 100).round(1)
report("by plan only:")
report(plan_rate.to_string())
report(f"plan holders: {int(plan_rate.loc['yes', 'n'])} of {len(pool)} ({plan_rate.loc['yes', 'n'] / len(pool):.1%})")
r5 = t5.pct_reached_5
report(f"chat gap: no plan {r5['no', 'yes'] - r5['no', 'no']:+.1f} pts, with plan {r5['yes', 'yes'] - r5['yes', 'no']:+.1f} pts")
report(f"plan gap: no chat {r5['yes', 'no'] - r5['no', 'no']:+.1f} pts, with chat {r5['yes', 'yes'] - r5['no', 'yes']:+.1f} pts")


# ---------------------------------------------------------------- 6. fields known at signup: stoppers vs lesson 5+
report()
report("== 6. Fields known at signup: share reaching lesson 5+ by value (pool); p from chi-square, approximate")
pool["signup_month"] = pool.signup_at.dt.to_period("M").astype(str)
for col in ["joined_group_chat", "has_training_plan", "referral_source", "primary_device",
            "city", "age_band", "preferred_language", "signup_month"]:
    t = pd.crosstab(pool[col], pool.reached_5)
    rates = (t[True] / t.sum(axis=1) * 100).round(1)
    report(f"{col}: p={chi2_p(t):.2g} | " + ", ".join(f"{k} {v}% (n={t.sum(axis=1)[k]})" for k, v in rates.items()))

record("lesson_dropoff", pool_n=len(pool), non_finishers=len(not_done), stoppers=len(early),
       reached_5=len(reached5), reached_5_finished=int((reached5.ev_max_lesson == 21).sum()),
       chat_gap_plan_holders=round(float(r5["yes", "yes"] - r5["yes", "no"]), 1))

(OUT / "lesson_dropoff_output.txt").write_text("\n".join(lines) + "\n")
print(f"\nwrote {OUT / 'lesson_dropoff_output.txt'}")
