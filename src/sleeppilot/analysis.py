"""All analyses reported in the article. `run()` returns one nested dictionary written to results/results.json.

Primary population: third-year baseline poor sleepers (PSQI > 5) who joined and returned a complete
follow-up questionnaire. Good sleepers who asked to join received the same programme and are described
separately; they are not a control group.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

from . import stats as st
from .data import PROGRAMME_LAST_DAY, build_wide, later_baseline, load
from .scoring import score_instruments, timing_plausibility

CUTOFF = 5.5                                    # PSQI > 5 on an integer scale
RHO_GRID = [0.0, 0.2, 0.4, 0.5, 0.6, 0.68, 0.7, 0.8, 0.87, 0.9]
# external anchors for the test-retest correlation of the PSQI
RHO_SHORT, RHO_YEAR = 0.87, 0.68                # Backhaus 2002 (days to weeks); Knutson 2006 (one year)
HABITS = {"adh_fixed": "Fixed sleep-wake time", "adh_screen": "No bright screens 45 min before bed",
          "adh_caffeine": "No caffeine after 18:00", "adh_phone": "Phone silent and out of reach",
          "adh_winddown": "Ten-minute wind-down"}


def _ci_shift(ps, shift):
    return [ps["ci_low"] - shift, ps["ci_high"] - shift]


def run():
    d = load()
    w = build_wide(d)
    R = {}
    poor_all = w[w["group"] == "poor"]
    good_all = w[w["group"] == "good"]
    poor = poor_all[poor_all["fu_analysed"]].copy()
    good = good_all[good_all["fu_analysed"]].copy()
    obs = w[w["fu_analysed"]]
    cohort, third = d["cohort"], d["third"]

    # ------------------------------------------------------------ flow and engagement
    c = d["counts"]
    R["flow"] = dict(
        cohort=len(cohort), third_year=len(third), third_year_poor=int(third["invited_poor_sleeper"].sum()),
        third_year_good=int((third["invited_poor_sleeper"] == 0).sum()),
        joined_poor=int(((third["joined"] == 1) & (third["invited_poor_sleeper"] == 1)).sum()),
        joined_good=int(((third["joined"] == 1) & (third["invited_poor_sleeper"] == 0)).sum()),
        group_members=c["group_members_attended_session"], submitted_any=c["submitted_any_diary_or_followup"],
        linked=c["linked_to_baseline"], unlinked=c["unlinked_ambiguous_ids"],
        never_submitted=c["group_members_attended_session"] - c["submitted_any_diary_or_followup"],
        followup_forms=c["followup_forms_submitted"],
        poor_followup_submitted=int(poor_all["fu_submitted"].sum()), poor_analysed=len(poor),
        good_followup_submitted=int(good_all["fu_submitted"].sum()), good_analysed=len(good),
        good_excluded_consent=int(good_all["fu_excluded_consent"].sum()))
    f = R["flow"]
    f["poor_not_joined"] = f["third_year_poor"] - f["joined_poor"]
    f["poor_lost"] = f["joined_poor"] - f["poor_analysed"]
    f["good_lost"] = f["joined_good"] - f["good_followup_submitted"]
    assert f["joined_poor"] + f["joined_good"] == f["linked"]

    R["interval_days"] = {                      # all analysed follow-up forms (poor and good sleepers)
        "baseline_to_followup": _desc(obs["fu_day"] - obs["b_day"]),
        "programme_start_to_followup": _desc(obs["fu_day"]),
        "after_programme_end": _desc(obs["fu_day"] - PROGRAMME_LAST_DAY),
        "baseline_day": _desc(obs["b_day"])}
    rem = d["reminders"]
    rem_in = rem[rem["prog_day"].between(1, PROGRAMME_LAST_DAY)]
    R["reminders"] = dict(messages=int(rem_in["diary_reminders"].sum()), days=int(len(rem_in)))
    R["diary_days"] = {g: st.mean_ci(x["n_diary_days"]) for g, x in (("poor", poor), ("good", good))}
    R["useful"] = dict(yes=int((obs["fu_useful"] == "Yes").sum()), partly=int((obs["fu_useful"] == "Partly").sum()),
                       n=int(len(obs)))
    R["homogeneity"] = dict(age_min=float(w["age_years"].min()), age_max=float(w["age_years"].max()),
                            age_mean=float(third["age_years"].mean()), age_sd=float(third["age_years"].std()),
                            third_age_min=float(third["age_years"].min()), third_age_max=float(third["age_years"].max()),
                            hostel_pct=float(100 * w["hostel"].mean()), female_pct=float(100 * w["female"].mean()))

    # ------------------------------------------------------------ primary and secondary outcomes
    P = R["primary"] = st.paired_summary(poor["b_PSQI_global"], poor["f_PSQI_global"])
    comps = {f"c{k}": st.paired_summary(poor[f"b_psqi_c{k}"], poor[f"f_psqi_c{k}"]) for k in range(1, 8)}
    for k, adj in zip(comps, st.holm([v["wilcoxon_p"] for v in comps.values()])):
        comps[k]["p_holm"] = adj
    R["components"] = comps
    sec = dict(duration=st.paired_summary(poor["b_sleep_duration_hours"], poor["f_sleep_duration_hours"]),
               latency=st.paired_summary(poor["b_sleep_latency_min"], poor["f_sleep_latency_min"]),
               ess=st.paired_summary(poor["b_ESS_total"], poor["f_ESS_total"]),
               eds=st.mcnemar_exact(poor["b_eds"], poor["f_eds"]))
    sec_p = [sec["duration"]["wilcoxon_p"], sec["latency"]["wilcoxon_p"], sec["ess"]["t_p"], sec["eds"]["p"]]
    for k, adj in zip(("duration", "latency", "ess", "eds"), st.holm(sec_p)):
        sec[k]["p_holm"] = adj
    sec["poor_sleep"] = st.mcnemar_exact(poor["b_poor_sleep"], poor["f_poor_sleep"])
    b8, f8 = (poor["b_sleep_duration_hours"] == 8).astype(float), (poor["f_sleep_duration_hours"] == 8).astype(float)
    sec["exactly_8h"] = st.mcnemar_exact(b8, f8)
    R["secondary"] = sec
    k3 = int((poor["change"] <= -3).sum())
    R["responders"] = dict(k=k3, n=len(poor), pct=100 * k3 / len(poor), ci=st.wilson(k3, len(poor)))
    R["psqi_without_c3_c4"] = st.paired_summary(poor[[f"b_psqi_c{k}" for k in (1, 2, 5, 6, 7)]].sum(axis=1),
                                                poor[[f"f_psqi_c{k}" for k in (1, 2, 5, 6, 7)]].sum(axis=1))
    lat = poor[poor["b_sleep_latency_min"] < 300]
    R["latency_detail"] = dict(max_baseline=float(poor["b_sleep_latency_min"].max()),
                               n_over_180=int((poor["b_sleep_latency_min"] > 180).sum()),
                               mean_change_excluding_max=float((lat["f_sleep_latency_min"] - lat["b_sleep_latency_min"]).mean()),
                               psqi_change_if_recoded_30=_latency_recode(d, poor))

    # good sleepers
    R["good"] = dict(psqi=st.paired_summary(good["b_PSQI_global"], good["f_PSQI_global"]),
                     ess=st.paired_summary(good["b_ESS_total"], good["f_ESS_total"]),
                     duration=st.paired_summary(good["b_sleep_duration_hours"], good["f_sleep_duration_hours"]),
                     exactly_8h=st.mcnemar_exact((good["b_sleep_duration_hours"] == 8).astype(float),
                                                 (good["f_sleep_duration_hours"] == 8).astype(float)))

    # ------------------------------------------------------------ regression to the mean
    mu, sd = float(cohort["psqi_global"].mean()), float(cohort["psqi_global"].std(ddof=1))
    mu3, sd3 = float(third["psqi_global"].mean()), float(third["psqi_global"].std(ddof=1))
    xp, xg = float(poor["b_PSQI_global"].mean()), float(good["b_PSQI_global"].mean())
    G = R["good"]["psqi"]
    rtm = []
    for r in RHO_GRID:
        ep, eg = -(1 - r) * (xp - mu), -(1 - r) * (xg - mu)
        rtm.append(dict(rho=r, expected_poor=ep, adjusted_poor=P["mean_diff"] - ep, adjusted_poor_ci=_ci_shift(P, ep),
                        expected_good=eg, adjusted_good=G["mean_diff"] - eg, adjusted_good_ci=_ci_shift(G, eg),
                        barnett_expected_poor=st.barnett_rtm(mu, sd, r, CUTOFF, "above"),
                        barnett_expected_poor_third=st.barnett_rtm(mu3, sd3, r, CUTOFF, "above")))
    R["rtm"] = rtm
    fine = np.round(np.arange(0, 0.951, 0.01), 2)
    excl = [r for r in fine if P["ci_high"] + (1 - r) * (xp - mu) < 0]
    R["rtm_parameters"] = dict(cohort_mean=mu, cohort_sd=sd, cohort_n=len(cohort), third_mean=mu3, third_sd=sd3,
                               poor_baseline_mean=xp, good_baseline_mean=xg,
                               ci_excludes_zero_from_r=float(min(excl)) if excl else None)
    R["observed_correlation"] = dict(all=float(np.corrcoef(obs["b_PSQI_global"], obs["f_PSQI_global"])[0, 1]),
                                     poor=float(np.corrcoef(poor["b_PSQI_global"], poor["f_PSQI_global"])[0, 1]),
                                     good=float(np.corrcoef(good["b_PSQI_global"], good["f_PSQI_global"])[0, 1]),
                                     n_all=int(len(obs)))
    exp_below = {}
    for r in (0.0, 0.5, RHO_YEAR, RHO_SHORT):
        if r == 0:
            exp_below[str(r)] = float(stats.norm.cdf((CUTOFF - mu) / sd) * len(poor))
        else:
            cm = mu + r * (poor["b_PSQI_global"] - mu)
            exp_below[str(r)] = float(stats.norm.cdf((CUTOFF - cm) / (sd * np.sqrt(1 - r ** 2))).sum())
    R["expected_below_cutoff"] = exp_below
    R["n_baseline_6"] = int((poor["b_PSQI_global"] == 6).sum())

    # ------------------------------------------------------------ scoring rule: validation and sensitivity
    fo = d["forms"]
    fu_forms = fo[fo["form"] == "followup"]
    R["scoring_plausibility"] = {
        rule: dict(baseline=timing_plausibility(cohort["bedtime_as_entered"], cohort["waketime_as_entered"],
                                                cohort["sleep_hours_reported"], rule),
                   followup=timing_plausibility(fu_forms["PSQI: Usual bedtime"].reset_index(drop=True),
                                                fu_forms["PSQI: Usual wake-up time"].reset_index(drop=True),
                                                fu_forms["PSQI: Actual hours of sleep per night"].reset_index(drop=True),
                                                rule))
        for rule in ("night", "literal")}
    allf = pd.concat([w[["b_PSQI_literal", "b_PSQI_sheet"]].set_axis(["lit", "sheet"], axis=1),
                      w[["f_PSQI_literal", "f_PSQI_sheet"]].set_axis(["lit", "sheet"], axis=1)]).dropna()
    R["literal_reproduces_sheet"] = dict(agree=int((allf["lit"] == allf["sheet"]).sum()), n=int(len(allf)))
    shift = poor["f_PSQI_global"] - poor["f_PSQI_sheet"]
    R["scoring_versions"] = dict(
        night=P,
        literal=st.paired_summary(poor["b_PSQI_literal"], poor["f_PSQI_literal"]),
        sheet=st.paired_summary(poor["b_PSQI_sheet"], poor["f_PSQI_sheet"]),
        mixed=st.paired_summary(poor["b_PSQI_global"], poor["f_PSQI_sheet"]),
        followup_forms_differing=int((shift != 0).sum()), n=int(len(poor)),
        mean_shift_all=float(shift.mean()), mean_shift_differing=float(shift[shift != 0].mean()),
        n_shift_minus3=int((shift == -3).sum()),
        literal_baseline_poor=int((poor["b_PSQI_literal"] > 5).sum()),
        sheet_baseline_poor=int((poor["b_PSQI_sheet"] > 5).sum()),
        below_cutoff={k: int((poor[col] <= 5).sum()) for k, col in
                      (("night", "f_PSQI_global"), ("literal", "f_PSQI_literal"), ("sheet", "f_PSQI_sheet"))})

    # ------------------------------------------------------------ eligibility and baseline sensitivity
    above6 = poor[poor["b_PSQI_global"] > 6]
    A6 = st.paired_summary(above6["b_PSQI_global"], above6["f_PSQI_global"])
    xa = float(above6["b_PSQI_global"].mean())
    R["above6"] = dict(summary=A6, rtm={str(r): dict(adjusted=A6["mean_diff"] + (1 - r) * (xa - mu),
                                                     ci=_ci_shift(A6, -(1 - r) * (xa - mu)))
                                        for r in (0.0, 0.5, RHO_YEAR, RHO_SHORT)},
                       below_cutoff=int((above6["f_PSQI_global"] <= 5).sum()),
                       below_6=int((above6["f_PSQI_global"] <= 6).sum()))
    lb = later_baseline(d).set_index("pid")
    dup_ids = [p for p in poor["pid"] if p in lb.index]
    later = poor["pid"].map(lb["PSQI_global"]).where(poor["pid"].isin(dup_ids), poor["b_PSQI_global"])
    still = poor[later > 5]
    R["duplicates"] = dict(
        n=len(dup_ids),
        table=[dict(first=float(lb.loc[p, "first_PSQI"]), later=float(lb.loc[p, "PSQI_global"]),
                    hours_apart=float(lb.loc[p, "hours_apart"]),
                    followup=float(poor.loc[poor["pid"] == p, "f_PSQI_global"].iloc[0]))
               for p in sorted(dup_ids, key=lambda p: -lb.loc[p, "first_PSQI"])],
        later_eligibility=st.paired_summary(later[later > 5], still["f_PSQI_global"]),
        n_reclassified=int((later <= 5).sum()),
        excluding=st.paired_summary(poor.loc[~poor["pid"].isin(dup_ids), "b_PSQI_global"],
                                    poor.loc[~poor["pid"].isin(dup_ids), "f_PSQI_global"]))

    # ------------------------------------------------------------ missing follow-up
    n_mis = len(poor_all) - len(poor)
    ch = poor["change"].to_numpy(float)
    R["missing"] = dict(n_missing=n_mis, n_total=len(poor_all), no_change=_mean_with_fill(ch, n_mis, 0.0))
    lo_c = None
    for cval in np.arange(0, 20.01, 0.05):
        if _mean_with_fill(ch, n_mis, cval)["ci_high"] >= 0:
            lo_c = float(round(cval, 2))
            break
    R["missing"]["tipping_change"] = lo_c

    # ------------------------------------------------------------ status, adherence and engagement
    comp_ = poor[poor["fu_status"] == "Completed"]
    notc = poor[poor["fu_status"] != "Completed"]
    R["status"] = dict(counts={k: int(v) for k, v in poor["fu_status"].value_counts().items()},
                       completed=st.paired_summary(comp_["b_PSQI_global"], comp_["f_PSQI_global"]),
                       not_completed=st.paired_summary(notc["b_PSQI_global"], notc["f_PSQI_global"]),
                       difference=st.welch_diff(comp_["change"], notc["change"]),
                       diary_days_completed=float(comp_["n_diary_days"].mean()),
                       diary_days_not_completed=float(notc["n_diary_days"].mean()),
                       excluding_withdrawn=st.paired_summary(poor.loc[poor["fu_status"] != "Withdrawn", "b_PSQI_global"],
                                                             poor.loc[poor["fu_status"] != "Withdrawn", "f_PSQI_global"]))
    dy = d["diary"]
    dy = dy[(dy["in_programme"] == 1) & (dy["linked"] == 1)]
    adh = {}
    for g, ids in (("poor", set(poor["pid"])), ("good", set(good["pid"]))):
        sub = dy[dy["pid"].isin(ids)]
        adh[g] = dict(n_students=int(sub["pid"].nunique()), n_nights=int(len(sub)),
                      student_mean=float(sub.groupby("pid")["adh_score"].mean().mean()),
                      mean_score=float(sub["adh_score"].mean()),
                      week1=float(sub.loc[sub["prog_day"] <= 7, "adh_score"].mean()),
                      week4=float(sub.loc[sub["prog_day"] >= 22, "adh_score"].mean()),
                      habits={h: dict(kept=float(100 * (sub[h] == 1).mean()), partly=float(100 * (sub[h] == 0.5).mean()))
                              for h in HABITS})
    R["adherence_diary"] = adh
    R["adherence_followup"] = {
        h: {k: int(v) for k, v in poor[f"fu_adh_{h}"].value_counts().items()} for h in ("fixed", "screen", "caffeine", "overall")}
    dose = {}
    for g, sub in (("poor", poor), ("good", good)):
        for term in ("mean_adh_score", "n_diary_days"):
            s_ = sub.dropna(subset=[term])
            fit = smf.ols(f"change ~ b_PSQI_global + {term}", data=s_).fit(cov_type="HC3")
            ci = fit.conf_int().loc[term]
            dose[f"{g}_{term}"] = dict(n=int(fit.nobs), coef=float(fit.params[term]), ci_low=float(ci.iloc[0]),
                                       ci_high=float(ci.iloc[1]), p=float(fit.pvalues[term]))
    R["dose"] = dose
    tri = {}
    dd = dy[dy["sleep_h_flag"] == 0]
    for g, ids in (("poor", set(poor["pid"])), ("good", set(good["pid"]))):
        sub = dd[dd["pid"].isin(ids)]
        tri[g] = dict(week1_mean_h=float(sub.loc[sub["prog_day"] <= 7, "sleep_h"].mean()),
                      week4_mean_h=float(sub.loc[sub["prog_day"] >= 22, "sleep_h"].mean()),
                      pct_nights_8h=float(100 * (sub["sleep_h"] == 8).mean()), n_nights=int(len(sub)))
    R["diary_sleep"] = tri

    # ------------------------------------------------------------ comparisons at baseline
    R["attrition"] = _smd_rows(poor_all[poor_all["fu_analysed"]], poor_all[~poor_all["fu_analysed"]],
                               cont=["b_PSQI_global", "b_ESS_total", "shi_total", "stress_0_10", "digital_risk_score",
                                     "exam_percent", "age_years", "n_diary_days"],
                               binv=["female", "hostel", "low_mood_any", "b_eds"])
    inv = third[third["invited_poor_sleeper"] == 1]
    R["joiners"] = _smd_rows(inv[inv["joined"] == 1], inv[inv["joined"] == 0],
                             cont=["psqi_global", "ess_total", "shi_total", "stress_0_10", "digital_risk_score",
                                   "exam_percent", "age_years"], binv=["female", "hostel", "low_mood_any"])
    R["sample_size"] = dict(sd_change=P["sd_diff"], half_width=(P["ci_high"] - P["ci_low"]) / 2, n=P["n"])
    five = cohort[[f"psqi_c{k}" for k in (1, 2, 5, 6, 7)]].sum(axis=1)
    b5 = poor[[f"b_psqi_c{k}" for k in (1, 2, 5, 6, 7)]].sum(axis=1)
    R["conservative"] = dict(adjusted_r05=R["psqi_without_c3_c4"]["mean_diff"] + 0.5 * (float(b5.mean()) - float(five.mean())),
                             cohort_mean_5=float(five.mean()))

    # ------------------------------------------------------------ reflection survey (descriptive)
    rf = d["reflections"]
    R["reflections"] = _reflections(rf, dy, c)
    R["table1"] = _table1(poor_all, poor, good)
    return R, w


# ---------------------------------------------------------------------------------------- helpers
def _desc(x):
    x = pd.Series(x, dtype=float)
    return dict(median=float(x.median()), min=float(x.min()), max=float(x.max()))


def _mean_with_fill(ch, n_missing, value):
    x = np.concatenate([ch, np.full(n_missing, value)])
    h = stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x))
    return dict(n=int(len(x)), est=float(x.mean()), ci_low=float(x.mean() - h), ci_high=float(x.mean() + h))


def _latency_recode(d, poor):
    """PSQI change if the one implausible baseline latency (300 min) had been entered as 30 min."""
    f = d["forms"]
    b1 = f[(f["form"] == "baseline") & (f["submission"] == 1) & f["pid"].isin(poor["pid"])].copy()
    lat = pd.to_numeric(b1["PSQI: Minutes needed to fall asleep"], errors="coerce")
    b1.loc[lat == 300, "PSQI: Minutes needed to fall asleep"] = 30
    s = score_instruments(b1).assign(pid=b1["pid"].values).set_index("pid")["PSQI_global"]
    return st.paired_summary(poor["pid"].map(s), poor["f_PSQI_global"])["mean_diff"]


def _smd_rows(a, b, cont, binv):
    rows = [dict(variable=v, first=float(a[v].mean()), second=float(b[v].mean()),
                 smd=st.smd_continuous(a[v], b[v])) for v in cont]
    rows += [dict(variable=v, first=float(a[v].mean()), second=float(b[v].mean()),
                  smd=st.smd_binary(a[v], b[v])) for v in binv]
    return dict(n_first=int(len(a)), n_second=int(len(b)), rows=rows)


def _reflections(rf, dy, counts):
    better = ("Much better", "Better", "A little better")
    hm = rf["hours_method"].value_counts()
    fi = rf["faculty_influence"].dropna()
    worked = "Checked my bed and wake times and worked it out"
    g = dy.assign(is8=dy["sleep_h"] == 8).groupby("pid")["is8"].mean()
    m = rf[rf["roster_status"] == "programme"].merge(g.rename("p8"), left_on="pid", right_index=True)
    habit = {h: dict(n=int(rf[f"habit_now_{h}"].notna().sum()),
                     most=int((rf[f"habit_now_{h}"] == "Still most nights").sum()))
             for h in ("fixed", "screen", "caffeine", "phone", "winddown")}
    pv = rf["phone_visibility"].value_counts()
    return dict(responses=counts["reflection_responses"], declined=counts["reflection_declined"],
                duplicates=counts["reflection_duplicates"], n=int(len(rf)),
                linked=int((rf["roster_status"] == "programme").sum()),
                entered_target=int(hm.get("Entered the 8 hours we aimed for", 0)), hours_n=int(rf["hours_method"].notna().sum()),
                worked_out_n=int((m["hours_method"] == worked).sum()),
                worked_out_pct8=float(100 * m.loc[m["hours_method"] == worked, "p8"].mean()),
                others_pct8=float(100 * m.loc[m["hours_method"] != worked, "p8"].mean()),
                faculty_agree=int((fi >= 4).sum()), faculty_n=int(len(fi)),
                now_better=int(rf["change_now"].isin(better).sum()), now_n=int(rf["change_now"].notna().sum()),
                habit_now=habit, phone_bothered=int(pv.get("Yes", 0)), phone_not=int(pv.get("No", 0)),
                phone_not_noticed=int(pv.get("I did not notice", 0)), phone_n=int(rf["phone_visibility"].notna().sum()))


def _msd(x):
    x = pd.Series(x, dtype=float).dropna()
    return f"{x.mean():.1f} ({x.std(ddof=1):.1f})"


def _npct(x):
    from decimal import ROUND_HALF_UP, Decimal
    x = pd.Series(x, dtype=float).dropna()
    p = Decimal(str(100 * x.mean())).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return f"{int(x.sum())} ({p})"


def _table1(poor_all, poor, good):
    groups = {"poor_followed": poor, "poor_not_followed": poor_all[~poor_all["fu_analysed"]], "good_followed": good}
    rows = [("n", lambda g: str(len(g))),
            ("Age, years, mean (SD)", lambda g: _msd(g["age_years"])),
            ("Female, n (%)", lambda g: _npct(g["female"])),
            ("Hostel resident, n (%)", lambda g: _npct(g["hostel"])),
            ("PSQI global, mean (SD)", lambda g: _msd(g["b_PSQI_global"])),
            ("ESS total, mean (SD)", lambda g: _msd(g["b_ESS_total"])),
            ("Excessive daytime sleepiness (ESS >10), n (%)", lambda g: _npct(g["b_eds"])),
            ("SHI total, mean (SD)", lambda g: _msd(g["shi_total"])),
            ("Perceived stress (0-10), mean (SD)", lambda g: _msd(g["stress_0_10"])),
            ("Low mood or anxiety affecting sleep, n (%)", lambda g: _npct(g["low_mood_any"])),
            ("Digital sleep-hygiene risk score, mean (SD)", lambda g: _msd(g["digital_risk_score"])),
            ("Latest university examination, %, mean (SD)", lambda g: _msd(g["exam_percent"])),
            ("Diary days completed (of 28), mean (SD)", lambda g: _msd(g["n_diary_days"]))]
    return [dict(characteristic=lab, **{k: fn(g) for k, g in groups.items()}) for lab, fn in rows]
