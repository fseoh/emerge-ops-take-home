# Emerge Career: Ops Take-Home ("1 in 10")

Thanks for taking the time. This is the work you'd do in your first 90 days, not a puzzle.

**Time box: 3 hours.** Stop at 3. If you run short, finish Part 1 and the memo, then sketch the rest.

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

Your numbers from this dataset won't match exactly. Tell us why.

---

## Part 1: Diagnose the funnel (about 75 min)

Build a view someone on our team could open Monday morning. Any format works: HTML, notebook, Markdown tables, or a spreadsheet.

It should answer:

1. **Stage conversion** for the three stages above, overall and by city. Say how you handled students who signed up too recently to have finished.
2. **Where in the 21 lessons do starters drop?** Show the lesson-by-lesson curve. Name the point after which students almost always finish.
3. **What separates students who make it past that point from those who don't?** Look at the training plan, community, device, referral source, and city fields. Be careful about what's cause and what's correlation.
4. **Who can we still help this week?** A list of current students worth reaching now, with your rule for picking them.

## Part 2: The community plan (about 75 min)

### 2a. Plan

Design a community program that moves more starters through the course. Keep it to what a team of ~10 can actually run. Cover:

- **Who it targets** (use the data to define the segment and size it)
- **What it is** (formats, cadence, who runs it, rough weekly hours or cost)
- **How it differs by city,** if it should
- **The one number you'd move** and by how much in 90 days
- **How you'd prove it worked.** Some of these signals are self-selected. Tell us how you'd test it.

### 2b. Outreach drafts

Write **3 messages** (SMS or group chat) to real `user_id`s from your Part 1 list. Ground each one in that student's data. Put them in `outbox/`, one file each, named `<user_id>.md`. **Do not send anything.**

### 2c. Automation spec

Spec (or code) the trigger that would draft these messages automatically. Cover:

- What event or state change fires it, and how you avoid messaging the same person every day
- Timing (when in their day, how soon after they stall)
- Who never gets an automated message
- Where a human reviews before anything goes out
- What you'd check before turning it on for real

---

## Deliverables

1. **Your analysis:** code, notebook, or spreadsheet that rebuilds your numbers from `data/`. Put it in `analysis/`.
2. **Your Monday view** from Part 1.
3. **`COMMUNITY_PLAN.md`** (Part 2a) and **`AUTOMATION.md`** (Part 2c).
4. **`outbox/`** with 3 message drafts.
5. **`MEMO.md`**, half a page max, using the template already in this repo.
6. **`ai_usage/`**: your key prompts or a session transcript. We want to see how you steered the tool, including where you pushed back on it.

Send a zip or a repo link.

## How we'll evaluate

- **Funnel read.** Did you find the real drop-off point and handle recent signups honestly?
- **Judgment.** Do you separate correlation from cause, and does your plan fit a small team?
- **Specificity.** Do the messages and the plan use the data, or could they be about anyone?
- **Care.** Our students have been through a lot. Does your outreach respect that? Does your automation protect them from spam and mistakes?
- **AI leverage.** Did you use the tool well and catch it when it was wrong?
- **Prioritization.** Something unfinished with a clear rationale beats something polished and narrow.

## Ground rules

- The data is synthetic. No real students are in it.
- Don't send messages, post anything, or contact anyone.
- Questions? Email us. If we can't answer fast, make a call, write down your assumption, and keep going.
