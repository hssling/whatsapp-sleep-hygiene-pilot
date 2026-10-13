# WhatsApp-supported sleep-hygiene programme for medical students: data and code

De-identified data and analysis code for the article

> **Sleep quality after a WhatsApp-supported sleep-hygiene programme among medical students with poor or good
> sleep: an exploratory uncontrolled pilot study.**
> Indian Journal of Sleep Medicine (manuscript under review).

The repository reproduces every number, table and figure in the article from the de-identified data, starting
from item-level questionnaire responses.

## Study in brief

Third-year MBBS students at one medical college in southern India were surveyed in May 2026. All 44 students
with a Pittsburgh Sleep Quality Index (PSQI) above 5 were invited to a four-week programme (13 July to
10 August 2026): one education session on five sleep-hygiene habits, followed by a daily online sleep diary and
reminders in a WhatsApp group. Students with better sleep who asked to join were allowed to. The PSQI and the
Epworth Sleepiness Scale (ESS) were repeated on 13-23 August 2026. There was no control group, so the
analyses describe change and examine how much of it regression to the mean, missing follow-up, scoring and
reporting could explain.

## Reproduce

Python 3.12 or later.

```bash
python -m venv .venv
.venv/Scripts/activate            # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python run_all.py                 # about 30 seconds
pytest -q                         # checks the reproduced values against the published ones
```

Outputs are written to `results/`:

| Output | Article item |
|---|---|
| `results/results.json` | every number quoted in the text |
| `results/tables/table1_baseline.csv` | Table 1 |
| `results/tables/table2_outcomes.csv` | Table 2 |
| `results/tables/supplementary_*.csv` | Supplementary tables |
| `results/figures/Figure 1-3 .tif/.jpg` | Figures 1-3 (600 dpi) |

## Layout

```
data/                    de-identified data and DATA_DICTIONARY.md
src/sleeppilot/
    scoring.py           PSQI and ESS scoring from item responses (night-anchored and literal bedtime rules)
    data.py              assembles one row per participant; consent rule for follow-up forms
    analysis.py          all analyses -> one results dictionary
    tables.py            publication tables
    figures.py           Figures 1-3 with automatic layout checks
    stats.py             paired summaries, McNemar, Holm, regression-to-the-mean helpers
run_all.py               entry point
tests/                   regression tests for the published values
```

## Key analytic decisions

* **Primary analysis**: baseline poor sleepers with a complete follow-up questionnaire (n = 24); paired change
  in the PSQI global score with a t-based 95% confidence interval.
* **Bedtime scoring**: the online form did not record reliably whether a clock time was morning or evening, so
  bedtimes are read as the night before waking (`scoring.py`). The rule was set for the baseline survey of the
  whole cohort and applied unchanged at follow-up. Results with clock times read literally, and with the
  spreadsheet's automatic scores, are reproduced for comparison.
* **Regression to the mean**: expected change = (1 - r) x (group baseline mean - cohort mean), over assumed
  test-retest correlations r from 0 to 0.9.
* **Consent**: a follow-up form is analysed only if the respondent agreed to participate on that form or later
  confirmed consent in writing (one form; `consent_confirmed_in_writing`).

## Data protection

Registration numbers were replaced by random codes; dates by programme days; examination marks were rounded;
no free text, message content, names, e-mail addresses or phone numbers are included. See `DATA_LICENSE.md`
for the terms of use, which prohibit any attempt at re-identification.

## Licence

Code: MIT (`LICENSE`). Data: CC BY 4.0 with the condition in `DATA_LICENSE.md`.

## Citation

See `CITATION.cff`.
