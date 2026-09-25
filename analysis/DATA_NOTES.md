# Data Notes

Every count below comes from a script in `analysis/`. Rebuild all analysis and the dashboard with:

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

**One definition per rule.** `analysis/definitions.py` holds the snapshot time, the 95th-percentile cutoffs, the 1,447-student CC/FV pool, the target segment, "stopper" (highest lesson 1–4), the 21-day lesson-5 window, pilot eligibility and the MDE formula. Every script imports these, so changing a rule there changes it everywhere.

**Consistency check.** Each script records its headline numbers in `analysis/key_numbers.json`. `dashboard_data.py` runs last and compares 26 numbers it shares with the other scripts, including the cutoffs, pool n, segment n, the 44.5% baseline (267/600), stoppers, eligible count and the chat gap. If any differs, or a script hasn't been rerun on the current snapshot, it stops and writes nothing.

**What the dashboard script still does itself.** `dashboard_data.py` is not a pure presentation layer. It uses the shared rules above but still reads `students_clean.csv` and `data/` and computes its own numbers. Some exist only on the dashboard: the monthly series, today's outreach list, the daily charts, the 21-day window table and the profile bars. Others repeat tables in other outputs and are not in the check: stop rates by lesson, plan × chat groups, and rates by city, language and device (`lesson_dropoff.py` tables 1, 5 and 6); the segment profile and seats vs permits (`pilot_sizing.py`); and the data-handling counts (`clean_data.py`). They use the same rules, so they should match, but nothing verifies it. **Judgment call:** shared rules plus the check were enough for this take-home. The stricter design has each analysis script write JSON and the dashboard only assemble it, with no computing of its own.

It reads `data/` (read-only) and writes:

- `analysis/students_clean.csv`: 3,000 real students. Normalized `city` (raw label kept in `city_raw`), event-derived funnel columns (`ev_*`, `permit_passed`), and `flag_*` columns for each open issue below.
- `analysis/data_checks_output.txt`: the full check log. Every number here appears in it.

## What changed in the cleaned file

| Issue | Rows | Action |
|---|---|---|
| Test accounts `test_01`–`test_09`. Same 9 rows fail the `u_######` ID pattern and have `referral_source = internal` (a value not in the dictionary). | 9 | **Dropped.** They have 0 rows in `lesson_events.csv`. 5 of them claim lessons anyway (test_04 claims 21 and `course_complete`). |
| City labels vary. After strip + lowercase: `New York` → NYC (14), `nyc` → NYC (13), `NYC ` with trailing space → NYC (10), `BOS` → Boston (6). | 43 | **Normalized.** Original kept in `city_raw`. The script stops if it finds a label it can't map. |

Whitespace was checked in every column of `students.csv`, `lesson_events.csv` and `seats_by_city.csv`, both leading and trailing. The only hits are the 10 `NYC ` rows. No leading spaces anywhere.

After cleaning: NYC 2,000, Sacramento 750, Boston 250. Every city appears in `seats_by_city.csv`.

## Funnel source

All funnel stages use the event log, per CLAUDE.md:

| Stage | Column | Rule |
|---|---|---|
| First Video | `ev_first_video` | Student has a lesson 1 row in `lesson_events.csv` |
| Course Complete | `ev_course_complete` | Student has a lesson 21 row |
| Permit | `permit_passed` | `permit_result = passed` |

For First Video and Course Complete, the summary fields agree with the event log for every real student. `first_video_at` and `course_completed_at` match the event times exactly. Only `lessons_completed` disagrees, for the mid-course students in flag 1 below. No one passed the permit without a lesson 21 event.

## Flagged, not fixed

The raw values stay in the cleaned file. A `flag_*` column marks each affected row.

