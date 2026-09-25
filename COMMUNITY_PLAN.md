# Community Plan

## Summary

- **Where students are lost:** between their first video and the end of lesson 4. Of students in the first-video pool who don't finish the course, 85.2% (717/842) stop there. Once students reach lesson 5, 82.9% (605/730) finish.
- **Who we target:** students who watched the first video and made a training plan but never joined their city's group chat. That's 600 of the 1,447 students in the first-video pool (41.5%), and 321 of the 717 who stopped at lessons 1–4 (44.8%).
- **What we change:** one thing. Whether a new student in the segment gets a personal, first-week text inviting them into the group chat. Half get it and half don't, chosen at random.
- **How we know it worked:** students who got the invite reach lesson 5 within 21 days of their first video more often than students who didn't, and the 95% confidence interval for the difference stays above zero. We count everyone assigned to outreach, not only the students who respond. Full rule in "The test" below.
- **The honest caveat:** chat members reach lesson 5 far more often (among plan holders, 76.7%, 253/330, vs 46.5%, 279/600). But students choose to join, and we don't know when they joined. The pilot exists to find out how much of that gap the chat actually causes. At current volume it can only detect a large effect in one quarter. That is the main risk to this plan.

Every number here comes from the scripts in `analysis/`. Data problems and assumptions are in `analysis/DATA_NOTES.md`. Sentences marked **Judgment call** are my reasoning, not something the data shows.

**To run it:** open the live dashboard at https://fseoh.github.io/emerge-ops-takehome/Dashboard/ (or `Dashboard/index.html` locally). It has today's outreach list, the lesson-5 metric by month, and the pilot's decision rule. Draft texts for the two touches are in `outbox/`. Nothing is sent from either.

---

## The test: what we change and how we know it worked

| | |
|---|---|
| **The one thing we change** | Whether a student gets the personal chat invite: up to 2 texts in the first week after their first video, from their city's coach or community lead, with the WhatsApp join link. |
| **Who decides who gets it** | Random, 50/50, when the student enters the segment. Not the coach and not the student. |
| **What stays the same for both groups** | The chat invite at signup, the lessons, the training plan, coach calls and study hall. Coach calls are logged in both groups to check this. |
| **What it should move first** | Joining the chat within 7 days. If the invite doesn't raise joins, it can't work through the chat. |
| **The outcome that decides it** | % reaching lesson 5 within 21 days of first video. Everyone assigned to a group counts, whether or not they read the text or joined. |
| **Starting point** | 44.5% (267/600) of the segment did this historically. If we widen to everyone not in the chat: 36.5% (337/924). **Judgment call: the real control rate is probably higher.** The segment uses chat status at the snapshot, but the pilot enrolls students by their status at first video. Students who joined the chat later, perhaps after making progress, aren't in the 600. Without join dates we can't say by how much. So judge the pilot against its own control group, never against 44.5%. |
| **Success: scale it** | At the final read, the invited group's rate minus the control group's rate is above zero, the 95% confidence interval stays above zero, and the lift is at least the smallest lift worth scaling (set before launch, see below). The opt-out rate stays under its limit. |
| **Redesign the message** | At the end of month 1, the invited group joins the chat no more often than the control group. The text isn't changing the thing it's meant to change. |
| **No proven effect** | The interval includes zero. Report it as "no lift as large as the pilot could detect" (14.7 points at 3 months for the segment, 11.7 if widened), not as "no effect". |
| **Decided before launch** | Program manager, in writing: (1) segment only or widened; (2) the smallest lift worth scaling; (3) the highest acceptable opt-out (STOP) rate; (4) if widened, when to text students with no training plan. They have no study days or times, and the timing rule depends on those. **Judgment call:** the data can't set these. There are no past texts to learn from, and the value of an extra lesson-5 student is a program decision. |
| **Needed before we can measure** | An outreach log (group, send times, replies, STOP) and chat join dates. Today the data has neither, so "joined within 7 days" can't be measured yet. See "What to track going forward". |

**Why randomize instead of comparing joiners with non-joiners:** students choose to join the chat, so comparing joiners with non-joiners mixes up the chat's effect with who chooses to join (CLAUDE.md rule 7). Randomizing the invite is the only way to measure the chat's effect with this data.

