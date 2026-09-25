# AI Usage: Key Prompts

This log shows how I used Claude Code to build the analysis, `COMMUNITY_PLAN.md`, and the dashboard. It covers five sessions on 2026-09-23, from about 19:57 to 23:00 ET, and follow-up sessions on 2026-09-25 (Phase 7). Prompts are quoted or lightly shortened.

## How I worked with Claude

- **Explore before writing.** Exploration prompts said "don't modify any files." A finding was saved to `analysis/` only after I had seen and questioned the numbers.
- **Findings live in scripts.** Every saved number comes from a script that rebuilds from the raw `data/` files.
- **Narrow the question step by step.** All students, then cohorts with time to finish, then the first-video pool, then the lesson 1–4 stall, then the plan × chat segment.
- **Ask whether data can support a claim.** When a pattern suggested a cause, I first checked whether the data could establish the order of events.
- **Get an independent review.** A separate session re-derived the numbers from raw data before I built on the plan.
- **Make the tool audit itself.** I asked Claude to check its own output for drift in a long thread, and to look for damage from a second session editing the same files.
- **Hold it to a written standard.** I pasted an engineering standard ("the dashboard should be a presentation layer") and asked Claude to confirm its work met it. It said no, and I made the tradeoff knowingly.
- **Ask for verification, not reassurance.** "Confirm it only reads from analysis/" got a "no" with evidence, which led to a refactor.

## Tools and integrations

| What | How I used it |
|---|---|
| `CLAUDE.md` guardrails | Hard rules the tool had to follow: never send messages, drafts only in `outbox/`, `data/` read-only, every rate with its denominator, correlation ≠ cause. Checked against every deliverable in Prompt 21. |
| Separate sessions | One session built the plan, and a fresh one reviewed it from raw data (Phase 5). Later, two sessions ran in parallel, and I had one audit the other's damage (Phase 7). |
| Git as an audit trail | Found the overwritten notes by diffing against the last commit. Used `reflog` and `git cherry` to confirm a deleted side branch's work was already on `main`. |
| Persistent memory | Claude kept a note that `main` is the submission branch and updated it when the side branches were deleted. |
| Skills | The data-visualization skill's palette validator checked chart colors for colorblind separation and contrast, in light and dark mode. |
| Headless browser | Chrome (via Puppeteer) and jsdom rendered the dashboard to catch script errors, screenshot it, and measure sideways scrolling at 360–1280 px. |
| Build gate | `analysis/key_numbers.json`: the dashboard refuses to build if 26 numbers shared with the analysis scripts disagree. |

---

## Phase 1: Data audit (read-only)

**Prompt 1: inventory the data**
> Look at data/DATA_DICTIONARY.md and then inspect students.csv, lesson_events.csv, lessons.csv, and seats_by_city.csv. Don't change anything yet. Tell me: row counts, column types, obvious duplicates, missing values, and anything that looks inconsistent (like dates that don't make sense, or lessons_completed disagreeing with lesson_events.csv).

This found:
- 9 test accounts
- 10 `NYC ` city labels with a trailing space
- `lessons_completed` values that disagree with the event log
- 11 rows where the 3-day engagement total is larger than the 7-day total, which should be impossible

**Prompt 2: test an unstated assumption**
> Is there a column to determine whether 3-day engagement and/or 7-day engagement is counting within consecutive hours or week days (i.e. skipping Saturdays or Sundays)

- No column says how the windows are counted, so Claude tested it against lesson timestamps.
- 65 students had lessons in the last 72 hours only on a Saturday or Sunday. All 65 have 3-day minutes, so weekends count.
- The only students who don't fit a rolling window were already among the 11 flagged rows.
- This was logged as an assumption in `DATA_NOTES.md`, not treated as fact.

## Phase 2: Cleaning rules, written to files

**Prompt 3: my cleaning plan**
> Write what inconsistencies/flags you found to analysis/DATA_NOTES.md with rerunnable scripts in analysis/. My plan:
> - Drop the 9 test accounts.
> - Normalize the city labels (making sure to check for city labels that have a rogue space after or before)
> - Use the event log for every funnel stage.
> - Keep the other issues flagged rather than "fixed."