| # | Flag column | Rows | What's wrong | How to handle it |
|---|---|---|---|---|
| 1 | `flag_lessons_mismatch` | 14 | `lessons_completed` is 1 higher than the highest lesson in the event log. All 14 are mid-course (8 `in_progress`, 6 `inactive`). | Use `ev_max_lesson` for lesson progress. None of the 14 is at lesson 0 or 21, so FV and CC counts are unaffected. |
| 2 | `flag_lesson2_before_lesson1` | 100 | Lesson 2 has an earlier timestamp than lesson 1. This breaks "lessons unlock in order." It is always lesson 2, one row per user. | Kept. Likely a timestamp or logging bug. Don't use the lesson 1 → 2 gap as a time-to-progress measure for these users. |
| 3 | `flag_last_lesson_before_first_video` | 12 | `last_lesson_completed_at` is earlier than `first_video_at`. All 12 are inside flag 2. For them, `last_lesson_completed_at` = lesson 2's time, and lesson 2 is also their highest lesson. The summary field records the highest lesson's time, not the latest completion. | Use `ev_last_completed_at` for "last lesson" timing. |
| 4 | `flag_eng3d_gt_7d` | 11 | `engagement_3d_minutes` > `engagement_7d_minutes`. The dictionary says this should never happen: the 3-day window sits inside the 7-day window. All 11 signed up Jul 28 – Sep 8. | Exclude these 11 from any analysis of engagement minutes. We can't tell which field is wrong. |

## Other things to know (not errors)

- **`withdrawn` covers two groups.** 34 withdrew with 0 lessons and 29 with 1–20. The status hides progress, so count stages from events.
- **Target permit date is often missing.** 535 of the students with a training plan have no `plan_target_permit_date`. The dictionary calls it optional.
- **Future dates are expected.** 297 target permit dates and 44 exam dates are after the snapshot. All 44 exam dates belong to `permit_scheduled` students.
- **Checks that passed.** None of these were found:
  - timestamps after the snapshot (other than the future dates above)
  - events before signup, or events after `last_seen_at`
  - `last_logged_in_at` after `last_seen_at`
  - status breaking the 14-day active/inactive rule
  - plan fields filled when `has_training_plan = no`
  - study hall attendance without the group chat
  - gaps in the event log
  - duplicate IDs or duplicate event rows

## Open questions for Emerge

Both need answers before any analysis treats these fields as levers.

### 1. Coach calls and lesson 5

**What's missing.** `coach_calls_completed` is a count. No file records when a call happened. So we can't tell which lesson a student was on before or after a call. Nothing documents a coach-call requirement: `lessons.csv` has no prerequisite field, and the only unlock rule in the dictionary is "Lessons unlock in order."

**What the data shows** (3,000 real students, from `clean_data.py`):

| Highest lesson (events) | 0 calls | 1 call | 2 calls | 3 calls |
|---|---|---|---|---|
| 0 | 1,002 | 0 | 0 | 0 |
| 1 | 110 | 99 | 74 | 0 |
| 2 | 112 | 97 | 39 | 0 |
| 3 | 122 | 126 | 57 | 0 |
| 4 | 77 | 83 | 31 | 0 |
| 5–20 | 0 | 118 | 107 | 50 |
| 21 | 0 | 290 | 272 | 134 |

- None of the 1,002 students with no lessons had a call.
- **None of the 1,423 students with 0 calls got past lesson 4.**
- 3 calls only appear among students at lesson 5 or later.
- None of the 696 students who finished the course had 0 calls (row 21; `coach_calls_finishers.py`).

**Evidence against a hard gate at lesson 5** (from `lesson_dropoff.py`). This uses students whose first video was by Jul 18 and who stopped at lessons 1–4 (n = 717). If a call were required to unlock lesson 5, students without a call would bunch up at lesson 4. They don't. The share with a call is flat across stopping points:

| Stopped at | 0 calls | ≥1 call | % with a call |
|---|---|---|---|
| 1 | 79 | 115 | 59.3% |
| 2 | 75 | 92 | 55.1% |
| 3 | 81 | 128 | 61.2% |
| 4 | 64 | 83 | 56.5% |

418 of 717 (58.3%) had at least one call and stopped anyway: 408 `inactive`, 10 `withdrawn`.

**Calls don't track engagement before lesson 5** (from `coach_calls_engagement.py`). Same 717 students. Those with and without a call look alike:

