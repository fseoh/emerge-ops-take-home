# Data Dictionary

Snapshot: **2026-09-15 06:00 ET**. All timestamps are Eastern Time, including Sacramento rows. The same content is in `README.csv`.

## Funnel definitions

| Stage | Definition |
|---|---|
| CA (create account) | Row exists in `students.csv` |
| First Video | Lesson 1 appears in `lesson_events.csv` |
| Course Complete | Lesson 21 appears in `lesson_events.csv` |
| Permit | `permit_result = passed` |

Stage conversion is step-to-step: FV / CA, CC / FV, Permit / CC.

## `students.csv`

One row per student. This is the simplified user summary table.

| Field | Type | Example / values | Definition |
|---|---|---|---|
| `user_id` | string | u_101234 | Unique student ID. One row per student. |
| `city` | string | NYC | Sacramento | Boston | Program market the student signed up for. |
| `signup_at` | datetime (ET) | 2026-04-03 19:22:10 | When the student created their account (CA). |
| `referral_source` | string | reentry_org | parole_probation_officer | friend_family | paid_social | workforce_center | How the student heard about Emerge. For analysis only. Never use in student messages. |
| `age_band` | string | 18-24 | 25-34 | 35-44 | 45-54 | 55+ | Self-reported age range at signup. |
| `preferred_language` | string | en | es | ht | Language the student asked to be contacted in. ht = Haitian Creole. |
| `primary_device` | string | phone | laptop | tablet | shared_computer | Device used for most sessions. shared_computer = library, reentry center, or similar. |
| `status` | string | not_started | in_progress | inactive | course_complete | permit_scheduled | permit_passed | permit_failed | withdrawn | Current state at snapshot. not_started = no lesson done. in_progress = 1-20 lessons and seen in the last 14 days. inactive = 1-20 lessons and not seen for 14+ days. withdrawn = student asked to leave the program. |
| `lessons_completed` | integer | 0-21 | Highest lesson completed, from the user summary table. Lessons unlock in order. |
| `first_video_at` | datetime (ET) |  | When the student completed Lesson 1. Blank = never activated. |
| `last_lesson_completed_at` | datetime (ET) |  | When the student completed their most recent lesson. |
| `course_completed_at` | datetime (ET) |  | When the student completed Lesson 21. Blank = not complete. |
| `last_seen_at` | datetime (ET) |  | Last time the student did anything in the app, including opening it while already logged in or tapping a text link. |
| `last_logged_in_at` | datetime (ET) |  | Last time the student entered credentials or a login code. Always on or before last_seen_at. A student can be seen often without logging in. |
| `engagement_7d_minutes` | integer | 0-600 | Minutes active in lessons or the app in the 7 days before the snapshot. |
| `engagement_3d_minutes` | integer | 0-600 | Minutes active in the 3 days before the snapshot. Should never exceed engagement_7d_minutes. |
| `has_training_plan` | string | yes | no | Whether the student finished the training-plan step in onboarding. All plan_* fields are blank when no. |
| `plan_created_at` | datetime (ET) |  | When the training plan was saved. |
| `plan_lessons_per_week` | integer | 3 | 5 | 7 | 10 | Pace the student picked. |
| `plan_study_days` | string | Mon|Wed|Sat | Days the student said they'd study, pipe-separated. |
| `plan_study_time` | string | morning | afternoon | evening | late_night | Time of day the student said they'd study. morning 6-11, afternoon 12-4, evening 5-9, late_night 10-11 PM. |
| `plan_hours_per_week` | decimal | 2.5 | Hours per week the student said they could commit. |
| `plan_target_permit_date` | date | 2026-05-13 | Date the student hopes to take the CLP exam. Optional in onboarding, so often blank even when a plan exists. |
| `plan_has_transport_to_dmv` | string | yes | no | unsure | Student's answer to: do you have a way to get to the DMV for your exam? |
| `joined_group_chat` | string | yes | no | Whether the student joined their city's cohort WhatsApp group. The invite is offered at signup. Joining is the student's choice. |
| `study_hall_sessions_attended` | integer | 0+ | Weekly Zoom study halls attended. Study hall is announced only in the group chat, so non-members are almost always 0. |
| `coach_calls_completed` | integer | 0+ | 1:1 calls completed with an Emerge coach. |
| `permit_exam_date` | date |  | Most recent CLP exam date, past or scheduled. Blank = never scheduled. |
| `permit_result` | string | passed | failed | (blank) | Result of the most recent CLP attempt. Blank = not taken yet (includes scheduled). |
| `permit_attempts` | integer | 0-2 | Number of CLP exam attempts taken so far. |

## `lesson_events.csv`

One row per lesson a student completed. Students with no lessons have no rows.

| Field | Type | Example / values | Definition |
|---|---|---|---|
| `user_id` | string | u_101234 | Joins to students.user_id. |
| `lesson_number` | integer | 1-21 | Lesson completed. Joins to lessons.lesson_number. |
| `completed_at` | datetime (ET) |  | When the student finished the lesson video and quiz. |
| `minutes_watched` | integer |  | Minutes of video watched for this lesson, including rewatches. |
| `quiz_score_pct` | integer | 0-100 | Score on the end-of-lesson quiz (best attempt). |

## `lessons.csv`

The 21-lesson CLP prep course.

| Field | Type | Example / values | Definition |
|---|---|---|---|
| `lesson_number` | integer | 1-21 | Position in the course. Lessons unlock in order. |
| `title` | string |  | Lesson title. |
| `module` | string | Orientation | General Knowledge | Air Brakes | Combination Vehicles | Practice Tests | Final Prep | CLP exam section the lesson prepares for. |
| `video_minutes` | integer |  | Runtime of the lesson video. |

## Known quirks

This is an export from production systems. Expect some mess: inconsistent labels, internal accounts, and summary fields that don't always match the event log. Document what you find.
