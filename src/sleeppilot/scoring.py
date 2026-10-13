"""PSQI and ESS scoring from item-level responses.

`score_instruments` is the scoring used for the baseline survey of this cohort and applied unchanged at
follow-up. The online form did not record reliably whether a clock time was morning or evening (for
example, 35 baseline respondents gave "11:00 AM" as their usual bedtime), so bedtimes are read as the
night before waking ("night-anchored rule"):

    clock hour 8-11 -> 20:00-23:59, 12 -> midnight, 1-5 -> 01:00-05:59, 6-7 -> 18:00-19:59;
    wake-up times are read as morning.

`score_literal` reproduces the automatic scores of the data-collection spreadsheet, which read each
clock time as entered and wrapped time in bed around midnight. It is used only for the sensitivity and
validation analyses.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

FREQ4 = {"Not during past month": 0, "Less than once a week": 1,
         "Once or twice a week": 2, "Three or more times a week": 3}
SQ = {"Very good": 0, "Fairly good": 1, "Fairly bad": 2, "Very bad": 3}
ENTH = {"No problem": 0, "Very slight problem": 1, "Somewhat a problem": 2, "Very big problem": 3}
DIST_COLS = [
    "PSQI disturbance: Wake up in the middle of the night or early morning",
    "PSQI disturbance: Have to get up to use the bathroom",
    "PSQI disturbance: Cannot breathe comfortably",
    "PSQI disturbance: Cough or snore loudly",
    "PSQI disturbance: Feel too cold",
    "PSQI disturbance: Feel too hot",
    "PSQI disturbance: Have bad dreams",
    "PSQI disturbance: Have pain",
]
BED, WAKE, DUR = "PSQI: Usual bedtime", "PSQI: Usual wake-up time", "PSQI: Actual hours of sleep per night"
LAT = "PSQI: Minutes needed to fall asleep"


def map_freq4(s):
    return s.astype(str).str.strip().map(FREQ4)


def parse_clock(val):
    """Return (hour, minute, 'AM'|'PM'|'') from '2:00:00 AM', '23:05:00' or similar text."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    m = re.match(r"\s*(\d{1,2}):(\d{2})(?::\d{2})?\s*([AP]M)?", str(val).strip(), re.I)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), (m.group(3) or "").upper()


def bedtime_minutes_since_18(val):
    """Night-anchored bedtime, in minutes after 18:00."""
    p = parse_clock(val)
    if p is None:
        return np.nan
    h, mi, _ = p
    h = h % 12
    if h in (8, 9, 10, 11):
        hod = h + 12
    elif h == 0:
        hod = 0
    elif h in (1, 2, 3, 4, 5):
        hod = h
    else:
        hod = h + 12
    return ((hod - 18) % 24) * 60 + mi


def wake_minutes_since_18(val):
    p = parse_clock(val)
    if p is None:
        return np.nan
    h, mi, _ = p
    h = h % 12
    hod = 12 if h == 0 else h
    return ((hod + 6) % 24) * 60 + mi


def literal_minutes_of_day(val):
    """Clock time read exactly as entered (AM/PM tag honoured; untagged times read as 24-hour)."""
    p = parse_clock(val)
    if p is None:
        return np.nan
    h, mi, ap = p
    if ap == "PM" and h < 12:
        h += 12
    if ap == "AM" and h == 12:
        h = 0
    return (h % 24) * 60 + mi


def latency_min_score(x):
    if pd.isna(x): return np.nan
    if x <= 15: return 0
    if x <= 30: return 1
    if x <= 60: return 2
    return 3


def comp_from_sum(x):
    if pd.isna(x): return np.nan
    if x == 0: return 0
    if x <= 2: return 1
    if x <= 4: return 2
    return 3


def dur_score(x):
    if pd.isna(x): return np.nan
    if x > 7: return 0
    if x >= 6: return 1
    if x >= 5: return 2
    return 3


def eff_score(x):
    if pd.isna(x): return np.nan
    if x >= 85: return 0
    if x >= 75: return 1
    if x >= 65: return 2
    return 3


def dist_score(x):
    if pd.isna(x): return np.nan
    if x == 0: return 0
    if x <= 9: return 1
    if x <= 18: return 2
    return 3