- **Created:** `analysis/clean_data.py`, `students_clean.csv`, and a "Flagged, not fixed" table in `DATA_NOTES.md`.
- **Test accounts:** two independent rules find them, the ID pattern and `referral_source = internal`. Both pick out the same 9 rows.
- **City labels:** Claude checked every column in every file for spaces before or after a value. City totals came out to exactly 2,000 NYC, 750 Sacramento and 250 Boston, which matches the README. If a new label appears that the script can't map, it stops instead of guessing.
- **Self-correction:** with the test rows removed, all 14 real `lessons_completed` mismatches were off by exactly 1 lesson. Claude said plainly that its first summary had been wrong: the larger gaps had come from test accounts.

**Signup-window cutoffs (pushback on my first idea)**

I proposed dropping September signups because the month wasn't over. Claude pushed back with data:
- **The real issue is time to finish, not a short month.** A recent student who hasn't finished hasn't dropped out yet.
- **It reaches back into the summer.** CC/FV was 35–44% for March–July signups but 13.1% (38/289) for August. Dropping only September would have let August make course completion look much worse than it is.
- **Rule adopted:** a student counts in a rate's denominator only if their starting event is at least the 95th-percentile time-to-next-stage before the snapshot. This is in `analysis/cohort_windows.py`.
- **Caveat recorded:** the 95th percentile is one choice. `PCT` in the script can be changed to test sensitivity.

## Phase 3: Finding where students stall

**Prompt 4: lesson-by-lesson drop-off**
> For the 1,447 students who watched their first video… find the highest lesson number they reached… how many students' progress stalled at each lesson number (1-21)?… is there a lesson where people consistently drop off, versus a steady leak across all 21?… median number of days between consecutive lesson completions, broken out by lesson number.

- **Claude caught my mismatch first.** I had called the 1,447 the "Jun 19 cohort." But 1,447 is the students whose first video was by Jul 18. The signed-up-by-Jun-19 group is 1,167 first-video students. Claude used the 1,447 as the main pool and showed the 1,167 alongside as a check.
- **Finding:** a cliff, not a steady leak.
  - 717 of the 842 students who didn't finish (85.2%) stopped at lessons 1–4.
  - Of the 730 students who reached lesson 5, 605 finished (82.9%).
  - The 1,167 group has the same shape.
- **Video length:** Claude noted that lessons 2–4 are the longest videos. It called this "a pattern worth testing, not proof that video length causes the drop."
- **Saved as:** `analysis/lesson_dropoff.py`, rerun from scratch to confirm it reproduced the numbers shown.

**Prompt 5: what separates students who stall from those who continue**
> Compare two groups: (A) students who stalled at lessons 1-4 (717) (B) students who reached lesson 5 or beyond (730). For each group, show: % with has_training_plan… median plan_lessons_per_week… days between signup and first_video_at… breakdown by city… any other student-level field that looks meaningfully different…

| Field | A: stopped 1–4 | B: reached 5+ | Separates the groups? |
|---|---|---|---|
| Joined group chat | 20.6% | 51.4% | Yes, strongest |
| Has training plan | 55.5% | 72.9% | Yes |
| City, age, language, signup month | about the same | about the same | No |
| At least 1 coach call | 58.3% | 100% | Looks like a gate, not an effect |

Claude flagged that group chat and training plan are choices students make, so the gaps show a connection, not a cause.

**Prompt 6: is the coach-call result a hidden gate?**
> For students who had at least one coach call: what's the median lesson number they had reached before their first coach call happened, versus after? Is there any evidence in the data (a lesson gate, a required field, a lessons.csv note) that a coach call is required to unlock a specific lesson?…

- **Claude said the first question can't be answered.** There are no call dates, only a count.
- **No documented rule:** Claude searched `data/`, the README and the dictionary. The only unlock rule is "lessons unlock in order."
- **Pattern:** 0 of 1,423 students with no calls got past lesson 4.
- **Logged:** Open Question 1 for Emerge, not presented as a finding.

**Prompt 7: training plan × group chat (2×2)**
> Build a 2x2 breakdown: has_training_plan (yes/no) x joined_group_chat (yes/no)… within each of the 4 combinations, show what % reached lesson 5+ vs stopped at lessons 1-4.

