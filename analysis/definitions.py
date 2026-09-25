"""Shared definitions for every analysis script and the dashboard.

Each rule below exists only here. Scripts import it instead of retyping it, so
the plan, the output files and the dashboard all count students the same way.
Change a rule here, then rerun every script (order in README / script docstrings).

Also holds the consistency check: each script records its headline numbers in
analysis/key_numbers.json, and dashboard_data.py stops if its own numbers differ.
"""
import json
import math
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent
DATA = ROOT / "data"
DASH = ROOT / "Dashboard"
KEY_NUMBERS = OUT / "key_numbers.json"

SNAPSHOT = pd.Timestamp("2026-09-15 06:00")  # ET, per DATA_DICTIONARY.md
PCT = 0.95  # time-to-stage percentile used for every signup-window cutoff
WINDOW = 21  # days from first video to lesson 5: the pilot metric
EARLY_MAX = 4  # "stopper" = highest lesson 1-4 (the drop-off zone)
Z_ALPHA = 1.959964  # two-sided alpha = 0.05
Z_POWER = 0.841621  # power = 0.80

DATE_COLS = ["signup_at", "ev_first_video_at", "ev_course_completed_at", "ev_last_completed_at",
             "permit_exam_date", "last_seen_at", "plan_created_at"]


# ---------------------------------------------------------------- loading
def load_students():
    """Real students from clean_data.py: test rows dropped, cities normalized, ev_* funnel fields."""
    return pd.read_csv(OUT / "students_clean.csv", parse_dates=DATE_COLS)


def load_events(d):
    """lesson_events.csv limited to the real students in d."""
    ev = pd.read_csv(DATA / "lesson_events.csv", parse_dates=["completed_at"])
    return ev.loc[ev.user_id.isin(d.user_id)]


# ---------------------------------------------------------------- signup-window cutoffs
def p95_days(s):
    return int(s.dropna().quantile(PCT, interpolation="higher"))


def stage_days(d):
    """Whole days between stages, for students who reached the later stage (NaN otherwise)."""
    # permit_exam_date is the most recent attempt, so for 2-attempt students this
    # overstates time to first exam. That makes the window longer (conservative).
    taken = d.permit_result.isin(["passed", "failed"])
    return {
        "Signup -> First Video": (d.ev_first_video_at - d.signup_at).dt.days,
        "First Video -> Course Complete": (d.ev_course_completed_at - d.ev_first_video_at).dt.days,
        "Course Complete -> Exam taken": (d.permit_exam_date - d.ev_course_completed_at.dt.normalize())
        .dt.days.where(taken),
        "Signup -> Permit passed": (d.permit_exam_date - d.signup_at.dt.normalize()).dt.days
        .where(d.permit_passed),
    }


def cutoffs(d):
    """Latest date a student can have entered each stage and still count in its rate.

    fv:  FV/CA      signed up on or before
    cc:  CC/FV      first video on or before
    p:   Permit/CC  course complete on or before
    all: Permit/CA  signed up on or before
    l5:  lesson-5 metric, first video on or before (fixed WINDOW, not a percentile)
    """
    days = {k: p95_days(v) for k, v in stage_days(d).items()}
    cut = lambda k: SNAPSHOT - pd.Timedelta(days=days[k])
    return {
        "fv": cut("Signup -> First Video"),
        "cc": cut("First Video -> Course Complete"),
        "p": cut("Course Complete -> Exam taken"),
        "all": cut("Signup -> Permit passed"),
        "l5": SNAPSHOT - pd.Timedelta(days=WINDOW),
    }


# ---------------------------------------------------------------- student flags and pools
def add_flags(d, ev):
    """Adds the per-student flags every analysis uses. Returns d."""
    d["l5_at"] = d.user_id.map(ev.loc[ev.lesson_number == 5].set_index("user_id").completed_at)
    d["fv_to_l5_days"] = (d.l5_at - d.ev_first_video_at).dt.total_seconds() / 86400
    d["l5_in_window"] = d.fv_to_l5_days <= WINDOW
    d["reached_5"] = d.ev_max_lesson >= 5
    d["stopper"] = d.ev_first_video & (d.ev_max_lesson <= EARLY_MAX)
    d["segment"] = d.ev_first_video & (d.has_training_plan == "yes") & (d.joined_group_chat == "no")
    d["no_chat"] = d.ev_first_video & (d.joined_group_chat == "no")
    return d