| Signal | 0 calls (n = 299) | ≥1 call (n = 418) |
|---|---|---|
| Training plan | 54.5% (163) | 56.2% (235) |
| Group chat | 20.4% (61) | 20.8% (87) |
| Any study hall | 13.0% (39) | 14.4% (60) |
| Lesson 1 quiz, median | 79 | 78 |

If calls went to more engaged students, the ≥1 call group would look more engaged. It doesn't.

**Working assumption: a call is not required to unlock lessons.** If it were, students without a call would pile up at lesson 4. They don't: 39–45% of early stoppers have no call at every stopping lesson (the "Stopped at" table above). Before lesson 5, calls look unrelated to progress or engagement. From lesson 5 on, every student has at least one call and counts rise. So calls look like a program touchpoint that continuing students get around lesson 4–5, not a lock and not a reward for engagement. We can't rule out that calls help, or that the pattern is built into the synthetic data. Either way, "every lesson 5+ student had a call" is not evidence that calls cause progress.

**How we'd test whether calls help.** The plan doesn't rely on calls, so this comes after the chat pilot. First, use the dated call log to compare lesson pace before and after each student's first call. If Emerge confirms coaches start calls, randomize *when* the first call is offered: in week 1 after the first video for the treatment group, the usual timing for control. Measure % reaching lesson 5 within 21 days, intent-to-treat, the same metric as the chat pilot. Enroll only students not in the chat pilot, so the two tests don't mix.

**Asked Emerge:**
Emailed Gabe, CEO, the following:
1. Is a coach call required or automatically triggered at a specific lesson? Who starts it: the student or the coach?
2. Can we get the call log with dates? That would let us measure lesson progress before and after the first call.

### 2. When students join the group chat

**What's missing.** `joined_group_chat` is yes/no. No file records a join date. The dictionary says "The invite is offered at signup," which tells us when the invite goes out, not when the student joins. A student could join on day one, or after finishing several lessons. So we can't tell whether joining the chat comes before a student starts succeeding or after.

**Why it matters.** Chat membership is the field most strongly tied to getting past lesson 4. Pool: first video by Jul 18, n = 1,447 (from `lesson_dropoff.py`, table 5):

| Training plan | Group chat | n | % of pool | Reached lesson 5+ |
|---|---|---|---|---|
| yes | yes | 330 | 22.8% | 76.7% (253/330) |
| no | yes | 193 | 13.3% | 63.2% (122/193) |
| yes | no | 600 | 41.5% | 46.5% (279/600) |
| no | no | 324 | 22.4% | 23.5% (76/324) |

If students join the chat *after* progressing, some of this gap runs the other way: progress leads to joining, not joining to progress. On top of that, joining is the student's own choice (CLAUDE.md rule 7), so members may just be more motivated. Both problems would make the chat look more effective than it is.

**Compare with training plans, where timing is known.** `plan_created_at` exists. All 930 plan holders in the pool made their plan before or right after lesson 1: 712 before any lesson, 216 after lesson 1, and 2 after lesson 2. Median time from signup to plan: 0.77 hours. So the plan always comes before the lesson 1–4 stall zone. That rules out the timing problem for plans, though not the fact that students choose them.

**Related.** Study hall is announced only in the chat, so `study_hall_sessions_attended` has the same timing problem. It is also a count with no dates.

**Working assumption.** Treat chat membership as a marker of students more likely to progress, not as proof the chat causes progress. Any plan that uses the chat should test it (for example, a randomized chat-invite nudge) rather than assume the 76.7% vs 46.5% gap will carry over.

**Ask Emerge:**
1. Can we get WhatsApp group join dates per student (from the group admin log or the invite-link tracking)?
2. Is the invite sent only at signup, or again later (for example, by a coach, or after a milestone)?

## Assumptions