| Plan | Chat | Students | Reached lesson 5 |
|---|---|---|---|
| yes | yes | 330 | 76.7% (253) |
| no | yes | 193 | 63.2% (122) |
| **yes** | **no** | **600** | **46.5% (279)** |
| no | no | 324 | 23.5% (76) |

Plan-yes / chat-no is the largest segment, with 41.5% of the 1,447 students. It became the plan's target.

**Prompt 8: can the data establish the order of events?**
> Is there a join date for the group chat anywhere in the data? If not, add this as a second open question in DATA_NOTES.md alongside the coach-call one: we can't tell whether chat membership happens before or after a student starts succeeding.

- **No join date exists.** If students join the chat after they start progressing, part of the 30.2-point gap runs the other way.
- **Plans can be checked:** 928 of 930 plans were made before the student completed lesson 2. So the plan names training plans as the better-evidenced lever, even though the chat gap is bigger.
- **Logged:** Open Question 2 for Emerge.

## Phase 4: The community plan

**Prompt 9: draft COMMUNITY_PLAN.md** (full brief, shortened)
> Draft COMMUNITY_PLAN.md based on everything we've established… WHO IT TARGETS: plan-yes / chat-no segment (600 students)… WHAT IT IS: a proactive outreach nudge getting plan-holders into the group chat within their first week… HOW WE'D MEASURE IT: A/B pilot… primary metric: % reaching lesson 5 within [a window picked from the pace data]… intent-to-treat… note the sample size honestly… Keep it grounded only in what analysis/ actually shows… Flag anywhere you're extrapolating or making a judgment call.

I asked for honest sample sizing and for every judgment call to be flagged. Claude pushed back on parts of my brief:
- **The pilot I specified is underpowered.**
  - About 120 new segment students join per month. Over 3 months that can only detect a lift of about 15 points in reaching lesson 5.
  - Realistic effects are smaller: the observed 30.2-point gap is correlational and likely overstates what outreach could cause.
  - Claude recommended widening randomization to all no-chat first-video students (185+ a month, about 11.7 points).
  - It also recommended using the chat-join rate as an early go/no-go check.
  - Built in `analysis/pilot_sizing.py`.
- **My "99.8% of plans predate lesson 2" was loose.** It was tightened to "928 of 930 plans were made before the student *completed* lesson 2." The stricter reading would have been wrong for the 216 students who made a plan after finishing lesson 1.
- **The 21-day window comes from the data.** 94.9% of students who ever reached lesson 5 did so within 21 days of their first video.
- **Labels:** every piece of reasoning not backed by a script is marked **Judgment call** in the plan.

## Phase 5: Independent review

**Prompt 10: fresh-session review from raw data**
> Review my last chat's community plan and validate the analysis

- **Numbers:** all four scripts reran with the same outputs. Claude wrote a separate script that reads only the raw `data/` files and skips my cleaned file and scripts. It matched every number it checked.
- **Formula:** the minimum-detectable-lift formula was confirmed as the standard two-proportion one.
- **Framing problems found in my plan:**

| Issue | Why it matters |
|---|---|
| The segment uses chat status at the snapshot, but the pilot would enroll by status at first video. | The 44.5% historical baseline is likely too low for a real control group. |
| The recommended wider pilot includes students with no training plan. | They have no study days or times, but send timing depends on them. |
| "Text within 1–2 days of first video" conflicts with "text only on a study day." | The rules conflict for 205 of 838 segment students (24.5%). |
| "The 30.2-point gap is an upper bound" was stated as fact. | It's an assumption and should be labelled a judgment call. |
| "City doesn't separate students" only holds up to lesson 5. | Permit pass rate differs by city: Sacramento 52.7% (69/131), NYC 41.1% (132/321), Boston 31.4% (11/35), p ≈ 0.03. |
| One sentence mixed two populations (1,423 of all students; 717 of the first-video pool). | Every rate needs a named denominator. |

## Phase 6: Dashboard

**Prompt 11: build the operating dashboard**
> Can you create a dashboard based on the community plan to show the metrics and insights from the analysis and track them over time. Presented as an HTML document.

