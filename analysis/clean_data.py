"""Data checks and cleaning for the Emerge ops take-home.

Reads only from data/ (never modifies it). Writes:
  analysis/students_clean.csv      real students only, city normalized,
                                   event-derived funnel columns, flag_* columns
  analysis/data_checks_output.txt  every count cited in analysis/DATA_NOTES.md

Run from anywhere:  python3 analysis/clean_data.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "analysis"
SNAPSHOT = pd.Timestamp("2026-09-15 06:00")  # ET, per DATA_DICTIONARY.md

# Every raw city label must map here after strip + lowercase. Unknown labels stop the script.
CITY_MAP = {
    "nyc": "NYC",
    "new york": "NYC",
    "new york city": "NYC",
    "sacramento": "Sacramento",
    "sac": "Sacramento",
    "boston": "Boston",
    "bos": "Boston",
}
VALID_ID = re.compile(r"^u_\d{6}$")
DATE_COLS = [
    "signup_at", "first_video_at", "last_lesson_completed_at", "course_completed_at",
    "last_seen_at", "last_logged_in_at", "plan_created_at", "plan_target_permit_date",
    "permit_exam_date",
]
INT_COLS = [
    "lessons_completed", "engagement_7d_minutes", "engagement_3d_minutes",
    "study_hall_sessions_attended", "coach_calls_completed", "permit_attempts",
]

lines = []


def report(msg=""):
    print(msg)
    lines.append(str(msg))


def section(title):
    report()
    report(f"== {title}")


# ---------------------------------------------------------------- load raw
raw = pd.read_csv(DATA / "students.csv", dtype=str, keep_default_na=False)
ev_raw = pd.read_csv(DATA / "lesson_events.csv", dtype=str, keep_default_na=False)
lessons = pd.read_csv(DATA / "lessons.csv")
seats = pd.read_csv(DATA / "seats_by_city.csv", dtype=str, keep_default_na=False)

section("Row counts (raw)")
report(f"students.csv: {len(raw)} rows, {raw.shape[1]} columns")
report(f"lesson_events.csv: {len(ev_raw)} rows, {ev_raw.user_id.nunique()} distinct users")
report(f"lessons.csv: {len(lessons)} rows")
report(f"seats_by_city.csv: {len(seats)} rows")

# ---------------------------------------------------------------- whitespace, every column
section("Leading/trailing whitespace (all string columns, all files)")
for name, df in [("students", raw), ("lesson_events", ev_raw), ("seats_by_city", seats)]:
    for col in df.columns:
        lead = (df[col] != df[col].str.lstrip()).sum()
        trail = (df[col] != df[col].str.rstrip()).sum()
        if lead or trail:
            report(f"{name}.{col}: leading={lead} trailing={trail} "
                   f"values={sorted(df.loc[df[col] != df[col].str.strip(), col].map(repr).unique())}")
report("(columns not listed have none)")

# ---------------------------------------------------------------- duplicates
section("Duplicates")
report(f"students duplicate user_id: {raw.user_id.duplicated().sum()}")
report(f"students fully duplicated rows: {raw.duplicated().sum()}")
report(f"lesson_events fully duplicated rows: {ev_raw.duplicated().sum()}")
report(f"lesson_events duplicate (user_id, lesson_number): "
       f"{ev_raw.duplicated(['user_id', 'lesson_number']).sum()}")

# ---------------------------------------------------------------- test accounts
section("Test / internal accounts")
bad_id = ~raw.user_id.str.match(VALID_ID)
internal = raw.referral_source.str.strip() == "internal"
report(f"user_id not matching u_######: {bad_id.sum()} -> {sorted(raw.loc[bad_id, 'user_id'])}")
report(f"referral_source = internal: {internal.sum()}")
report(f"same rows? {bool((bad_id == internal).all())}")
is_test = bad_id | internal
test_ids = set(raw.loc[is_test, "user_id"])
report(f"dropping {is_test.sum()} test rows (union of both rules)")
report(f"lesson_events rows belonging to test accounts: {ev_raw.user_id.isin(test_ids).sum()}")
tests = raw.loc[is_test, ["user_id", "city", "status", "lessons_completed"]]
report(tests.sort_values("user_id").to_string(index=False))

st = raw.loc[~is_test].copy()
report(f"real students after drop: {len(st)}")

# ---------------------------------------------------------------- city labels
section("City labels (real students)")
report("raw labels (repr shows hidden spaces):")
report(st.city.map(repr).value_counts().to_string())
key = st.city.str.strip().str.lower()
unknown = sorted(set(key) - set(CITY_MAP))
if unknown:
    sys.exit(f"Unmapped city labels {unknown}: add them to CITY_MAP after checking them.")
st["city_raw"] = st.city
st["city"] = key.map(CITY_MAP)
changed = st.city != st.city_raw
report(f"rows whose label changed: {changed.sum()}")
report(st.loc[changed].groupby(["city_raw", "city"]).size().rename("rows")
       .reset_index().assign(city_raw=lambda d: d.city_raw.map(repr)).to_string(index=False))
report("normalized counts:")
report(st.city.value_counts().to_string())
seat_cities = set(seats.city.str.strip())
report(f"cities missing from seats_by_city.csv: {sorted(set(st.city) - seat_cities) or 'none'}")

# ---------------------------------------------------------------- types and ranges
section("Types and ranges (real students)")
for c in DATE_COLS:
    parsed = pd.to_datetime(st[c].replace("", None), errors="coerce")
    unparseable = ((st[c] != "") & parsed.isna()).sum()
    report(f"{c}: blank={(st[c] == '').sum()} unparseable={unparseable} "
           f"after_snapshot={(parsed > SNAPSHOT).sum()}")
    st[c] = parsed
for c in INT_COLS:
    num = pd.to_numeric(st[c], errors="coerce")
    report(f"{c}: non_numeric={num.isna().sum()} min={num.min()} max={num.max()}")
    st[c] = num.astype("Int64")
st["plan_hours_per_week"] = pd.to_numeric(st.plan_hours_per_week.replace("", None))
report(f"referral_source values: {sorted(st.referral_source.unique())}")

# ---------------------------------------------------------------- event log
section("lesson_events.csv integrity")
ev = ev_raw.loc[~ev_raw.user_id.isin(test_ids)].copy()
ev["lesson_number"] = pd.to_numeric(ev.lesson_number)
ev["minutes_watched"] = pd.to_numeric(ev.minutes_watched)
ev["quiz_score_pct"] = pd.to_numeric(ev.quiz_score_pct)
ev["completed_at"] = pd.to_datetime(ev.completed_at)
report(f"lesson_number outside 1-21: {(~ev.lesson_number.between(1, 21)).sum()}")
report(f"completed_at after snapshot: {(ev.completed_at > SNAPSHOT).sum()}")
report(f"user_ids not in students.csv: {(~ev.user_id.isin(raw.user_id)).sum()}")
report(f"minutes_watched range: {ev.minutes_watched.min()}-{ev.minutes_watched.max()}; "
       f"quiz_score_pct range: {ev.quiz_score_pct.min()}-{ev.quiz_score_pct.max()}")
signup = ev.user_id.map(st.set_index("user_id").signup_at)
last_seen = ev.user_id.map(st.set_index("user_id").last_seen_at)
report(f"events before signup: {(ev.completed_at < signup).sum()}; "
       f"events after last_seen_at: {(ev.completed_at > last_seen).sum()}")

per_user = ev.groupby("user_id").agg(
    ev_max_lesson=("lesson_number", "max"),
    ev_lesson_count=("lesson_number", "nunique"),
    ev_last_completed_at=("completed_at", "max"),
)
report(f"users with gaps (max lesson != lessons done): "
       f"{(per_user.ev_max_lesson != per_user.ev_lesson_count).sum()}")

ordered = ev.sort_values(["user_id", "lesson_number"])
prev_time = ordered.groupby("user_id").completed_at.shift()
out_of_order = ordered.loc[ordered.completed_at < prev_time]
report(f"events finished before the previous lesson: {len(out_of_order)} rows, "
       f"{out_of_order.user_id.nunique()} users, lesson numbers "
       f"{out_of_order.lesson_number.value_counts().to_dict()}")

# ---------------------------------------------------------------- event-derived funnel
l1 = ev.loc[ev.lesson_number == 1].set_index("user_id").completed_at
l21 = ev.loc[ev.lesson_number == 21].set_index("user_id").completed_at
st = st.join(per_user, on="user_id")
st["ev_max_lesson"] = st.ev_max_lesson.fillna(0).astype(int)
st["ev_lesson_count"] = st.ev_lesson_count.fillna(0).astype(int)
st["ev_first_video_at"] = st.user_id.map(l1)
st["ev_course_completed_at"] = st.user_id.map(l21)
st["ev_first_video"] = st.ev_first_video_at.notna()
st["ev_course_complete"] = st.ev_course_completed_at.notna()
st["permit_passed"] = st.permit_result == "passed"

section("Summary fields vs event log (real students)")
diff = st.lessons_completed - st.ev_max_lesson
st["flag_lessons_mismatch"] = diff != 0
report(f"lessons_completed != max event lesson: {st.flag_lessons_mismatch.sum()}")
report(f"  summary higher: {(diff > 0).sum()}  summary lower: {(diff < 0).sum()}")
report(f"  difference distribution: { {int(k): int(v) for k, v in diff[diff != 0].value_counts().sort_index().items()} }")
report(f"  by status: {st.loc[st.flag_lessons_mismatch, 'status'].value_counts().to_dict()}")
report(f"  summary > 0 but no events at all: "
       f"{((st.lessons_completed > 0) & (st.ev_max_lesson == 0)).sum()}")
mm = st.loc[st.flag_lessons_mismatch, ["user_id", "status", "lessons_completed", "ev_max_lesson"]]
report(mm.sort_values("user_id").to_string(index=False))

report(f"first_video_at blank vs lesson-1 event disagree: "
       f"{(st.first_video_at.notna() != st.ev_first_video).sum()}")
report(f"first_video_at != lesson-1 event time: "
       f"{(st.first_video_at.notna() & st.ev_first_video & (st.first_video_at != st.ev_first_video_at)).sum()}")
report(f"course_completed_at blank vs lesson-21 event disagree: "
       f"{(st.course_completed_at.notna() != st.ev_course_complete).sum()}")
report(f"permit passed without lesson-21 event: {(st.permit_passed & ~st.ev_course_complete).sum()}")

st["flag_lesson2_before_lesson1"] = st.user_id.isin(
    out_of_order.loc[out_of_order.lesson_number == 2, "user_id"])
st["flag_last_lesson_before_first_video"] = st.last_lesson_completed_at < st.first_video_at
report(f"last_lesson_completed_at earlier than first_video_at: "
       f"{st.flag_last_lesson_before_first_video.sum()} "
       f"(all within lesson-2-before-lesson-1 group: "
       f"{bool(st.loc[st.flag_last_lesson_before_first_video, 'flag_lesson2_before_lesson1'].all())})")
report(f"last_lesson_completed_at != latest event time: "
       f"{(st.ev_last_completed_at.notna() & (st.last_lesson_completed_at != st.ev_last_completed_at)).sum()}")

# ---------------------------------------------------------------- engagement
section("Engagement fields (real students)")
st["flag_eng3d_gt_7d"] = st.engagement_3d_minutes > st.engagement_7d_minutes
report(f"engagement_3d_minutes > engagement_7d_minutes: {st.flag_eng3d_gt_7d.sum()}")
report(st.loc[st.flag_eng3d_gt_7d, ["user_id", "signup_at", "engagement_7d_minutes",
                                    "engagement_3d_minutes"]].to_string(index=False))

report("Window test (dictionary does not say how the windows are counted):")
report(f"  snapshot is a {SNAPSHOT.day_name()}")
recent = ev.loc[ev.completed_at >= SNAPSHOT - pd.Timedelta(hours=72)]
weekend_only = recent.groupby("user_id").completed_at.apply(lambda t: (t.dt.dayofweek >= 5).all())
wk = st.loc[st.user_id.isin(weekend_only[weekend_only].index)]
report(f"  lessons in last 72h only on Sat/Sun: {len(wk)} students; "
       f"3d minutes = 0 for {(wk.engagement_3d_minutes == 0).sum()}")
r72 = st.loc[st.user_id.isin(recent.user_id)]
report(f"  any lesson in last 72h: {len(r72)} students; 3d minutes = 0 for "
       f"{(r72.engagement_3d_minutes == 0).sum()}")
r7 = st.loc[st.user_id.isin(ev.loc[ev.completed_at >= SNAPSHOT - pd.Timedelta(days=7), 'user_id'])]
report(f"  any lesson in last 7d: {len(r7)} students; 7d minutes = 0 for "
       f"{(r7.engagement_7d_minutes == 0).sum()}")
old7 = st.loc[st.last_seen_at < SNAPSHOT - pd.Timedelta(days=7)]
report(f"  last seen > 7d before snapshot: {len(old7)}; 7d minutes > 0 for "
       f"{(old7.engagement_7d_minutes > 0).sum()}")
old72 = st.loc[st.last_seen_at < SNAPSHOT - pd.Timedelta(hours=72)]
odd = old72.loc[old72.engagement_3d_minutes > 0]
report(f"  last seen > 72h before snapshot: {len(old72)}; 3d minutes > 0 for {len(odd)} "
       f"(all in the 3d > 7d group: {bool(odd.flag_eng3d_gt_7d.all())})")

# ---------------------------------------------------------------- status checks
section("Status vs other fields (real students)")
since_seen = SNAPSHOT - st.last_seen_at
report(f"in_progress but not seen for 14+ days: "
       f"{((st.status == 'in_progress') & (since_seen > pd.Timedelta(days=14))).sum()}")
report(f"inactive but seen within 14 days: "
       f"{((st.status == 'inactive') & (since_seen <= pd.Timedelta(days=14))).sum()}")
band = pd.cut(st.ev_max_lesson, [-1, 0, 20, 21], labels=["0", "1-20", "21"])
report("status x lessons done per event log:")
report(pd.crosstab(st.status, band).to_string())
report(f"last_logged_in_at after last_seen_at: {(st.last_logged_in_at > st.last_seen_at).sum()}")
report(f"has_training_plan=no with plan fields filled: "
       f"{((st.has_training_plan == 'no') & st.plan_created_at.notna()).sum()}")
report(f"has_training_plan=yes with no target permit date: "
       f"{((st.has_training_plan == 'yes') & st.plan_target_permit_date.isna()).sum()}")
report(f"study_hall > 0 without group chat: "
       f"{((st.study_hall_sessions_attended > 0) & (st.joined_group_chat == 'no')).sum()}")
report("permit_attempts x permit_result:")
report(pd.crosstab(st.permit_attempts, st.permit_result.replace("", "(blank)")).to_string())

# ---------------------------------------------------------------- coach calls
section("Coach calls vs lesson progress (real students)")
report("coach_calls_completed is a count only; no file records when calls happened")
call_band = pd.cut(st.ev_max_lesson, [-1, 0, 1, 2, 3, 4, 20, 21],
                   labels=["0", "1", "2", "3", "4", "5-20", "21"])
report(pd.crosstab(call_band.rename("highest_lesson"), st.coach_calls_completed, margins=True).to_string())
report(f"0 lessons with a call: {((st.ev_max_lesson == 0) & (st.coach_calls_completed > 0)).sum()}")
report(f"0 calls who reached lesson 5+: {((st.coach_calls_completed == 0) & (st.ev_max_lesson >= 5)).sum()} "
       f"of {(st.coach_calls_completed == 0).sum()} with 0 calls")
report(f"3 calls with highest lesson <= 4: {((st.coach_calls_completed == 3) & (st.ev_max_lesson <= 4)).sum()}")

# ---------------------------------------------------------------- signup window
section("Signups by month (real students)")
report(st.signup_at.dt.to_period("M").value_counts().sort_index().to_string())
report(f"signup range: {st.signup_at.min()} to {st.signup_at.max()}")

# ---------------------------------------------------------------- write outputs
cols = list(raw.columns) + ["city_raw"] + [c for c in st.columns if c.startswith(("ev_", "permit_passed", "flag_"))]
st[cols].to_csv(OUT / "students_clean.csv", index=False)
(OUT / "data_checks_output.txt").write_text("\n".join(lines) + "\n")
print(f"\nwrote {OUT / 'students_clean.csv'} ({len(st)} rows) and {OUT / 'data_checks_output.txt'}")
