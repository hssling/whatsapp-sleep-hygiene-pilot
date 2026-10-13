"""Publication tables (main Tables 1-2 and Supplementary Tables) as formatted text, written to results/tables/."""
from __future__ import annotations

import pandas as pd

DASH = "—"
MINUS = "−"


def num(x, d=2):
    if x is None or pd.isna(x):
        return DASH
    return f"{x:.{d}f}".replace("-", MINUS)


def pfmt(p):
    if p is None or pd.isna(p):
        return DASH
    return "<0.001" if p < 0.001 else f"{p:.3f}"


def chg(ps, d=2):
    return f"{num(ps['mean_diff'], d)} ({num(ps['ci_low'], d)} to {num(ps['ci_high'], d)})"


def msd(ps, when, d=2):
    return f"{num(ps['mean_' + when], d)} ({num(ps['sd_' + when], d)})"


def table1(R):
    n = {r["characteristic"]: r for r in R["table1"]}["n"]
    df = pd.DataFrame([r for r in R["table1"] if r["characteristic"] != "n"])
    df.columns = ["Characteristic", f"Poor sleepers, followed up (n = {n['poor_followed']})",
                  f"Poor sleepers, not followed up (n = {n['poor_not_followed']})",
                  f"Good sleepers, followed up (n = {n['good_followed']})"]
    return df


def table2(R):
    P, comp, sec, good = R["primary"], R["components"], R["secondary"], R["good"]
    names = {1: "Subjective sleep quality", 2: "Sleep latency", 3: "Sleep duration", 4: "Habitual sleep efficiency",
             5: "Sleep disturbances", 6: "Use of sleep medication", 7: "Daytime dysfunction"}
    rows = [dict(o="PSQI global score", b=msd(P, "pre"), f=msd(P, "post"), c=chg(P), dz=num(P["dz"]),
                 p=pfmt(P["t_p"]), ph=DASH, g=chg(good["psqi"]))]
    for k in range(1, 8):
        c = comp[f"c{k}"]
        rows.append(dict(o=f"  C{k} {names[k]}", b=msd(c, "pre"), f=msd(c, "post"), c=chg(c), dz=num(c["dz"]),
                         p=pfmt(c["wilcoxon_p"]), ph=pfmt(c["p_holm"]), g=DASH))
    du, la, es = sec["duration"], sec["latency"], sec["ess"]
    rows.append(dict(o="Sleep duration, h", b=msd(du, "pre"), f=msd(du, "post"), c=chg(du), dz=num(du["dz"]),
                     p=pfmt(du["wilcoxon_p"]), ph=pfmt(du["p_holm"]), g=chg(good["duration"])))
    rows.append(dict(o="Sleep latency, min, median (IQR)",
                     b=f"{la['median_pre']:.1f} ({la['q1_pre']:.0f} to {la['q3_pre']:.0f})",
                     f=f"{la['median_post']:.1f} ({la['q1_post']:.0f} to {la['q3_post']:.0f})",
                     c=f"median {num(la['median_diff'], 1)}", dz=DASH, p=pfmt(la["wilcoxon_p"]), ph=pfmt(la["p_holm"]),
                     g=DASH))
    rows.append(dict(o="ESS total score", b=msd(es, "pre"), f=msd(es, "post"), c=chg(es), dz=num(es["dz"]),
                     p=pfmt(es["t_p"]), ph=pfmt(es["p_holm"]), g=chg(good["ess"])))
    e, ps8, g8, pp = sec["eds"], sec["exactly_8h"], good["exactly_8h"], sec["poor_sleep"]
    nn = P["n"]
    pct = lambda k, n_: f"{k} ({100 * k / n_:.0f})"
    rows.append(dict(o="EDS (ESS >10), n (%)", b=pct(e["pre_pos"], nn), f=pct(e["post_pos"], nn),
                     c=f"{e['to_negative']} resolved, {e['to_positive']} new", dz=DASH, p=pfmt(e["p"]),
                     ph=pfmt(e["p_holm"]), g=DASH))
    rows.append(dict(o="Reported exactly 8 h of sleep, n (%)", b=pct(ps8["pre_pos"], nn), f=pct(ps8["post_pos"], nn),
                     c=f"{ps8['to_positive']} new, {ps8['to_negative']} ceased", dz=DASH, p=pfmt(ps8["p"]), ph=DASH,
                     g=f"{g8['pre_pos']} to {g8['post_pos']} of {g8['n']}"))
    ex = R["expected_below_cutoff"]
    rows.append(dict(o="Poor sleep (PSQI >5), n (%)", b=pct(pp["pre_pos"], nn), f=pct(pp["post_pos"], nn),
                     c=f"{pp['to_negative']} below cut-off (expected from regression to the mean: "
                       f"{ex['0.87']:.0f} to {ex['0.0']:.0f})", dz=DASH, p=DASH, ph=DASH, g=DASH))
    df = pd.DataFrame(rows)
    df.columns = ["Outcome", "Baseline", "Follow-up", "Change (95% CI)", "dz", "P", "P (Holm)",
                  f"Good sleepers: change (95% CI), n = {good['psqi']['n']}"]
    return df