---

## Who it targets

**The segment:** students who completed lesson 1, have `has_training_plan = yes`, and have `joined_group_chat = no`.

**Pool used to size it:** the 1,447 students whose first video was on or before Jul 18, 2026. That cutoff gives each of them time to have finished the course (95% of finishers do so within 59 days of their first video).

| | Students | Share |
|---|---|---|
| First-video pool | 1,447 | 100% |
| **Target segment** (plan yes, chat no) | **600** | **41.5%** |
| Pool students who stopped at lessons 1–4 | 717 | |
| Of those, in the target segment | 321 | 44.8% of stoppers |

**Why lessons 1–4:**

| | Value | Source |
|---|---|---|
| Non-finishers who stopped at lessons 1–4 | 85.2% (717/842) | `lesson_dropoff_output.txt` |
| Students who reached lesson 5 and finished | 82.9% (605/730) | `lesson_dropoff_output.txt` |
| Stop rate per lesson, lessons 1–4 | 13.3–19.2% | same |
| Stop rate per lesson, lessons 5–20 | 0.5–1.9% | same |

**Why this segment and not all stoppers:**
- It is the largest single group of stoppers.
- These students already did the planning step, so they signed up with some intent.
- They were offered the chat invite at signup and didn't join, so a second, personal invite is a concrete next step.

Students with no plan and no chat have the lowest rate of reaching lesson 5 (23.5%, 76/324). They're the next segment to try. **Judgment call:** I start with plan holders because the invite is one simple ask, and their existing plan tells us when and how to reach them.

**Segment profile** (useful for staffing and language):

| City | Students | | Language | Students |
|---|---|---|---|---|
| NYC | 387 | | English | 495 |
| Sacramento | 157 | | Spanish | 100 |
| Boston | 56 | | Haitian Creole | 5 |

Planned study time: evening 252, morning 136, afternoon 116, late night 96.

**Flow:** about 120–139 new segment students per month (by first-video month, Mar–Aug 2026). At the snapshot, 63 students were in the segment, still at lessons 1–4, and within 21 days of their first video.

---

## What it is

**A first-week, personal invite into the city group chat**, for plan holders who haven't joined.

| Element | Design | Basis |
|---|---|---|
| Trigger | Student completes lesson 1, has a plan, isn't in the chat | Segment definition |
| First touch | Within 1–2 days of first video | Median gap from lesson 1 to 2 is 1.95 days, and 13.4% (194/1,447) stop after lesson 1. **Judgment call:** reach them before the next lesson is due. |
| Second touch | Once, about day 4–5, only if still not in the chat | **Judgment call.** Two touches max, to avoid pestering. |
| Timing | Sent in the student's `plan_study_time` window, on a `plan_study_days` day | CLAUDE.md. Every student in the segment has these fields. |
| Channel & sender | SMS from the student's city coach or community lead, with the WhatsApp join link | **Judgment call.** A personal sender is more likely to work than a system blast. Untested. |
| Content | Warm, plain, one step: "Join your city group. Study hall times are posted there." Offer of help. "Reply STOP to stop texts." Drafts in English and Spanish are in `outbox/`; Haitian Creole is marked NEEDS TRANSLATION. | CLAUDE.md writing rules. Study hall is announced only in the chat (data dictionary). |
| Language | Student's `preferred_language`. Haitian Creole drafts marked NEEDS TRANSLATION until reviewed | CLAUDE.md |
| Never | Mention of record, parole, or probation. Deadlines, urgency, or job or pay promises | CLAUDE.md |

**Owners and cadence** (**Judgment call:** role names are placeholders; Emerge will know the right people):

| Owner | Does what | Cadence | Metric they watch |
|---|---|---|---|
| Community lead (one per city) | Sends touches to that day's eligible list; welcomes new joiners in the chat | Daily | % of treated students who join within 7 days |
| Ops analyst | Builds the daily list, assigns treatment or control at random, logs every send | Daily list, weekly readout | Sends logged, arm balance |
| Program manager | Reviews pilot results; decides to scale, change, or stop | Every 2 weeks, plus a final read | % reaching lesson 5 within 21 days, treatment vs control |

**Where the evidence is stronger vs weaker:**

