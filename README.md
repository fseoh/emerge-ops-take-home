# Emerge Career: Ops Take-Home ("1 in 10")

Thanks for taking the time. This is the work you'd do in your first 90 days, not a puzzle.

**Time box: 3 hours.**

**Use Claude Code (or your AI tool of choice) for the heavy lifting.** We care about your judgment and how you direct the tool, not whether you hand-write pandas. Read `CLAUDE.md` first; it sets the rules your AI tool should follow in this repo.

---

## Context

Emerge Career trains justice-impacted people for CDL (commercial driver's license) careers in **NYC, Sacramento, and Boston**. The path looks like this:

1. **Create account (CA).** Student signs up and usually builds a training plan (pace, study days, target permit date).
2. **First video (FV).** Student finishes Lesson 1. This is activation.
3. **Course complete (CC).** Student finishes all 21 online lessons.
4. **Permit (CLP).** Student sits the Commercial Learner's Permit written exam in person at the DMV and passes.

Today, roughly **1 in 10 signups ends up holding a permit.** Most of the loss happens between the first video and finishing the course.

Your job: figure out where and why students drop, and design a **community plan** that gets more of them through.

## The data

Synthetic exports live in `data/`. The snapshot was taken **September 15, 2026 at 6:00 AM ET**. The field-by-field definitions are in `data/DATA_DICTIONARY.md` (same content as a spreadsheet in `data/README.csv`).

| File | Grain | Rows |
|---|---|---|
| `data/students.csv` | one row per student (user summary) | ~3,000 |
| `data/lesson_events.csv` | one row per lesson a student completed | ~20,000 |
| `data/lessons.csv` | one row per lesson in the course | 21 |

Students by city: NYC ~2,000, Sacramento ~750, Boston ~250. The data is not perfectly clean. Real exports never are.

## The funnel you're working on

We only care about three stage conversions:

| Stage | What it measures |
|---|---|
| CA → First Video | Activation |
| First Video → Course Complete | Course completion among starters |
| Course Complete → Permit | Permit pass among completers |

For reference, our NYC funnel tracker measured these in July 2026:

| | Jul 1, 2026 | Jul 16, 2026 |
|---|---|---|
| CA → First Video | 68.8% | 67.5% |
| First Video → Course Complete | 31.7% | 49.0% |
| Course Complete → Permit | 35.6% | 46.4% |

These are for reference. Your numbers from this dataset won't match exactly.

---

## The task: A community plan

Design a community program that moves more starters through the course. Keep it to what a team of ~10 can actually run. Cover:

- **Who it targets** (use the data to define the segment and size it)
- **What it is** (formats, cadence, who runs it)
- **How you'd measure it** (the one number you'd move, and how you'd prove it — some signals are self-selected)

---

## Deliverables

1. **`COMMUNITY_PLAN.md`**: your plan.
2. **Any analysis** that backs it up — code, notebook, spreadsheet, or tables. Put it in `analysis/`. We want to see the numbers your plan rests on and be able to rebuild them from `data/`.
3. **`MEMO.md`**, half a page max, using the template already in this repo.
4. **`ai_usage/`**: your key prompts or a session transcript. We want to see how you steered the tool, including where you pushed back on it.

Send a zip or a repo link.

## How we'll evaluate

- **Critical thinking.** Did you dig into the data to find where and why students actually drop, handle recent signups honestly, and separate correlation from cause?
- **Strategy.** Does the plan fit a small team, move the right number, and respect that our students have been through a lot?
- **AI fluency.** Did you use the tool well and catch it when it was wrong?
- **Prioritization & execution.** Does the plan use the data specifically? Something unfinished with a clear rationale beats something polished and narrow.

## Ground rules

- The data is synthetic. No real students are in it.
- Don't send messages, post anything, or contact anyone.
- Questions? Email us. If we can't answer fast, make a call, write down your assumption, and keep going.
