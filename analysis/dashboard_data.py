"""Numbers for the community-plan dashboard, by cohort month, plus a snapshot history.

Every figure on Dashboard/index.html comes from this script. Shared rules (cutoffs,
pool, target segment, stoppers, eligibility, MDE) come from definitions.py. Rerun the
whole pipeline after each new export; this script must run last, because it checks its
numbers against what the other scripts recorded in analysis/key_numbers.json and stops
without writing anything if one disagrees:

  python3 analysis/clean_data.py
  python3 analysis/cohort_windows.py
  python3 analysis/lesson_dropoff.py
  python3 analysis/pilot_sizing.py
  python3 analysis/coach_calls_finishers.py
  python3 analysis/coach_calls_engagement.py
  python3 analysis/dashboard_data.py

Reads:
  analysis/students_clean.csv     real students with event-based funnel fields
  data/students.csv               row count only (to report test rows dropped)
  data/lesson_events.csv          lesson 5 dates and daily activity (real students only)
  data/lessons.csv                lesson titles and video minutes
  data/seats_by_city.csv          funded seats per city
  analysis/key_numbers.json       numbers recorded by the other scripts, for the check

Writes:
  Dashboard/dashboard_data.json   everything the page shows
  Dashboard/snapshot_history.csv  one row per export (upserted by snapshot time)
  Dashboard/index.html            Dashboard/dashboard_template.html with the JSON inlined

Update SNAPSHOT in definitions.py when a new export arrives. Every script reads it from there.
"""
import json

import pandas as pd

from definitions import (DASH, DATA, SNAPSHOT, WINDOW, add_flags, cc_pool, check, cutoffs, eligible_now,
                         load_events, load_students, lowest_full_month, mde)

TOUCH1 = (0, 2)  # days since first video: first touch due (COMMUNITY_PLAN "within 1-2 days")
TOUCH2 = (4, 5)  # days since first video: second touch due (COMMUNITY_PLAN "about day 4-5")
QUIET = 4  # days since last lesson to flag as quiet; judgment call, ~2x the 1.95-day median lesson 1->2 gap
DAILY = 60  # days of daily history shown
DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
STUDY_WINDOW = {"morning": "6-11 AM", "afternoon": "12-4 PM", "evening": "5-9 PM", "late_night": "10-11 PM"}

d = load_students()
raw_rows = len(pd.read_csv(DATA / "students.csv", dtype=str))
ev = load_events(d)
d = add_flags(d, ev)  # segment, no_chat, reached_5, stopper, l5_in_window (definitions.py)
lessons = pd.read_csv(DATA / "lessons.csv").set_index("lesson_number")
seats = pd.read_csv(DATA / "seats_by_city.csv")
seats["city"] = seats.city.str.strip()


def rate(num, den):
    return {"num": int(num), "den": int(den), "pct": round(num / den * 100, 1) if den else None}


# ---------------------------------------------------------------- cutoffs and pool (definitions.py)
cut = cutoffs(d)
cut_fv, cut_cc, cut_p, cut_l5 = cut["fv"], cut["cc"], cut["p"], cut["l5"]

d["signup_month"] = d.signup_at.dt.to_period("M").astype(str)
d["fv_month"] = d.ev_first_video_at.dt.to_period("M").astype(str)
d["cc_month"] = d.ev_course_completed_at.dt.to_period("M").astype(str)

pool = cc_pool(d, cut)
seg = pool.loc[pool.segment]
wide = pool.loc[pool.no_chat]

# ---------------------------------------------------------------- monthly series
months = sorted(d.signup_month.unique())
fv_all = d.loc[d.ev_first_video]


