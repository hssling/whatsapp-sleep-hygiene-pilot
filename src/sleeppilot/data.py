"""Load the de-identified files and assemble one row per programme participant."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .scoring import score_instruments, score_literal

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
PROGRAMME_LAST_DAY = 28          # day 0 = education session (13 July 2026); day 28 = 10 August 2026

# Ethical rule for the follow-up form: a form is analysed only if the respondent answered "Yes" to
# "I agree to participate in this digital form" on that same form. One good sleeper answered "No" and is
# excluded from every analysis. The status item ('Completed', 'Lost to follow-up', 'Withdrawn') records
# programme participation, not consent, and does not affect eligibility for analysis.
REQUIRE_FOLLOWUP_AGREEMENT = True


def load():
    rd = lambda f: pd.read_csv(DATA / f)
    return dict(cohort=rd("cohort_baseline.csv"), third=rd("third_year_baseline.csv"),
                participants=rd("participants.csv"), forms=rd("questionnaire_forms.csv"), diary=rd("diary.csv"),
                reminders=rd("reminders.csv"), reflections=rd("reflections.csv"),
                counts=json.loads((DATA / "counts.json").read_text()))


def _scored(forms, prefix):
    s = score_instruments(forms)
    s["PSQI_literal"] = score_literal(forms)
    keep = [f"psqi_c{k}" for k in range(1, 8)] + ["PSQI_global", "poor_sleep", "ESS_total", "eds",
                                                  "psqi_efficiency_pct", "time_in_bed_hours",
                                                  "sleep_duration_hours", "sleep_latency_min", "PSQI_literal"]
    out = s[keep].add_prefix(prefix)
    out[prefix + "PSQI_sheet"] = forms["sheet_psqi_global"].values
    out["pid"] = forms["pid"].values
    return out


def build_wide(d):
    f = d["forms"]
    b1 = f[(f["form"] == "baseline") & (f["submission"] == 1)].reset_index(drop=True)
    fu = f[f["form"] == "followup"].reset_index(drop=True)
    bs = _scored(b1, "b_").assign(b_day=b1["day"].values)
    fs = _scored(fu, "f_").assign(fu_day=fu["day"].values, fu_status=fu["fu_status"].values,
                                  consent_agree=fu["consent_agree"].values,
                                  fu_adh_fixed=fu["fu_adh_fixed"].values, fu_adh_screen=fu["fu_adh_screen"].values,
                                  fu_adh_caffeine=fu["fu_adh_caffeine"].values,
                                  fu_adh_overall=fu["fu_adh_overall"].values, fu_useful=fu["fu_useful"].values)
    w = d["participants"].merge(bs, on="pid", how="left").merge(fs, on="pid", how="left")
    w["fu_submitted"] = w["f_PSQI_global"].notna() | w["f_ESS_total"].notna()
    complete = w["f_PSQI_global"].notna() & w["f_ESS_total"].notna()
    agreed = (w["consent_agree"] == "Yes") if REQUIRE_FOLLOWUP_AGREEMENT else True
    w["fu_analysed"] = complete & agreed
    w["fu_excluded_consent"] = complete & ~agreed if REQUIRE_FOLLOWUP_AGREEMENT else False
    w["change"] = w["f_PSQI_global"] - w["b_PSQI_global"]
    dy = d["diary"]
    ip = dy[(dy["in_programme"] == 1) & (dy["linked"] == 1)]
    eng = ip.groupby("pid").agg(n_diary_days=("prog_day", "nunique"), mean_adh_score=("adh_score", "mean"))
    w = w.merge(eng, on="pid", how="left")
    w["n_diary_days"] = w["n_diary_days"].fillna(0).astype(int)
    return w


def later_baseline(d):
    """Scores from each participant's last baseline submission (only for those who submitted twice)."""
    f = d["forms"]
    b = f[f["form"] == "baseline"]
    multi = b.groupby("pid")["submission"].transform("max") > 1
    last = b[multi].sort_values("submission").groupby("pid").tail(1).reset_index(drop=True)
    first = b[multi & (b["submission"] == 1)].set_index("pid")
    s = score_instruments(last).assign(pid=last["pid"].values, hours_apart=last["hours_after_first"].values)
    s["first_PSQI"] = s["pid"].map(score_instruments(first.reset_index()).set_index(first.index)["PSQI_global"])
    return s