1. **Snapshot time is 2026-09-15 06:00 ET (a Tuesday).** All "days since" math uses this.
2. **Engagement windows are rolling and count every day, weekends included.** No column says how the windows are counted. Evidence:
   - 65 students did lessons in the last 72 hours only on Sat/Sun. All 65 have 3-day minutes > 0.
   - Of 2,687 students last seen more than 7 days ago, none has 7-day minutes > 0.
   - Of 2,786 students last seen more than 72 hours ago, 3 have 3-day minutes > 0. All 3 are in flag 4.
   - The data can't tell a rolling 72 hours apart from calendar days starting Sep 12. That only matters for activity between midnight and 06:00 on Sep 12.
3. **Test accounts are the rows that fail the `u_######` pattern or have `referral_source = internal`.** The two rules pick out the same 9 rows.
4. **Each stage rate only counts students who have had time to reach that stage.** Details below.
5. **The 44.5% segment baseline is probably low for a real control group.** The segment (600 students) uses `joined_group_chat` as of the snapshot. The pilot enrolls students by their status at first video. Students who were out of the chat at first video but joined later, perhaps after making progress, are missing from the 600. With no join dates this can't be measured. The plan judges the pilot against its own control group, not against 44.5%.
6. **City matters after the course, not before it.** Reaching lesson 5 doesn't differ by city (p ≈ 0.78, `lesson_dropoff_output.txt`). Permit / Course Complete does: Sacramento 51.7% (74/143), NYC 42.3% (149/352), Boston 31.6% (12/38), p ≈ 0.04, for students who completed by Aug 6 (`cohort_windows_output.txt`). The mature cohort (signed up by Jun 19) shows the same pattern, p ≈ 0.03. Pass/fail doesn't separate "failed" from "no exam on record," so this may be about who takes the exam, not who passes.

## Signup-window cutoffs

Source: `analysis/cohort_windows.py` (run after `clean_data.py`), output in `analysis/cohort_windows_output.txt`.

**The problem.** A student who signed up recently and hasn't finished isn't a drop-off yet. Counting them as one makes later stages look worse. The problem isn't that September is a short month. It reaches back into the summer. With no cutoff, CC/FV is 35.3–44.3% for Mar–Jul signups, then 13.1% (38/289) for August. That's time-to-finish, not a real collapse.

**How long each stage takes.** Whole days, among students who reached the later stage:

| Step | n | Median | 95% done within |
|---|---|---|---|
| Signup → First Video | 1,998 | 0 | 9 |
| First Video → Course Complete | 696 | 34 | 59 |
| Course Complete → Exam taken | 326 | 18 | 40 |
| Signup → Permit passed | 274 | 57 | 88 |

**Rule.** For each rate, the denominator only includes students whose starting event is at least the 95% window before the snapshot (2026-09-15 06:00):

| Rate | Included | Excluded as too new | Rate |
|---|---|---|---|
| FV / CA | Signed up by 2026-09-06 | 84 signups | 66.8% (1,947/2,916) |
| CC / FV | First video by 2026-07-18 | 551 first videos | 41.8% (605/1,447) |
| Permit / CC | Course complete by 2026-08-06 | 163 completions | 44.1% (235/533) |
| Permit / CA | Signed up by 2026-06-19 | 1,273 signups | 12.3% (212/1,727) |

All 3 cities are combined, test accounts excluded. Withdrawn students stay in: withdrawing is a drop-off.

**Mature cohort** (signed up by 2026-06-19; every stage has had time):

| CA | FV | CC | Permit | FV/CA | CC/FV | Permit/CC |
|---|---|---|---|---|---|---|
| 1,727 | 1,167 | 487 | 212 | 67.6% | 41.7% | 43.5% |

Students lost at each step: 560 before First Video, **680 between First Video and Course Complete**, 275 between Course Complete and Permit.

**Caveats.**
- The windows are measured only on students who finished each step. The oldest signups have had about 6.5 months, so very slow finishers are underrepresented. Treat the windows as a floor.
- `permit_exam_date` is the most recent attempt. For the 47 students with 2 attempts, "Course Complete → Exam" measures to the second exam. This makes the window longer, which is the safe direction.
- July's lower rates (CC/FV 35.3%, Permit/CC 31.0%, no cutoff) may be partly timing. With these cutoffs July counts only in part, so it doesn't drive any conclusion.
- The cutoffs are one choice (95th percentile). A 90th percentile window would add more recent students at the cost of more that are still unfinished. Rerun with a different `PCT` in the script to test sensitivity.