def month_row(m):
    fvm = fv_all.loc[fv_all.fv_month == m]
    closed = fvm.loc[fvm.ev_first_video_at <= cut_l5]  # 21-day window has ended
    cc_ok = fvm.loc[fvm.ev_first_video_at <= cut_cc]
    su = d.loc[d.signup_month == m]
    su_ok = su.loc[su.signup_at <= cut_fv]
    ccm = d.loc[d.ev_course_complete & (d.cc_month == m)]
    ccm_ok = ccm.loc[ccm.ev_course_completed_at <= cut_p]
    s, o = closed.loc[closed.segment], closed.loc[~closed.segment]
    return {
        "month": m,
        "signups": len(su),
        "first_videos": len(fvm),
        "segment_new": int(fvm.segment.sum()),
        "l5_segment": rate(s.l5_in_window.sum(), len(s)),
        "l5_other": rate(o.l5_in_window.sum(), len(o)),
        "l5_all": rate(closed.l5_in_window.sum(), len(closed)),
        "l5_excluded": len(fvm) - len(closed),
        "chat_share": rate((fvm.joined_group_chat == "yes").sum(), len(fvm)),
        "fv_ca": rate(su_ok.ev_first_video.sum(), len(su_ok)),
        "fv_ca_excluded": len(su) - len(su_ok),
        "cc_fv": rate(cc_ok.ev_course_complete.sum(), len(cc_ok)),
        "cc_fv_excluded": len(fvm) - len(cc_ok),
        "permit_cc": rate(ccm_ok.permit_passed.sum(), len(ccm_ok)),
        "permit_cc_excluded": len(ccm) - len(ccm_ok),
    }


monthly = [month_row(m) for m in months]

# ---------------------------------------------------------------- snapshot KPIs
not_done = pool.loc[pool.ev_max_lesson < 21]
early = not_done.loc[not_done.stopper]
reached5 = pool.loc[pool.reached_5]
eligible = eligible_now(d)
seg_base = rate(seg.l5_in_window.sum(), len(seg))
wide_base = rate(wide.l5_in_window.sum(), len(wide))

# ---------------------------------------------------------------- days to lesson 5 (pool, cumulative)
# Every pool student had their first video 59+ days before the snapshot, so days 0-CURVE_DAYS are
# fully observed for all of them: no one is cut off early.
CURVE_DAYS = 28
rest = pool.loc[~pool.segment]
l5_curve = [{"day": t, "segment": rate((seg.fv_to_l5_days <= t).sum(), len(seg)),
             "other": rate((rest.fv_to_l5_days <= t).sum(), len(rest))} for t in range(CURVE_DAYS + 1)]
assert l5_curve[WINDOW]["segment"] == seg_base, "day-21 point must equal the segment baseline"
l5_ever = {"segment": rate(seg.reached_5.sum(), len(seg)), "other": rate(rest.reached_5.sum(), len(rest))}

seg_per_month = lowest_full_month(d.loc[d.segment].ev_first_video_at)
wide_per_month = lowest_full_month(d.loc[d.no_chat].ev_first_video_at)

stops = []
for n in range(1, 21):
    reached = int((pool.ev_max_lesson >= n).sum())
    stopped = int((pool.ev_max_lesson == n).sum())
    stops.append({"lesson": n, "title": lessons.loc[n, "title"],
                  "video_min": int(lessons.loc[n, "video_minutes"]),
                  "stopped": stopped, "reached": reached,
                  "stop_rate": round(stopped / reached * 100, 1)})

groups = []
for plan in ["yes", "no"]:
    for chat in ["yes", "no"]:
        g = pool.loc[(pool.has_training_plan == plan) & (pool.joined_group_chat == chat)]
        groups.append({"plan": plan, "chat": chat, "n": len(g),
                       "share": round(len(g) / len(pool) * 100, 1),
                       "reached_5": rate(g.reached_5.sum(), len(g))})

passed = d.loc[d.permit_passed].groupby("city").size()
seat_rows = [{"city": r.city, "seats": int(r.seats), "permits_passed": int(passed.get(r.city, 0))}
             for r in seats.itertuples()]

plan_yes = pool.loc[pool.has_training_plan == "yes"]
chat_gap = round(((plan_yes.loc[plan_yes.joined_group_chat == "yes"].reached_5.mean()
                   - plan_yes.loc[plan_yes.joined_group_chat == "no"].reached_5.mean()) * 100), 1)

