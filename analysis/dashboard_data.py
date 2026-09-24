"""Numbers for the community-plan dashboard, by cohort month, plus a snapshot history.

Every figure on Dashboard/index.html comes from this script. Rerun after each new
export to refresh the dashboard and add a row to the history:

  python3 analysis/clean_data.py
  python3 analysis/dashboard_data.py

Writes:
  Dashboard/dashboard_data.json   everything the page shows
  Dashboard/snapshot_history.csv  one row per export (upserted by snapshot time)
  Dashboard/index.html            Dashboard/dashboard_template.html with the JSON inlined

Update SNAPSHOT when a new export arrives (same constant as the other scripts).
"""
import json
import math
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
DATA = ROOT / "data"
DASH = ROOT / "Dashboard"
SNAPSHOT = pd.Timestamp("2026-09-15 06:00")  # ET, per DATA_DICTIONARY.md
PCT = 0.95  # same window rule as cohort_windows.py
WINDOW = 21  # days from first video to lesson 5, same as pilot_sizing.py
Z_ALPHA = 1.959964
Z_POWER = 0.841621

d = pd.read_csv(OUT / "students_clean.csv",
                parse_dates=["signup_at", "ev_first_video_at", "ev_course_completed_at",
                             "permit_exam_date", "last_seen_at"])
raw_rows = len(pd.read_csv(DATA / "students.csv", dtype=str))
ev = pd.read_csv(DATA / "lesson_events.csv", parse_dates=["completed_at"])
ev = ev.loc[ev.user_id.isin(d.user_id)]
lessons = pd.read_csv(DATA / "lessons.csv").set_index("lesson_number")
seats = pd.read_csv(DATA / "seats_by_city.csv")
seats["city"] = seats.city.str.strip()


def p95_days(s):
    return int(s.dropna().quantile(PCT, interpolation="higher"))


def rate(num, den):
    return {"num": int(num), "den": int(den), "pct": round(num / den * 100, 1) if den else None}


def mde(p0, n_arm):
    lo, hi = 0.0, 1 - p0
    for _ in range(60):
        delta = (lo + hi) / 2
        p1 = p0 + delta
        need = (Z_ALPHA * math.sqrt(2 * ((p0 + p1) / 2) * (1 - (p0 + p1) / 2) / n_arm)
                + Z_POWER * math.sqrt((p0 * (1 - p0) + p1 * (1 - p1)) / n_arm))
        lo, hi = (delta, hi) if need > delta else (lo, delta)
    return round(hi * 100, 1)


# ---------------------------------------------------------------- cutoffs (same rules as cohort_windows.py)
taken = d.permit_result.isin(["passed", "failed"])
cut_fv = SNAPSHOT - pd.Timedelta(days=p95_days((d.ev_first_video_at - d.signup_at).dt.days))
cut_cc = SNAPSHOT - pd.Timedelta(days=p95_days((d.ev_course_completed_at - d.ev_first_video_at).dt.days))
cut_p = SNAPSHOT - pd.Timedelta(days=p95_days(
    (d.permit_exam_date - d.ev_course_completed_at.dt.normalize()).dt.days.where(taken)))
cut_l5 = SNAPSHOT - pd.Timedelta(days=WINDOW)

d["l5_at"] = d.user_id.map(ev.loc[ev.lesson_number == 5].set_index("user_id").completed_at)
d["l5_in_window"] = (d.l5_at - d.ev_first_video_at).dt.total_seconds() / 86400 <= WINDOW
d["segment"] = d.ev_first_video & (d.has_training_plan == "yes") & (d.joined_group_chat == "no")
d["no_chat"] = d.ev_first_video & (d.joined_group_chat == "no")
d["signup_month"] = d.signup_at.dt.to_period("M").astype(str)
d["fv_month"] = d.ev_first_video_at.dt.to_period("M").astype(str)
d["cc_month"] = d.ev_course_completed_at.dt.to_period("M").astype(str)

pool = d.loc[d.ev_first_video & (d.ev_first_video_at <= cut_cc)].copy()
pool["reached_5"] = pool.ev_max_lesson >= 5
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
early = not_done.loc[not_done.ev_max_lesson <= 4]
reached5 = pool.loc[pool.reached_5]
eligible_now = d.loc[d.segment & (d.ev_max_lesson <= 4) & (d.ev_first_video_at > cut_l5)]
seg_base = rate(seg.l5_in_window.sum(), len(seg))
wide_base = rate(wide.l5_in_window.sum(), len(wide))

seg_month_counts = d.loc[d.segment].fv_month.value_counts()
full_months = [m for m in months if m < str(SNAPSHOT.to_period("M"))]
seg_per_month = int(seg_month_counts.reindex(full_months).min())
wide_per_month = int(d.loc[d.no_chat].fv_month.value_counts().reindex(full_months).min())

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

result = {
    "snapshot": f"{SNAPSHOT:%Y-%m-%d %H:%M}",
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
        "segment_share_of_stoppers": rate((seg.ev_max_lesson <= 4).sum(), len(early)),
        "eligible_now": len(eligible_now),
        "eligible_now_by_city": eligible_now.city.value_counts().to_dict(),
        "eligible_now_by_language": eligible_now.preferred_language.value_counts().to_dict(),
        "chat_gap_plan_holders": chat_gap,
        "pool_n": len(pool),
    },
    "monthly": monthly,
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
                              "mde": mde(seg_base["pct"] / 100, seg_per_month * k // 2)} for k in [1, 2, 3, 4]]},
        "wide": {"per_month": wide_per_month, "baseline": wide_base["pct"],
                 "rows": [{"months": k, "per_arm": wide_per_month * k // 2,
                           "mde": mde(wide_base["pct"] / 100, wide_per_month * k // 2)} for k in [1, 2, 3, 4]]},
    },
    "seats": seat_rows,
}

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
    "eligible_now": len(eligible_now),
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