## Dashboard (`Dashboard/index.html`)

Built by `analysis/dashboard_data.py` from `students_clean.csv` and `data/`. It uses the same cutoffs as the other scripts. It adds these definitions:

- **Monthly lesson-5 metric.** Students are grouped by first-video month. A student counts only after their 21-day window has closed (first video on or before snapshot minus 21 days, 2026-08-25). August is partial: 97 of 120 segment students count. September has none yet.
- **Monthly funnel rates.** FV/CA by signup month, CC/FV by first-video month, Permit/CC by course-completion month. Each uses the same 95th-percentile cutoff as `cohort_windows.py`. A month is marked partial when some of its students are past the cutoff.
- **Small months.** March has only 4 course completions, so its Permit/CC point (50.0%, 2/4) is not meaningful. The chart shows it with a wide interval.
- **Intervals.** Whiskers are 95% Wilson score intervals, computed in the page from each month's numerator and denominator. They show sampling noise only.
- **Group chat share by month** (in `dashboard_data.json`, not charted) uses the current `joined_group_chat` flag. There is no join date, so it can't show when students joined.
- **Snapshot history.** `Dashboard/snapshot_history.csv` gets one row per export, keyed by `SNAPSHOT`. Update `SNAPSHOT` in the scripts when a new export arrives. Rerunning on the same export replaces that row.
- **Pilot readout** shows no treatment or control numbers. No outreach log exists yet.

### Today's outreach list

The "Who to reach today" section turns the outreach rules in `COMMUNITY_PLAN.md` into a daily list. These are the choices it makes. All counts are as of the 2026-09-15 06:00 snapshot.

| Choice | What the script does | Why | Rows affected |
|---|---|---|---|
| Who is eligible | Target segment (first video, training plan, not in the chat), highest lesson 1–4, first video in the last 21 days | Same definition as the pilot | 63 students |
| Withdrawn students | Listed as "Do not contact", left out of every count of contactable students | **Judgment call.** A student who withdrew shouldn't get a re-engagement text. | 3 of 63. The other 60 are 56 `in_progress` and 4 `inactive`. |
| Day count | Full days since first video, rounded down. Day 0 = first video less than 24 hours ago. | Needed to apply the touch windows | – |
| First touch window | Days 0–2 | **Judgment call.** The plan says "within 1–2 days". Day 0 is included so a student isn't skipped before day 1. | 6 due (1 on day 0) |
| Second touch window | Days 4–5, only if still not in the chat | The plan says "about day 4–5". Everyone on the list is not in the chat, per the current `joined_group_chat` flag. | 5 due |
| Quiet flag | No lesson completed in 4+ days (from `lesson_events.csv`) | **Judgment call.** About 2× the 1.95-day median gap from lesson 1 to lesson 2. It flags students for review. It doesn't trigger an extra touch. | 33 of 60 contactable |
| Active in the last 3 days | `engagement_3d_minutes` > 0 | Field definition in `DATA_DICTIONARY.md` | 32 of 60 contactable |
| Send day | First `plan_study_days` day on or after the snapshot date, in the `plan_study_time` window | CLAUDE.md: time messages to the student's plan | 7 of the 11 due students have a study day today |
| Touch window vs study day | Flagged "study day after window". The student stays on the list. | **Open question.** The plan doesn't say which rule wins. The community lead decides. | 3 students: 2 due a first touch, 1 due a second touch |

**Students inside their 21-day window** (the table under "Day to day") counts everyone with a first video in the last 21 days, segment or not, and leaves out withdrawn students: 4 of 175. That leaves 73 in the segment (60 at lessons 1–4 plus 13 at lesson 5+) and 98 others.

**Daily charts** cover the 60 full days before the snapshot date. The snapshot day is left out because it runs only to 06:00.

**Student profile bars** ("By student profile") use the same pool as plan × chat: first video by 2026-07-18, n = 1,447. Study time uses plan holders only. Groups under 100 students are marked "small group".