| Lever | Observed link | How sure we are about the order of events | Confidence |
|---|---|---|---|
| **Training plan** | Plan holders reach lesson 5 more often (57.2%, 532/930, vs 38.3%, 198/517) | **Known.** 928 of 930 plans (99.8%) were made before the student completed lesson 2. The plan comes before the drop-off zone. | Higher. Students still choose to make a plan. |
| **Group chat** | Among plan holders, 76.7% (253/330) vs 46.5% (279/600) reach lesson 5 (a 30.2-point gap). This is the largest gap observed. | **Unknown.** There's no join date. Some students may join *because* they're progressing. | Lower. The gap is bigger, but the cause is unproven. |

So why pilot the chat and not the plan? **Judgment call:** most students already have plans (930 of 1,447, 64.3% of the pool), and plan-making happens in onboarding. The chat has the bigger possible upside and the bigger unknown. A randomized pilot settles that unknown, which the observational data can't.

---

## How we'd measure it

### Pilot design

- **Population:** every new student who enters the segment (first video, plan, no chat), enrolled on a rolling basis. Widening it is recommended below; the program manager picks before launch.
- **Randomization:** 50/50 at entry, by the ops analyst, before any outreach. The control group gets business as usual (the signup invite they already had).
- **Primary metric:** % reaching lesson 5 within **21 days** of first video.
  - Why lesson 5: it's where the drop-off ends. Past it, 82.9% (605/730) finish.
  - Why 21 days: among pool students who ever reached lesson 5, 94.9% (693/730) did so within 21 days (median 10.1 days).
  - Why not course completion: it takes up to 59 days after the first video, and permits up to 88 days after signup. Lesson 5 at 21 days reads out 1–2 months sooner.
- **Control baseline:** historically 44.5% (267/600) of this segment reached lesson 5 within 21 days.
- **Secondary metrics:**
  1. % who join the chat within 7 days (did the outreach work at all?)
  2. % completing the course within 59 days
  3. Opt-out (STOP) rate

### Handling self-selection

- **Intent-to-treat.** Compare *everyone assigned* to outreach against *everyone in control*, whether or not they read the text or joined. Comparing joiners to non-joiners would repeat the self-selection problem we're trying to escape.
- The chat-join rate in each arm tells us how much the outreach moved behaviour. If it doesn't raise joins, a null result on lesson 5 says nothing about the chat itself.
- **Coach calls:** log them in both arms. Every student who reached lesson 5 had at least one call (see open questions). If call scheduling differs between arms, it could skew the result.

### Sample size, stated honestly

Assumptions: 120 new segment students per month (the lowest full month), 50/50 split, α = 0.05 two-sided, 80% power, baseline 44.5%.

| Enrollment | Per arm | Smallest detectable lift (percentage points) |
|---|---|---|
| 1 month | 60 | 25.1 |
| 2 months | 120 | 18.0 |
| 3 months | 180 | 14.7 |
| 4 months | 240 | 12.8 |

What might a realistic effect be? Intent-to-treat effect ≈ (share who join *because of* the outreach) × (true effect of joining). **Judgment call:** the observed 30.2-point gap is probably an upper bound on that true effect, because it includes self-selection: students who choose to join may be more motivated to begin with. The data can't confirm this. These are hypotheticals, not predictions:

| Extra joins from outreach | If joining is worth the full 30.2 pts | If it's worth half |
|---|---|---|
| 10% | 3.0 pts | 1.5 pts |
| 20% | 6.0 pts | 3.0 pts |
| 30% | 9.1 pts | 4.5 pts |
| 50% | 15.1 pts | 7.5 pts |

**What this means:** a 3-month pilot on this segment only detects a lift of about 15 points. That requires both high uptake and a chat effect close to the observed gap. More modest (and more likely) effects would show up as "no significant difference." Three ways to respond:

