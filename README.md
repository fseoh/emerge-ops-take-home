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

## The task: A community plan

Design a community program that moves more starters through the course. Cover:

- **Who it targets** (use the data to define the segment and size it)
- **What it is** (formats, cadence, who runs it)
- **How you'd measure it** (the one number you'd move, and how you'd prove it — some signals are self-selected)

Also build a **dashboard** the team could use to run this plan day to day — who to reach, how the target number is trending, whether it's working. Any format works.

---

## Deliverables

1. **`COMMUNITY_PLAN.md`**: your plan.
2. **A dashboard** to operationalize the plan. Any format works.
3. **Any analysis** that backs it up — code, notebook, spreadsheet, or tables. Put it in `analysis/`. We want to see the numbers your plan rests on and be able to rebuild them from `data/`.
4. **`ai_usage/`**: your key prompts or a session transcript. We want to see how you steered the tool, including where you pushed back on it.

Send a zip or a repo link.

## How we'll evaluate

- **Critical thinking**
- **Strategy**
- **AI fluency**
- **Prioritization & execution**

## Ground rules

- The data is synthetic. No real students are in it.
- Don't send messages, post anything, or contact anyone.
- Questions? Email us. If we can't answer fast, make a call, write down your assumption, and keep going.