def score_instruments(df):
    """PSQI components, global score and ESS total (night-anchored bedtime rule)."""
    out = pd.DataFrame(index=df.index)
    c1 = df["PSQI: Overall sleep quality"].astype(str).str.strip().map(SQ)
    lat_min = pd.to_numeric(df[LAT], errors="coerce")
    lat_sum = lat_min.map(latency_min_score) + map_freq4(
        df["PSQI disturbance: Cannot get to sleep within 30 minutes"])
    c2 = lat_sum.map(comp_from_sum)
    dur = pd.to_numeric(df[DUR], errors="coerce")
    c3 = dur.map(dur_score)
    bed = df[BED].map(bedtime_minutes_since_18)
    wake = df[WAKE].map(wake_minutes_since_18)
    tib = (wake - bed) / 60.0
    tib = tib.where((tib > 0) & (tib <= 16))
    eff = 100.0 * dur / tib
    eff = eff.where(eff <= 100, 100)
    c4 = eff.map(eff_score)
    dist = sum(map_freq4(df[col]).fillna(0) for col in DIST_COLS)
    dist = dist + map_freq4(df["PSQI disturbance: Cannot get to sleep within 30 minutes"]).fillna(0)
    dist = dist + map_freq4(df["PSQI: Frequency of other reason for trouble sleeping"]).fillna(0)
    c5 = dist.map(dist_score)
    c6 = map_freq4(df["PSQI: Taken medicine to help you sleep"])
    dd_a = map_freq4(df["PSQI: Trouble staying awake while eating, social activity, or during classes"])
    dd_b = df["PSQI: Problem keeping enough enthusiasm to get things done"].astype(str).str.strip().map(ENTH)
    c7 = (dd_a + dd_b).map(comp_from_sum)
    comp = pd.DataFrame(dict(c1=c1, c2=c2, c3=c3, c4=c4, c5=c5, c6=c6, c7=c7))
    g = comp.sum(axis=1, min_count=7)
    six = comp.drop(columns="c4").notna().sum(axis=1) == 6
    prorated = comp.drop(columns="c4").sum(axis=1) * 7.0 / 6.0
    g = g.where(~(g.isna() & six), prorated.round())
    for k in range(1, 8):
        out[f"psqi_c{k}"] = comp[f"c{k}"]
    out["PSQI_global"] = g
    out["poor_sleep"] = (g > 5).astype(float).where(g.notna())
    ess_cols = [col for col in df.columns if str(col).startswith("ESS item")]
    assert len(ess_cols) == 8, ess_cols
    ess = pd.DataFrame({col: pd.to_numeric(df[col].astype(str).str.extract(r"^\s*(\d)")[0], errors="coerce")
                        for col in ess_cols})
    out["ESS_total"] = ess.sum(axis=1, min_count=8)
    out["eds"] = (out["ESS_total"] > 10).astype(float).where(out["ESS_total"].notna())
    out["psqi_efficiency_pct"] = eff
    out["time_in_bed_hours"] = tib
    out["sleep_duration_hours"] = dur
    out["sleep_latency_min"] = lat_min
    return out


def score_literal(df):
    """PSQI global score with clock times read literally and time in bed wrapped around midnight
    (reproduces the spreadsheet's automatic scoring). Other components as in score_instruments."""
    s = score_instruments(df)
    bed = df[BED].map(literal_minutes_of_day)
    wake = df[WAKE].map(literal_minutes_of_day)
    tib = ((wake - bed) % 1440) / 60.0
    dur = pd.to_numeric(df[DUR], errors="coerce")
    eff = (100 * dur / tib).clip(upper=100)
    comp = s[[f"psqi_c{k}" for k in range(1, 8)]].copy()
    comp["psqi_c4"] = eff.map(eff_score)
    return comp.sum(axis=1, min_count=7)


def timing_plausibility(bed_text, wake_text, sleep_hours, rule):
    """Share of forms with a daytime bedtime (06:00-17:59), more than 12 h in bed, and time in bed that
    is at least the reported sleep and no more than 4 h longer, under the 'night' or 'literal' rule."""
    if rule == "night":
        bed = pd.Series(bed_text).map(bedtime_minutes_since_18)
        hod = (bed / 60 + 18) % 24
        tib = (pd.Series(wake_text).map(wake_minutes_since_18) - bed) / 60
    else:
        bedm = pd.Series(bed_text).map(literal_minutes_of_day)
        hod = bedm / 60
        tib = ((pd.Series(wake_text).map(literal_minutes_of_day) - bedm) % 1440) / 60
    dur = pd.to_numeric(pd.Series(sleep_hours), errors="coerce")
    ok = bed_text.notna().values & pd.Series(wake_text).notna().values & dur.notna().values
    hod, tib, dur = hod[ok], tib[ok], dur[ok]
    tib = tib.where(tib > 0, tib + 24)
    return dict(n=int(ok.sum()), daytime_bedtime_pct=float(100 * ((hod >= 6) & (hod < 18)).mean()),
                tib_over_12h_pct=float(100 * (tib > 12).mean()),
                tib_consistent_pct=float(100 * ((tib >= dur - 0.01) & (tib <= dur + 4)).mean()))