1. **Widen the randomized population** to all first-video students not in the chat, plan or no plan. Baseline is 36.5% (337/924), with at least 185 new students per month. The smallest detectable lift improves to 14.4 pts at 2 months, 11.7 at 3 and 10.1 at 4. Pre-register plan holders as the main subgroup. Students without a plan need a default send time (see "The test"). **Recommended.** Owner: program manager, before launch. Metric: smallest detectable lift at the planned enrollment.
2. **Use the join rate as an early go/no-go.** It moves more and needs fewer students. If outreach doesn't lift joins within the first month, redesign the message before waiting on lesson 5. Owner: program manager, end of month 1. Metric: % joining the chat within 7 days, treatment vs control. This needs chat join dates, which the data doesn't have yet.
3. **Treat a null result as "not large," not as "zero."** Report the confidence interval, not just the p-value. Owner: ops analyst, at every readout (every 2 weeks). Metric: 95% confidence interval of the lift.

---

## What the data shows

Full detail and data problems are in `analysis/DATA_NOTES.md`. Rebuild everything from `data/` with:

```
pip install -r analysis/requirements.txt
python3 analysis/clean_data.py
python3 analysis/cohort_windows.py
python3 analysis/lesson_dropoff.py
python3 analysis/pilot_sizing.py
python3 analysis/coach_calls_finishers.py
python3 analysis/coach_calls_engagement.py
python3 analysis/dashboard_data.py
```

**Data handling:** 9 test accounts dropped, 43 city labels normalized, and funnel stages taken from `lesson_events.csv`. That leaves 3,000 real students: NYC 2,000, Sacramento 750, Boston 250.

### 1. Funnel

Recent students haven't had time to finish, so each rate only counts students old enough to have reached that stage (95th-percentile time-to-stage). Source: `cohort_windows_output.txt`.

| Stage | Rate | Who's included |
|---|---|---|
| First Video / signups | 66.8% (1,947/2,916) | Signed up by Sep 6 |
| Course Complete / First Video | **41.8% (605/1,447)** | First video by Jul 18 |
| Permit / Course Complete | 44.1% (235/533) | Completed by Aug 6 |
| Permit / signups | 12.3% (212/1,727) | Signed up by Jun 19 |

In the Jun 19 cohort (1,727 signups), students lost at each step:

| Step | Students lost |
|---|---|
| Before First Video | 560 |
| **First Video → Course Complete** | **680** |
| Course Complete → Permit | 275 |

The largest loss is between the first video and course completion.

### 2. Where students stop

Pool: first video by Jul 18, n = 1,447. Source: `lesson_dropoff_output.txt`.

| Highest lesson reached | Students | Stop rate (stopped / reached) | Video minutes |
|---|---|---|---|
| 1 | 194 | 13.4% | 8 |
| 2 | 167 | 13.3% | 32 |
| 3 | 209 | 19.2% | 44 |
| 4 | 147 | 16.8% | 41 |
| 5–20 | 3–12 each, 125 total | 0.5–1.9% each | 12–26 |
| 21 (finished) | 605 | | 12 |

- **It's a cliff, not a steady leak.** Stop rates fall from 13–19% per lesson to about 1% after lesson 4.
- **Pace changes at the same point.** Median days between lessons is about 2 for lessons 1→5, then about 1 for every lesson after.
- **Students who stop at lessons 1–4 are gone, not paused.** The most recent of them did a lesson 49.5 days before the snapshot, and none was seen in the last 14 days.
- **Lessons 2–4 have the three longest videos** (32–44 min vs 12–26 for lessons 5–21). **Judgment call:** that is worth testing (for example, splitting lesson 3), but the data only shows they go together. Owner: curriculum lead (placeholder), after the chat pilot so the two tests don't mix. Metric: lesson 3 stop rate, now 19.2% (209/1,086).

### 3. Training plan × group chat

Share reaching lesson 5+. Pool: first video by Jul 18, n = 1,447. Source: `lesson_dropoff_output.txt`, table 5.

| Plan | Chat | Students | % of pool | Reached lesson 5+ |
|---|---|---|---|---|
| yes | yes | 330 | 22.8% | **76.7%** (253) |
| no | yes | 193 | 13.3% | 63.2% (122) |
| **yes** | **no** | **600** | **41.5%** | **46.5%** (279) |
| no | no | 324 | 22.4% | 23.5% (76) |

Each factor goes with higher progress on its own, and the two add up. Chat has the larger gap at either plan level:

| Factor | Gap without the other factor | Gap with it |
|---|---|---|
| Chat | +39.7 pts (no plan) | +30.2 pts (with plan) |
| Plan | +23.0 pts (no chat) | +13.5 pts (with chat) |