def sensitivity_rows(R):
    """(group, label, n, estimate, lo, hi, note) for the sensitivity table and Figure 3B."""
    P, sv, st_, a6, dup, mi = R["primary"], R["scoring_versions"], R["status"], R["above6"], R["duplicates"], R["missing"]
    rt = {x["rho"]: x for x in R["rtm"]}
    ab = lambda r: a6["rtm"][str(r)]
    row = lambda g, lab, ps, note="": (g, lab, ps["n"], ps["mean_diff"], ps["ci_low"], ps["ci_high"], note)
    rows = [
        row("Primary analysis", "Night-anchored scoring, complete cases", P),
        row("Scoring of bedtimes", "Clock times read as entered, both time points", sv["literal"]),
        row("Scoring of bedtimes", "Spreadsheet's automatic scores, both time points", sv["sheet"]),
        row("Scoring of bedtimes", "Mixed: night-anchored baseline, spreadsheet follow-up", sv["mixed"],
            "two different rules; not a valid comparison"),
        row("Eligibility and baseline", "Baseline PSQI >6 only (Indian validation cut-off)", a6["summary"]),
        row("Eligibility and baseline", "Later duplicate baseline used for eligibility and baseline",
            dup["later_eligibility"]),
        row("Eligibility and baseline", "Duplicate baseline submitters excluded", dup["excluding"]),
        row("Eligibility and baseline", "Without duration and efficiency components (0-15)", R["psqi_without_c3_c4"]),
        ("Missing follow-up", "Missing follow-up assumed unchanged", mi["no_change"]["n"], mi["no_change"]["est"],
         mi["no_change"]["ci_low"], mi["no_change"]["ci_high"], "single imputation; interval too narrow"),
        row("Missing follow-up", "Follow-up status recorded as completed", st_["completed"]),
        row("Missing follow-up", "Follow-up status not recorded as completed", st_["not_completed"]),
        row("Missing follow-up", "Excluding the form marked 'withdrawn'", st_["excluding_withdrawn"]),
    ]
    for r in (0.87, 0.68, 0.5, 0.0):
        x = rt[r]
        rows.append(("Regression to the mean", f"Adjusted, r = {r:g}", P["n"], x["adjusted_poor"], *x["adjusted_poor_ci"], ""))
    for r in (0.68, 0.0):
        rows.append(("Regression to the mean", f"Baseline PSQI >6 only, adjusted, r = {r:g}", a6["summary"]["n"],
                     ab(r)["adjusted"], *ab(r)["ci"], ""))
    g = R["good"]["psqi"]
    rows.append(("Reference", "Good sleepers (received the programme)", g["n"], g["mean_diff"], g["ci_low"],
                 g["ci_high"], "not a control group"))
    return rows