# ---------------------------------------------------------------- daily outreach queue (eligible_now)
def next_study_day(days):
    """First date on or after the snapshot date that is one of the student's plan_study_days."""
    wanted = set(str(days).split("|"))
    for k in range(7):
        day = SNAPSHOT.normalize() + pd.Timedelta(days=k)
        if DOW[day.weekday()] in wanted:
            return day
    return None


queue = []
for r in eligible.sort_values("ev_first_video_at", ascending=False).itertuples():
    day_n = int((SNAPSHOT - r.ev_first_video_at).total_seconds() // 86400)
    quiet_days = (SNAPSHOT - r.ev_last_completed_at).total_seconds() / 86400
    if r.status == "withdrawn":
        action = "Do not contact (withdrawn)"
    elif TOUCH1[0] <= day_n <= TOUCH1[1]:
        action = "Touch 1 due"
    elif TOUCH2[0] <= day_n <= TOUCH2[1]:
        action = "Touch 2 due"
    else:
        action = "Monitor"
    nxt = next_study_day(r.plan_study_days)
    send_at_day = day_n + (nxt - SNAPSHOT.normalize()).days if nxt is not None else None
    window = TOUCH1 if action == "Touch 1 due" else TOUCH2 if action == "Touch 2 due" else None
    queue.append({
        "user_id": r.user_id, "city": r.city, "language": r.preferred_language,
        "day": day_n, "lesson": int(r.ev_max_lesson), "status": r.status,
        "days_since_lesson": round(quiet_days, 1), "quiet": bool(quiet_days >= QUIET),
        "active_3d": bool(r.engagement_3d_minutes > 0),
        "send_day": f"{nxt:%a %b} {nxt.day}" if nxt is not None else None,
        "send_today": bool(nxt is not None and nxt == SNAPSHOT.normalize()),
        "send_window": STUDY_WINDOW.get(r.plan_study_time, r.plan_study_time),
        "action": action,
        "study_day_after_window": bool(window and send_at_day is not None and send_at_day > window[1]),
    })
qdf = pd.DataFrame(queue)
contactable = qdf.loc[qdf.action != "Do not contact (withdrawn)"]
queue_summary = {
    "eligible": len(qdf),
    "withdrawn_excluded": int((qdf.action == "Do not contact (withdrawn)").sum()),
    "contactable": len(contactable),
    "touch1_due": int((contactable.action == "Touch 1 due").sum()),
    "touch2_due": int((contactable.action == "Touch 2 due").sum()),
    "monitor": int((contactable.action == "Monitor").sum()),
    "due_send_today": int(contactable.action.isin(["Touch 1 due", "Touch 2 due"])
                          .mul(contactable.send_today).sum()),
    "study_day_after_window": int(contactable.study_day_after_window.sum()),
    "quiet": int(contactable.quiet.sum()),
    "active_3d": int(contactable.active_3d.sum()),
    "by_lesson": contactable.lesson.value_counts().sort_index().to_dict(),
}

# ---------------------------------------------------------------- daily activity, last DAILY full days
day_end = SNAPSHOT.normalize()  # snapshot day itself is partial (to 06:00), so stop the day before
days = pd.date_range(day_end - pd.Timedelta(days=DAILY), day_end - pd.Timedelta(days=1), freq="D")
fv_day = d.loc[d.ev_first_video].ev_first_video_at.dt.normalize().value_counts()
seg_day = d.loc[d.segment].ev_first_video_at.dt.normalize().value_counts()
ev_day = ev.assign(day=ev.completed_at.dt.normalize())
active_day = ev_day.groupby("day").user_id.nunique()
early_day = ev_day.loc[ev_day.lesson_number <= 4].groupby("day").size()
daily = [{"date": f"{t:%Y-%m-%d}", "dow": DOW[t.weekday()],
          "first_videos": int(fv_day.get(t, 0)), "segment_entries": int(seg_day.get(t, 0)),
          "students_active": int(active_day.get(t, 0)), "lessons_1_4": int(early_day.get(t, 0))}
         for t in days]

# ---------------------------------------------------------------- students inside their 21-day window
win = d.loc[d.ev_first_video & (d.ev_first_video_at > cut_l5) & (d.status != "withdrawn")]
window_pipeline = [{"lesson": label, "segment": int(((win.segment) & sel).sum()),
                    "other": int(((~win.segment) & sel).sum())}
                   for label, sel in [("1", win.ev_max_lesson == 1), ("2", win.ev_max_lesson == 2),
                                      ("3", win.ev_max_lesson == 3), ("4", win.ev_max_lesson == 4),
                                      ("5+", win.ev_max_lesson >= 5)]]

# ---------------------------------------------------------------- variation in progress (pool)
def by_field(col, frame=pool, order=None):
    g = frame.groupby(col).reached_5.agg(["sum", "size"])
    keys = order or g.sort_values("size", ascending=False).index.tolist()
    return [{"value": k, "reached_5": rate(g.loc[k, "sum"], g.loc[k, "size"])} for k in keys if k in g.index]


variation = {
    "city": by_field("city"),
    "language": by_field("preferred_language"),
    "device": by_field("primary_device"),
    "study_time": by_field("plan_study_time", plan_yes,
                           ["morning", "afternoon", "evening", "late_night"]),
    "pool_all": rate(pool.reached_5.sum(), len(pool)),
    "plan_holders": len(plan_yes),
}

result = {
    "snapshot": f"{SNAPSHOT:%Y-%m-%d %H:%M}",
    "snapshot_dow": DOW[SNAPSHOT.weekday()],
    "rules": {"touch1": TOUCH1, "touch2": TOUCH2, "quiet_days": QUIET},
    "queue": queue,
    "queue_summary": queue_summary,
    "daily": daily,
    "window_pipeline": window_pipeline,
    "variation": variation,
    "window_days": WINDOW,
    "cutoffs": {
        "fv_ca_signup_by": f"{cut_fv:%Y-%m-%d}",
        "cc_fv_first_video_by": f"{cut_cc:%Y-%m-%d}",
        "permit_cc_complete_by": f"{cut_p:%Y-%m-%d}",
        "l5_first_video_by": f"{cut_l5:%Y-%m-%d}",
    },
    "data_handling": {
        "raw_rows": raw_rows,
        "real_students": len(d),
        "test_rows_dropped": raw_rows - len(d),
        "city_labels_normalized": int((d.city != d.city_raw).sum()),
        "lessons_mismatch": int(d.flag_lessons_mismatch.sum()),
        "by_city": d.city.value_counts().to_dict(),
    },
    "kpis": {
        "segment_l5_baseline": seg_base,
        "wide_l5_baseline": wide_base,
        "cc_fv": rate(pool.ev_course_complete.sum(), len(pool)),
        "early_share_of_nonfinishers": rate(len(early), len(not_done)),
        "reached5_finished": rate((reached5.ev_max_lesson == 21).sum(), len(reached5)),
        "segment_share_of_pool": rate(len(seg), len(pool)),
        "segment_share_of_stoppers": rate(seg.stopper.sum(), len(early)),
        "eligible_now": len(eligible),
        "chat_gap_plan_holders": chat_gap,
        "pool_n": len(pool),
    },
    "monthly": monthly,
    "l5_curve": l5_curve,
    "l5_ever": l5_ever,
    "stops": stops,
    "plan_chat": groups,
    "segment_profile": {
        "city": seg.city.value_counts().to_dict(),
        "language": seg.preferred_language.value_counts().to_dict(),
        "study_time": seg.plan_study_time.value_counts().to_dict(),
    },
    "mde": {
        "segment": {"per_month": seg_per_month, "baseline": seg_base["pct"],
                    "rows": [{"months": k, "per_arm": seg_per_month * k // 2,
                              "mde": round(mde(seg_base["num"] / seg_base["den"], seg_per_month * k // 2) * 100, 1)}
                             for k in [1, 2, 3, 4]]},
        "wide": {"per_month": wide_per_month, "baseline": wide_base["pct"],
                 "rows": [{"months": k, "per_arm": wide_per_month * k // 2,
                           "mde": round(mde(wide_base["num"] / wide_base["den"], wide_per_month * k // 2) * 100, 1)}
                          for k in [1, 2, 3, 4]]},
    },
    "seats": seat_rows,
}

# ---------------------------------------------------------------- consistency check
# Every number the dashboard shares with another script must match what that script
# recorded in key_numbers.json. Stop before writing anything if one doesn't.
K = result["kpis"]
shared = {"cohort_windows.cut_fv": cut_fv, "cohort_windows.cut_cc": cut_cc, "cohort_windows.cut_p": cut_p,
          "cohort_windows.cc_fv_num": K["cc_fv"]["num"], "cohort_windows.cc_fv_den": K["cc_fv"]["den"],
          "lesson_dropoff.pool_n": len(pool), "lesson_dropoff.non_finishers": len(not_done),
          "lesson_dropoff.stoppers": len(early), "lesson_dropoff.reached_5": len(reached5),
          "lesson_dropoff.reached_5_finished": K["reached5_finished"]["num"],
          "lesson_dropoff.chat_gap_plan_holders": chat_gap,
          "pilot_sizing.pool_n": len(pool), "pilot_sizing.segment_n": len(seg),
          "pilot_sizing.segment_l5_num": seg_base["num"], "pilot_sizing.stoppers": len(early),
          "pilot_sizing.segment_stoppers": K["segment_share_of_stoppers"]["num"],
          "pilot_sizing.eligible_now": len(eligible), "pilot_sizing.segment_per_month": seg_per_month,
          "pilot_sizing.wide_n": wide_base["den"], "pilot_sizing.wide_l5_num": wide_base["num"],
          "pilot_sizing.wide_per_month": wide_per_month, "pilot_sizing.chat_gap_plan_holders": chat_gap,
          "pilot_sizing.mde_segment_3mo": result["mde"]["segment"]["rows"][2]["mde"],
          "coach_calls_engagement.pool_n": len(pool), "coach_calls_engagement.stoppers": len(early),
          "coach_calls_finishers.pool_n": len(pool)}
problems = check("dashboard_data", **shared)
if problems:
    raise SystemExit("Dashboard not written. Numbers disagree with the analysis scripts:\n  - "
                     + "\n  - ".join(problems))
print(f"consistency check passed: {len(shared)} shared numbers match")

# ---------------------------------------------------------------- snapshot history (upsert by snapshot)
hist_path = DASH / "snapshot_history.csv"
row = pd.DataFrame([{
    "snapshot": result["snapshot"],
    "real_students": len(d),
    "cc_fv_pct": result["kpis"]["cc_fv"]["pct"],
    "cc_fv_den": result["kpis"]["cc_fv"]["den"],
    "segment_l5_21d_pct": seg_base["pct"],
    "segment_l5_21d_den": seg_base["den"],
    "early_share_of_nonfinishers_pct": result["kpis"]["early_share_of_nonfinishers"]["pct"],
    "eligible_now": len(eligible),
    "chat_gap_pts": chat_gap,
}])
if hist_path.exists():
    hist = pd.read_csv(hist_path, dtype={"snapshot": str})
    hist = pd.concat([hist.loc[hist.snapshot != result["snapshot"]], row]).sort_values("snapshot")
else:
    hist = row
hist.to_csv(hist_path, index=False)
result["history"] = hist.to_dict(orient="records")

payload = json.dumps(result, indent=1, default=int)
(DASH / "dashboard_data.json").write_text(payload + "\n")
template = (DASH / "dashboard_template.html").read_text()
(DASH / "index.html").write_text(template.replace("__DASHBOARD_DATA__", payload))
print(json.dumps(result["kpis"], indent=1, default=int))
print(f"wrote {DASH / 'index.html'}, {DASH / 'dashboard_data.json'}, {hist_path}")