- **QA before building:** Claude did a dry run with a stub page first. It confirmed the headline numbers matched the plan (44.5%, 41.8%, 85.2%, 63 eligible, the detectable-lift table) before designing anything.
- **Chart colors:** checked with a palette validator. One failing color was replaced.
- **Layout:** Claude looked at the rendered page, found charts overflowing their panels, and fixed them.
- **Maturity:** a student counts in the monthly lesson-5 metric only after their 21-day window has closed. Months that are too new show as partial.
- **Small samples:** the March Permit / Course Complete point rests on 4 completions (2/4). It's shown with a wide interval instead of being hidden.
- **No invented results:** the pilot panel shows "Pilot not started / Waiting on outreach log," not placeholder numbers.
- **Over time:** each run adds one row to `Dashboard/snapshot_history.csv`.
- **Definitions:** the new ones are recorded in `DATA_NOTES.md`.

---

## Phase 7: Audit, single source of truth, and making the test explicit (2026-09-25)

I ran a second Claude session on the dashboard at the same time as this one. That created problems of its own, which this phase caught.

**Prompt 12: check the tool's own output**
> Check my last prompt output for signs of deterioration or inconsistencies due to using the same claude thread for too long

- Claude reran the dashboard script and confirmed it rebuilt the page byte-for-byte. Queue totals added up (60 contactable + 3 withdrawn = 63).
- It found new judgment calls that lived only in code: the 4-day "quiet" flag, the touch windows, dropping withdrawn students. They're now logged in `DATA_NOTES.md`.

**Prompt 13: look for damage from the parallel session**
> search for any redundancies based on my last session running at the same time and editing the dashboard while this session edited the dashboard

- Claude found `DATA_NOTES.md` had been overwritten with an older version three minutes after its last edit. The Dashboard section, the group-chat open question, and the committed coach-call work were gone.
- It didn't restore anything until I confirmed which edit was mine (the note about emailing Gabe). Then it restored the file from the last commit and re-applied both changes.

**Prompt 14: verify a claim instead of trusting it**
> … confirm it only reads from analysis/ outputs, not from data/ directly.

- Claude said no: it also read 4 raw files from `data/`.

**Prompt 15: stress-test the proposed fix against a failure scenario**
> by doing the second option do I avoid the following scenario? [pasted: the dashboard should be a presentation layer; two scripts deciding "who counts as a stopper" will eventually disagree]

- Claude said the option on offer (cleaned copies of the raw files) wouldn't fix it. The real risk was that the cutoffs, pool, segment and stopper rules were typed out separately in 6 scripts.
- It checked that none disagreed yet (44.5% = 267/600, 63 eligible, same detectable lifts) and laid out two fixes: shared definitions (A) or a pure presentation layer (B).

**Prompt 16: pick the design and add a build gate**
> proceed with A and make a consistency check

- `analysis/definitions.py` now holds every shared rule. All 7 scripts import it. All 10 output files stayed byte-for-byte identical.
- Each script records its headline numbers in `analysis/key_numbers.json`. `dashboard_data.py` checks 26 of them and refuses to build if one differs or a script is stale. Tested by faking a mismatch.

**Prompt 17: hold it to the standard**
> Confirm that what you did above addresses the following: The dashboard should be a presentation layer …

- Claude said no, and listed what the dashboard script still computes itself. I chose to keep A. The limits are written down in `DATA_NOTES.md`.

**Prompt 18: make the experiment explicit**
> Compare what I have in the dashboard--make sure it clearly shows what variable it changes and how to measure whether it has success. Make sure that is addressed explicitly in the community plan file as well

- New section in the plan and on the dashboard: the one variable (chat invite, randomized), what stays the same, the metric, and a decision rule (scale / redesign / no proven effect / pause).
- Values the data can't set (smallest lift worth scaling, highest acceptable STOP rate) are marked "set before launch," not invented.

**Prompts 19–20: layout fix and a new chart, checked in a real browser**

- Claude rendered each change in headless Chrome at four widths, light and dark, instead of trusting the code. It found a label forcing sideways scrolling on phones.
- The new chart shows the share reaching lesson 5 by day since first video. The segment keeps pace with everyone else until about day 11, then falls behind: 44.5% (267/600) vs 50.3% (426/847) by day 21. The script checks that the day-21 point equals the baseline.