def cc_pool(d, cut):
    """Students old enough to have finished the course: first video on or before the CC/FV cutoff."""
    return d.loc[d.ev_first_video & (d.ev_first_video_at <= cut["cc"])].copy()


def eligible_now(d):
    """Pilot eligibility at the snapshot: target segment, lessons 1-4, first video in the last WINDOW days."""
    return d.loc[d.segment & (d.ev_max_lesson <= EARLY_MAX)
                 & (d.ev_first_video_at > SNAPSHOT - pd.Timedelta(days=WINDOW))]


def lowest_full_month(first_video_at):
    """Fewest first videos in any full calendar month before the snapshot month (conservative volume)."""
    m = first_video_at.dt.to_period("M").value_counts().sort_index()
    return int(m.loc[m.index < SNAPSHOT.to_period("M")].min())


# ---------------------------------------------------------------- pilot sizing
def mde(p0, n_arm):
    """Minimum detectable lift (fraction) for a two-arm test of proportions."""
    lo, hi = 0.0, 1 - p0
    for _ in range(60):
        delta = (lo + hi) / 2
        p1 = p0 + delta
        need = (Z_ALPHA * math.sqrt(2 * ((p0 + p1) / 2) * (1 - (p0 + p1) / 2) / n_arm)
                + Z_POWER * math.sqrt((p0 * (1 - p0) + p1 * (1 - p1)) / n_arm))
        lo, hi = (delta, hi) if need > delta else (lo, delta)
    return hi


def chi2_p(table):
    """Pearson chi-square p-value; Wilson-Hilferty approximation (no scipy)."""
    obs = table.to_numpy(dtype=float)
    exp = obs.sum(axis=1, keepdims=True) * obs.sum(axis=0) / obs.sum()
    x = ((obs - exp) ** 2 / exp).sum()
    k = (obs.shape[0] - 1) * (obs.shape[1] - 1)
    z = ((x / k) ** (1 / 3) - (1 - 2 / (9 * k))) / math.sqrt(2 / (9 * k))
    return 0.5 * math.erfc(z / math.sqrt(2))


# ---------------------------------------------------------------- consistency check
def _plain(v):
    """JSON-safe value: timestamps as text, numpy scalars as plain Python numbers."""
    return f"{v:%Y-%m-%d %H:%M}" if isinstance(v, pd.Timestamp) else v.item() if hasattr(v, "item") else v


def record(script, **numbers):
    """Store a script's headline numbers in key_numbers.json, stamped with the snapshot."""
    data = json.loads(KEY_NUMBERS.read_text()) if KEY_NUMBERS.exists() else {}
    data[script] = {"snapshot": f"{SNAPSHOT:%Y-%m-%d %H:%M}", **{k: _plain(v) for k, v in numbers.items()}}
    KEY_NUMBERS.write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")


def check(script, **numbers):
    """Compare numbers against what other scripts recorded. Returns a list of mismatch messages.

    Keys are "<script>.<name>". A missing script or a different snapshot counts as a mismatch,
    so a stale or skipped script is caught too.
    """
    data = json.loads(KEY_NUMBERS.read_text()) if KEY_NUMBERS.exists() else {}
    snap = f"{SNAPSHOT:%Y-%m-%d %H:%M}"
    problems = []
    for key, mine in numbers.items():
        src, name = key.split(".", 1)
        rec = data.get(src)
        if rec is None:
            problems.append(f"{src}.py has no recorded numbers. Run it before {script}.py.")
        elif rec.get("snapshot") != snap:
            problems.append(f"{src}.py was last run on snapshot {rec.get('snapshot')}, not {snap}. Rerun it.")
        elif rec.get(name) != _plain(mine):
            problems.append(f"{key}: {src}.py says {rec.get(name)}, {script}.py says {_plain(mine)}")
    return sorted(set(problems))
