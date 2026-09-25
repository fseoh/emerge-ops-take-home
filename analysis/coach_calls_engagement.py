"""Do 0-call students look less engaged overall than 1+-call students?

Every 0-call student stopped at lesson 4 or earlier, so comparing them with all
1+-call students mostly compares progress. The main comparison is therefore
among students who stopped at lessons 1-4, and again within each stopping lesson.

Signals used are ones recorded before or at the start of the drop-off zone:
plan, plan pace/hours, signup -> first video gap, lesson 1 watch time and quiz,
lesson 1 -> 2 gap, chat, study hall, device.

Pool: first video on or before the cutoff used in lesson_dropoff.py (n = 1,447).
Needs analysis/students_clean.csv (run analysis/clean_data.py first).
Writes analysis/coach_calls_engagement_output.txt.
"""
import math
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
DATA = OUT.parent / "data"
SNAPSHOT = pd.Timestamp("2026-09-15 06:00")  # ET, per DATA_DICTIONARY.md
PCT = 0.95  # same window rule as cohort_windows.py / lesson_dropoff.py

pd.set_option("display.width", 250)
d = pd.read_csv(OUT / "students_clean.csv",
                parse_dates=["signup_at", "ev_first_video_at", "ev_course_completed_at"])
ev = pd.read_csv(DATA / "lesson_events.csv", parse_dates=["completed_at"])
lessons = pd.read_csv(DATA / "lessons.csv").set_index("lesson_number")
lines = []


def report(msg=""):
    print(msg)
    lines.append(str(msg))


def frac(n, total):
    return f"{n}/{total} = {n / total:.1%}" if total else "-"


def two_prop_p(x1, n1, x2, n2):
    """Two-sided z-test p-value for a difference in proportions (normal approximation)."""
    p = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    return math.erfc(abs(x1 / n1 - x2 / n2) / se / math.sqrt(2)) if se else float("nan")


gap = (d.ev_course_completed_at - d.ev_first_video_at).dt.days.dropna()
cut_cc = SNAPSHOT - pd.Timedelta(days=int(gap.quantile(PCT, interpolation="higher")))
pool = d.loc[d.ev_first_video & (d.ev_first_video_at <= cut_cc)].copy()
pool["calls"] = pool.coach_calls_completed.gt(0).map({False: "0", True: "1+"})

# per-student early signals from the event log
ev = ev.loc[ev.user_id.isin(pool.user_id)]
l1 = ev.loc[ev.lesson_number == 1].drop_duplicates("user_id").set_index("user_id")
l2 = ev.loc[ev.lesson_number == 2].drop_duplicates("user_id").set_index("user_id")
pool = pool.set_index("user_id")
pool["signup_to_fv_days"] = (pool.ev_first_video_at - pool.signup_at).dt.total_seconds() / 86400
pool["l1_watch_ratio"] = l1.minutes_watched / lessons.loc[1, "video_minutes"]
pool["l1_quiz"] = l1.quiz_score_pct
pool["l1_to_l2_days"] = (l2.completed_at - l1.completed_at).dt.total_seconds() / 86400
pool["plan_yes"] = pool.has_training_plan == "yes"
pool["chat_yes"] = pool.joined_group_chat == "yes"
pool["any_study_hall"] = pool.study_hall_sessions_attended > 0
pool["shared_computer"] = pool.primary_device == "shared_computer"
pool["withdrawn"] = pool.status == "withdrawn"

BINARY = ["plan_yes", "chat_yes", "any_study_hall", "shared_computer", "withdrawn"]
NUMERIC = ["signup_to_fv_days", "plan_hours_per_week", "plan_lessons_per_week",
           "l1_watch_ratio", "l1_quiz", "l1_to_l2_days"]


def compare(g, title):
    z, o = g.loc[g.calls == "0"], g.loc[g.calls == "1+"]
    report(f"== {title}")
    report(f"0 calls: {len(z)}; 1+ calls: {len(o)}")
    rows = []
    for c in BINARY:
        x1, x2 = int(z[c].sum()), int(o[c].sum())
        rows.append({"signal": c, "0 calls": frac(x1, len(z)), "1+ calls": frac(x2, len(o)),
                     "p (2-prop z)": f"{two_prop_p(x1, len(z), x2, len(o)):.3g}"})
    for c in NUMERIC:
        a, b = z[c].dropna(), o[c].dropna()
        rows.append({"signal": f"{c} (median)",
                     "0 calls": f"{a.median():.2f} (n={len(a)})",
                     "1+ calls": f"{b.median():.2f} (n={len(b)})", "p (2-prop z)": ""})
    report(pd.DataFrame(rows).to_string(index=False))
    report()


report(f"Pool: first video on or before {cut_cc} -> {len(pool)} students")
report("plan_* medians use plan holders only; l1_to_l2_days uses students who reached lesson 2")
report()
compare(pool, "A. Whole pool (confounded: 0-call students all stopped at lessons 1-4)")
stop = pool.loc[pool.ev_max_lesson.between(1, 4)]
compare(stop, "B. Students who stopped at lessons 1-4 (main comparison)")

report("== C. Within each stopping lesson: plan, chat, signup->first video, lesson 1 quiz")
rows = []
for n in range(1, 5):
    g = stop.loc[stop.ev_max_lesson == n]
    z, o = g.loc[g.calls == "0"], g.loc[g.calls == "1+"]
    rows.append({"stopped_at": n, "n_0": len(z), "n_1+": len(o),
                 "plan_0": f"{z.plan_yes.mean():.1%}", "plan_1+": f"{o.plan_yes.mean():.1%}",
                 "chat_0": f"{z.chat_yes.mean():.1%}", "chat_1+": f"{o.chat_yes.mean():.1%}",
                 "su_fv_med_0": f"{z.signup_to_fv_days.median():.2f}",
                 "su_fv_med_1+": f"{o.signup_to_fv_days.median():.2f}",
                 "quiz_med_0": f"{z.l1_quiz.median():.0f}", "quiz_med_1+": f"{o.l1_quiz.median():.0f}"})
report(pd.DataFrame(rows).to_string(index=False))
report()

report("== D. Share with 0 calls by stopping lesson (students who stopped at 1-4)")
for n in range(1, 5):
    g = stop.loc[stop.ev_max_lesson == n]
    report(f"lesson {n}: {frac(int((g.calls == '0').sum()), len(g))}")

(OUT / "coach_calls_engagement_output.txt").write_text("\n".join(lines) + "\n")