Both are choices students make. None of these gaps prove cause (CLAUDE.md rule 7).

### 4. What doesn't separate students

Share reaching lesson 5+ by fields known at signup. Pool: first video by Jul 18, n = 1,447. Source: `lesson_dropoff_output.txt`, table 6. p-values are approximate chi-square tests.

| Field | Range of reach-5 rates across values | p | Separates? |
|---|---|---|---|
| Group chat | 38.4% (no, n=924) to 71.7% (yes, n=523) | ~5e-22 | Strongly |
| Training plan | 38.3% (no, n=517) to 57.2% (yes, n=930) | ~8e-10 | Strongly |
| Primary device | 33.0% (shared computer, n=88) to 56.5% (laptop, n=324) | ~0.001 | Moderately; the low group is small |
| Referral source | 41.9% (paid social, n=339) to 55.9% (reentry org, n=424) | ~0.003 | Moderately |
| City | 49.1% (Boston, n=110) to 52.0% (Sacramento, n=379) | ~0.78 | No |
| Age band | 45.5% (55+, n=77) to 54.4% (45–54, n=193) | ~0.73 | No |
| Preferred language | 49.9% (English, n=1,193) to 66.7% (Haitian Creole, n=9) | ~0.46 | No |
| Signup month | 48.1% (Jul, n=158) to 52.2% (Jun, n=291) | ~0.87 | No |

- City doesn't separate students up to lesson 5, so the outreach runs the same way in all three cities.
- City does matter after the course. Permit / Course Complete: Sacramento 51.7% (74/143), NYC 42.3% (149/352), Boston 31.6% (12/38), p ≈ 0.04 (course complete by Aug 6; `cohort_windows_output.txt`). This plan doesn't change that, but the next one should look at it.
- Referral source is for analysis only and never appears in student messages (CLAUDE.md).
- **Judgment call:** shared-computer users (library, reentry center) may need a different touch, such as study-hall times they can attend in person. The group is too small (88) to design around yet.

### 5. Related findings outside this plan

- **Finishing the course doesn't mean taking the exam.** In the Jun 19 cohort, 487 finished the course and 212 passed the permit. 233 of the 275 who didn't pass still have `course_complete` status with no exam on record. They look like non-takers, not failures. That makes it a candidate for the next plan. Owner: program manager, scoped after the chat pilot's first readout. Metric: Permit / Course Complete, now 44.1% (235/533).
- **Seats.** The funded seats in `seats_by_city.csv` compare to permits passed so far as follows:

| City | Seats | Permits passed so far |
|---|---|---|
| NYC | 200 | 166 |
| Sacramento | 75 | **94** |
| Boston | 25 | 14 |

The data doesn't say what period the seats cover. **Judgment call:** if they're annual, Sacramento may already have more permit holders than funded seats. Moving more students through there may not produce more trainees. Worth confirming before scaling by city.

---

## What to track going forward

Both gaps limit what this analysis can claim. Closing them is part of the plan, not a footnote. Details are in `analysis/DATA_NOTES.md`, "Open questions for Emerge."

| Gap | Why it matters | What to start logging | Owner (placeholder) |
|---|---|---|---|
| **Coach calls have no dates.** All 3,000 real students: 0 of the 1,423 with no calls got past lesson 4. Students with a first video by Jul 18 who stopped at lessons 1–4: 418 of 717 (58.3%) had a call. | We assume a call doesn't unlock lesson 5 (see `analysis/DATA_NOTES.md`), but can't tell if calls help progress or are a required process step. Calls can't be treated as a lever until we know. | Call log with timestamp, student, coach, outcome. Confirm whether any call is required at a set lesson. | Coaching lead |
| **Chat has no join date.** | We can't tell whether joining comes before or after progress. The pilot answers this for treated students, but only going forward. | Join date per student from the WhatsApp admin log or invite-link tracking. Record whether each join came from the signup invite or a later touch. | Community lead |
| **Outreach has no log** (new for the pilot) | Needed for intent-to-treat analysis | Per student: arm, send times, touches, replies, STOP | Ops analyst |
| **Seat period** | Decides whether more finishers become more trainees | Seats per city with the time period they cover | Program manager |
