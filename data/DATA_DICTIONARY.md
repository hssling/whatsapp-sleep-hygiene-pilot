# Data dictionary

All files are de-identified. Each student is identified only by a random code (`pid`, e.g. `S123`) that is
consistent across files; the key linking codes to registration numbers is held by the investigators and is
not part of this repository. Calendar dates are replaced by days relative to programme day 0
(the education session, 13 July 2026). No names, e-mail addresses, phone numbers, message text or
free-text answers are included. Examination marks are rounded to whole percent.

Missing values are empty cells.

## `cohort_baseline.csv` — whole baseline survey (N = 354)

Used for the cohort mean and SD of the PSQI (regression-to-the-mean calculations) and for the
bedtime-scoring plausibility checks.

| Column | Description |
|---|---|
| `pid` | Pseudonymous code |
| `year` | MBBS year at baseline (`2nd Year`, `3rd Year`, `Final Year`) |
| `psqi_c1` … `psqi_c7` | PSQI component scores (0–3): subjective quality, latency, duration, efficiency, disturbances, medication, daytime dysfunction |
| `psqi_global` | PSQI global score (0–21), night-anchored bedtime rule |
| `bedtime_as_entered` | Usual bedtime exactly as stored by the online form (text; AM/PM tag as entered) |
| `waketime_as_entered` | Usual wake-up time as stored by the form |
| `sleep_hours_reported` | PSQI item 4, actual hours of sleep per night |

## `third_year_baseline.csv` — third-year batch (n = 132)

| Column | Description |
|---|---|
| `pid` | Pseudonymous code |
| `invited_poor_sleeper` | 1 = baseline PSQI > 5 (invited to the programme) |
| `joined` | 1 = joined the programme (linked to programme records) |
| `psqi_global`, `ess_total`, `shi_total` | Baseline PSQI (0–21), Epworth Sleepiness Scale (0–24), Sleep Hygiene Index (0–52) |
| `stress_0_10` | Perceived stress in the last month (0–10) |
| `digital_risk_score` | Sum of six bedtime device habits (possible range 1–20) |
| `exam_percent` | Latest university examination, % (rounded) |
| `age_years`, `female`, `hostel` | Age in completed years; 1 = female; 1 = hostel resident |
| `low_mood_any` | 1 = low mood or anxiety affected sleep in the last 2 weeks |
| `eds` | 1 = ESS > 10 |

## `participants.csv` — programme participants linked to a baseline record (n = 54)

| Column | Description |
|---|---|
| `pid` | Pseudonymous code |
| `group` | `poor` = baseline PSQI > 5 (invited); `good` = baseline PSQI ≤ 5 (asked to join) |
| `age_years`, `female`, `hostel`, `exam_percent`, `stress_0_10`, `low_mood_any`, `digital_risk_score`, `shi_total` | Baseline covariates, as above |

## `questionnaire_forms.csv` — item-level PSQI and ESS responses (100 forms)

One row per submitted form: each participant's baseline form(s) and follow-up form.

| Column | Description |
|---|---|
| `pid` | Pseudonymous code |
| `form` | `baseline` or `followup` |
| `submission` | 1 = first baseline submission (used in the primary analysis); 2 = a later resubmission |
| `day` | Day of submission relative to programme day 0 |
| `hours_after_first` | For baseline resubmissions, hours after the first submission |
| `PSQI: …`, `ESS item: …` | Item responses as recorded by the online form (the column names are the form's item labels) |
| `sheet_psqi_global` | PSQI global score calculated automatically by the data-collection spreadsheet (clock times read as entered) |
| `fu_status` | Follow-up form item on programme participation: `Completed`, `Lost to follow-up`, `Withdrawn` |
| `consent_agree` | Answer to "I agree to participate in this digital form" on the follow-up form |
| `consent_items_yes` | Number of the nine consent statements answered "Yes" on the follow-up form |
| `fu_adh_fixed`, `fu_adh_screen`, `fu_adh_caffeine` | Self-reported adherence on most days: Yes / Partly / No |
| `fu_adh_overall` | Overall adherence: Good / Moderate / Poor |
| `fu_useful` | Did the guidance feel useful? Yes / Partly / No |

Follow-up forms are analysed only when `consent_agree` is "Yes" (one form is excluded on this rule).
The status item records programme participation, not consent.

## `diary.csv` — daily online diary (653 entries after removing duplicate dates)

| Column | Description |
|---|---|
| `pid` | Pseudonymous code (three codes belong to registration numbers that matched more than one student; `linked` = 0) |
| `linked` | 1 = linked to a baseline record |
| `prog_day` | Programme day of the diary date (1–28 = programme period) |
| `in_programme` | 1 = programme days 1–28 |
| `backfilled` | 1 = entry submitted one day or more after its diary date |
| `sleep_h` | Approximate hours of sleep; `sleep_h_flag` = 1 when outside 2–14 h |
| `rested` | Restedness on waking (1–5) |
| `stress_bed` | Stress or racing mind at bedtime (1–5) |
| `adh_fixed`, `adh_screen`, `adh_caffeine`, `adh_phone`, `adh_winddown` | Habit kept the night before: 1 = yes, 0.5 = partly, 0 = no |
| `adh_score` | Sum of the five habit items (0–5) |

## `reminders.csv`

Number of diary-reminder messages posted by the facilitators on each programme day (message text not included).

## `reflections.csv` — reflection survey, about seven weeks after follow-up (n = 50 analysed)

Structured items only; `pid` is filled when the respondent's optional registration number matched a
programme participant (`roster_status` = `programme`).

## `counts.json`

Counts that cannot be derived from the files above (members of the programme group, diary or follow-up
submitters, reflection-survey responses excluded before analysis).