**Prompt 21: check against the brief**
> compare the community plan tracker and everything here with the readme.md and claude.md--make sure each prompt is addressed

- Four issues from my Phase 5 review were still open in the plan. They're fixed now: the baseline caveat, city mattering for permits (now computed in `cohort_windows.py`), the "upper bound" judgment call, and send timing for students without a plan.
- Rates missing their counts got them. Recommendations got an owner, cadence and metric.
- Draft texts went into `outbox/`: English and Spanish, with Haitian Creole marked NEEDS TRANSLATION. Each was measured under 320 characters.

---

## Where Claude pushed back on my numbers and assumptions

| My input | Claude's response | Outcome |
|---|---|---|
| Drop September signups because the month isn't finished | The issue is time to finish. August also looks artificially low (CC/FV 13.1%). | 95th-percentile cutoffs per stage |
| "1,447 students… Jun 19 cohort" | Those are two different groups: 1,447 (first video by Jul 18) vs 1,167 (signed up by Jun 19). | Used 1,447, with 1,167 as a check |
| Coach calls look like a lesson gate | No call dates exist, and no documented rule was found. | Open question, not a finding |
| "99.8% of plans predate lesson 2" | Too loose for 216 students. | "928 of 930 made before completing lesson 2" |
| Pilot on the 600-student segment only | Detects only about a 15-point lift over 3 months. | Wider pool option and an early go/no-go metric |
| Segment by chat status at the snapshot | Doesn't match enrollment at first video, so the baseline is likely low. | Flagged in the review |
| "City doesn't separate students" | False for permit pass rate (p ≈ 0.03). | Flagged in the review |
| Claude's own first audit | Its mismatch gaps came from test accounts. | Corrected in `DATA_NOTES.md` |
| "Confirm it only reads from analysis/" | No: it read 4 raw files from `data/`. | Reads documented; shared definitions added |
| Cleaned copies of raw files would prevent drift | No: the rules themselves were copied across 6 scripts. | `definitions.py` + consistency check |
| "Confirm A makes the dashboard a presentation layer" | No: listed what it still computes. | Kept A knowingly; limits written down |
| Claude's own consistency check | First run failed on its own rounding bug (30.2 read as 30). The check stopped the build, as designed. | Fixed before anything was written |
| Claude's own draft README | Said the longest text was 299 characters; measured 311. | Shortened the drafts, and the README now shows the measured length |

## Quality assurance checks

- **Reruns:** every script was rerun from scratch after each change, and outputs matched earlier results.
- **Raw-data re-derivation:** the review session rebuilt the key numbers from `data/` without using my cleaned file or scripts.
- **Test accounts:** two independent rules found the same 9 test rows.
- **Totals:** city totals were reconciled to the README (2,000 / 750 / 250).
- **Fail loudly:** the cleaning script stops on unknown city labels instead of guessing.
- **Behavior checks:** the engagement-window assumption was tested against lesson timestamps.
- **Dashboard:** numbers were dry-run against `COMMUNITY_PLAN.md` before the page was built.
- **One definition per rule:** after the refactor, every output file was compared byte-for-byte with the version before it.
- **Consistency check:** the dashboard won't build if 26 shared numbers differ from the analysis scripts. Tested with a faked mismatch.
- **Rendering:** checked in a headless browser at 360, 390, 768 and 1280 px, light and dark, with no script errors and no sideways scroll.
- **Data problems:** they are flagged, counted and kept, not silently fixed. See the "Flagged, not fixed" table in `analysis/DATA_NOTES.md`.
- **Source data:** nothing in `data/` was modified.

## Reproduce

```
pip install -r analysis/requirements.txt
python3 analysis/clean_data.py
python3 analysis/cohort_windows.py
python3 analysis/lesson_dropoff.py
python3 analysis/pilot_sizing.py
python3 analysis/coach_calls_finishers.py
python3 analysis/coach_calls_engagement.py
python3 analysis/coach_calls_segments.py
python3 analysis/dashboard_data.py
```