def supplementary(R):
    S = {}
    rt = R["rtm"]
    S["rtm"] = pd.DataFrame([{
        "r": f"{x['rho']:g}",
        "Expected change, poor sleepers": num(x["expected_poor"]),
        "Adjusted change, poor sleepers (95% CI)": f"{num(x['adjusted_poor'])} ({num(x['adjusted_poor_ci'][0])} to {num(x['adjusted_poor_ci'][1])})",
        "Expected change, truncated-normal form": num(x["barnett_expected_poor"]),
        "Expected change, good sleepers": num(x["expected_good"]),
        "Adjusted change, good sleepers (95% CI)": f"{num(x['adjusted_good'])} ({num(x['adjusted_good_ci'][0])} to {num(x['adjusted_good_ci'][1])})"}
        for x in rt])
    pl = R["scoring_plausibility"]
    sv = R["scoring_versions"]
    S["scoring"] = pd.DataFrame([
        {"Measure": "Bedtime between 06:00 and 17:59, % of forms", "Night-anchored (baseline)": num(pl["night"]["baseline"]["daytime_bedtime_pct"], 1),
         "Literal (baseline)": num(pl["literal"]["baseline"]["daytime_bedtime_pct"], 1),
         "Night-anchored (follow-up)": num(pl["night"]["followup"]["daytime_bedtime_pct"], 1),
         "Literal (follow-up)": num(pl["literal"]["followup"]["daytime_bedtime_pct"], 1)},
        {"Measure": "Time in bed more than 12 h, % of forms", "Night-anchored (baseline)": num(pl["night"]["baseline"]["tib_over_12h_pct"], 1),
         "Literal (baseline)": num(pl["literal"]["baseline"]["tib_over_12h_pct"], 1),
         "Night-anchored (follow-up)": num(pl["night"]["followup"]["tib_over_12h_pct"], 1),
         "Literal (follow-up)": num(pl["literal"]["followup"]["tib_over_12h_pct"], 1)},
        {"Measure": "Time in bed consistent with reported sleep, % of forms", "Night-anchored (baseline)": num(pl["night"]["baseline"]["tib_consistent_pct"], 1),
         "Literal (baseline)": num(pl["literal"]["baseline"]["tib_consistent_pct"], 1),
         "Night-anchored (follow-up)": num(pl["night"]["followup"]["tib_consistent_pct"], 1),
         "Literal (follow-up)": num(pl["literal"]["followup"]["tib_consistent_pct"], 1)},
        {"Measure": "Change in PSQI among poor sleepers, mean (95% CI)", "Night-anchored (baseline)": chg(sv["night"]),
         "Literal (baseline)": chg(sv["literal"]), "Night-anchored (follow-up)": "", "Literal (follow-up)": ""},
        {"Measure": "Poor sleepers below the cut-off at follow-up, n of 24", "Night-anchored (baseline)": str(sv["below_cutoff"]["night"]),
         "Literal (baseline)": str(sv["below_cutoff"]["literal"]), "Night-anchored (follow-up)": "", "Literal (follow-up)": ""},
    ])
    S["sens"] = pd.DataFrame([{"Analysis": f"{g}: {lab}", "n": str(n), "Change (95% CI)":
                               f"{num(e)} ({num(lo)} to {num(hi)})", "Note": note}
                              for g, lab, n, e, lo, hi, note in sensitivity_rows(R)])
    lab = {"b_PSQI_global": "PSQI global", "b_ESS_total": "ESS total", "shi_total": "SHI total",
           "stress_0_10": "Perceived stress (0-10)", "digital_risk_score": "Digital sleep-hygiene risk",
           "exam_percent": "Examination %", "age_years": "Age, years", "n_diary_days": "Diary days",
           "female": "Female", "hostel": "Hostel resident", "low_mood_any": "Low mood or anxiety",
           "b_eds": "Excessive daytime sleepiness", "psqi_global": "PSQI global", "ess_total": "ESS total"}
    S["attr"] = pd.DataFrame([{"Baseline variable": lab[r["variable"]], "With follow-up": num(r["first"]),
                               "Without follow-up": num(r["second"]), "Standardised difference": num(r["smd"])}
                              for r in R["attrition"]["rows"]])
    S["join"] = pd.DataFrame([{"Baseline variable": lab[r["variable"]], "Joined": num(r["first"]),
                               "Did not join": num(r["second"]), "Standardised difference": num(r["smd"])}
                              for r in R["joiners"]["rows"]])
    S["dup"] = pd.DataFrame([{"Participant": str(i), "First submission": f"{r['first']:.0f}",
                              "Later submission": f"{r['later']:.0f}", "Hours apart": f"{r['hours_apart']:.1f}",
                              "Follow-up": f"{r['followup']:.0f}"} for i, r in enumerate(R["duplicates"]["table"], 1)])
    hab = {"adh_fixed": "Fixed sleep-wake time", "adh_screen": "No bright screens for 45 min before bed",
           "adh_caffeine": "No caffeine after 18:00", "adh_phone": "Phone silent and out of reach",
           "adh_winddown": "Ten-minute wind-down"}
    ad = R["adherence_diary"]
    rows = [{"Measure": f"Diary nights habit kept: {v}, %", "Poor sleepers": f"{ad['poor']['habits'][k]['kept']:.0f}",
             "Good sleepers": f"{ad['good']['habits'][k]['kept']:.0f}"} for k, v in hab.items()]
    rows += [{"Measure": "Diary adherence score (0-5), mean of student means", "Poor sleepers": num(ad["poor"]["student_mean"], 1),
              "Good sleepers": num(ad["good"]["student_mean"], 1)},
             {"Measure": "Diary adherence score (0-5), week 1 vs week 4 nights",
              "Poor sleepers": f"{num(ad['poor']['week1'], 1)} vs {num(ad['poor']['week4'], 1)}",
              "Good sleepers": f"{num(ad['good']['week1'], 1)} vs {num(ad['good']['week4'], 1)}"},
             {"Measure": "Diary nights (students)", "Poor sleepers": f"{ad['poor']['n_nights']} ({ad['poor']['n_students']})",
              "Good sleepers": f"{ad['good']['n_nights']} ({ad['good']['n_students']})"}]
    fa = R["adherence_followup"]
    for k, v in (("fixed", "Follow-up: kept a fixed schedule on most days"), ("screen", "Follow-up: avoided screens on most days"),
                 ("caffeine", "Follow-up: avoided caffeine after 18:00 on most days")):
        rows.append({"Measure": f"{v}, yes / partly / no", "Poor sleepers":
                     f"{fa[k].get('Yes', 0)} / {fa[k].get('Partly', 0)} / {fa[k].get('No', 0)}", "Good sleepers": DASH})
    ov = fa["overall"]
    rows.append({"Measure": "Follow-up: overall adherence good / moderate / poor", "Poor sleepers":
                 f"{ov.get('Good', 0)} / {ov.get('Moderate', 0)} / {ov.get('Poor', 0)}", "Good sleepers": DASH})
    st_ = R["status"]
    rows.append({"Measure": "PSQI change, status completed vs not completed (95% CI of difference)",
                 "Poor sleepers": f"{num(st_['completed']['mean_diff'])} vs {num(st_['not_completed']['mean_diff'])} "
                                  f"({num(st_['difference']['ci_low'])} to {num(st_['difference']['ci_high'])})",
                 "Good sleepers": DASH})
    for term, lab_ in (("mean_adh_score", "PSQI change per adherence point (95% CI)"),
                       ("n_diary_days", "PSQI change per diary day (95% CI)")):
        cell = lambda g: (f"{num(R['dose'][f'{g}_{term}']['coef'], 3 if term == 'n_diary_days' else 2)} "
                          f"({num(R['dose'][f'{g}_{term}']['ci_low'], 3 if term == 'n_diary_days' else 2)} to "
                          f"{num(R['dose'][f'{g}_{term}']['ci_high'], 3 if term == 'n_diary_days' else 2)}); "
                          f"n = {R['dose'][f'{g}_{term}']['n']}")
        rows.append({"Measure": lab_, "Poor sleepers": cell("poor"), "Good sleepers": cell("good")})
    S["adherence"] = pd.DataFrame(rows)
    return S


def write_all(R, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    table1(R).to_csv(outdir / "table1_baseline.csv", index=False)
    table2(R).to_csv(outdir / "table2_outcomes.csv", index=False)
    for k, df in supplementary(R).items():
        df.to_csv(outdir / f"supplementary_{k}.csv", index=False)
