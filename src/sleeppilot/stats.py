"""Small statistical helpers used throughout the analysis."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def _f(x):
    return pd.Series(x, dtype=float).dropna()


def smd_continuous(a, b):
    a, b = _f(a), _f(b)
    pooled = np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
    return float((a.mean() - b.mean()) / pooled) if pooled > 0 else float("nan")


def smd_binary(a, b):
    p1, p0 = _f(a).mean(), _f(b).mean()
    pooled = np.sqrt((p1 * (1 - p1) + p0 * (1 - p0)) / 2)
    return float((p1 - p0) / pooled) if pooled > 0 else float("nan")


def paired_summary(pre, post):
    """Mean paired change (post minus pre) with t-based 95% CI, dz, paired t and Wilcoxon P values."""
    d = pd.DataFrame({"pre": pd.Series(pre, dtype=float).values,
                      "post": pd.Series(post, dtype=float).values}).dropna()
    diff = d["post"] - d["pre"]
    n = len(diff)
    m, s = diff.mean(), diff.std(ddof=1)
    tcrit = stats.t.ppf(0.975, n - 1)
    se = s / np.sqrt(n)
    return dict(
        n=n, mean_pre=d["pre"].mean(), sd_pre=d["pre"].std(ddof=1), mean_post=d["post"].mean(),
        sd_post=d["post"].std(ddof=1), median_pre=d["pre"].median(), median_post=d["post"].median(),
        q1_pre=d["pre"].quantile(.25), q3_pre=d["pre"].quantile(.75),
        q1_post=d["post"].quantile(.25), q3_post=d["post"].quantile(.75),
        median_diff=diff.median(), mean_diff=m, sd_diff=s, ci_low=m - tcrit * se, ci_high=m + tcrit * se,
        dz=m / s if s > 0 else float("nan"),
        t_p=float(stats.ttest_rel(d["post"], d["pre"]).pvalue) if s > 0 else float("nan"),
        wilcoxon_p=float(stats.wilcoxon(d["post"], d["pre"]).pvalue) if (diff != 0).any() else 1.0,
    )


def mean_ci(x):
    x = _f(x)
    n, m, s = len(x), x.mean(), x.std(ddof=1)
    h = stats.t.ppf(0.975, n - 1) * s / np.sqrt(n)
    return dict(n=n, mean=float(m), sd=float(s), ci_low=float(m - h), ci_high=float(m + h))


def welch_diff(a, b):
    """Difference in means a - b with a Welch 95% CI."""
    a, b = _f(a), _f(b)
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    se = np.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    d = a.mean() - b.mean()
    h = stats.t.ppf(0.975, df) * se
    return dict(diff=float(d), ci_low=float(d - h), ci_high=float(d + h), df=float(df),
                p=float(stats.ttest_ind(a, b, equal_var=False).pvalue))


def mcnemar_exact(pre, post):
    d = pd.DataFrame({"pre": pd.Series(pre, dtype=float).values,
                      "post": pd.Series(post, dtype=float).values}).dropna()
    b = int(((d["pre"] == 1) & (d["post"] == 0)).sum())
    c = int(((d["pre"] == 0) & (d["post"] == 1)).sum())
    p = float(stats.binomtest(min(b, c), b + c, 0.5).pvalue) if b + c > 0 else 1.0
    return dict(n=len(d), pre_pos=int(d["pre"].sum()), post_pos=int(d["post"].sum()),
                to_negative=b, to_positive=c, p=p)


def holm(pvals):
    p = np.asarray(pvals, float)
    m = len(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(np.argsort(p)):
        running = max(running, (m - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj.tolist()


def barnett_rtm(mu, sigma, rho, cutoff, side):
    """Expected mean change from regression to the mean alone for a group selected above (or below) a
    cut-off from a normal population (Barnett et al., Int J Epidemiol 2005)."""
    z = (cutoff - mu) / sigma
    if side == "above":
        return float(-(1 - rho) * sigma * stats.norm.pdf(z) / (1 - stats.norm.cdf(z)))
    return float((1 - rho) * sigma * stats.norm.pdf(z) / stats.norm.cdf(z))


def wilson(k, n):
    from statsmodels.stats.proportion import proportion_confint
    lo, hi = proportion_confint(k, n, method="wilson")
    return float(100 * lo), float(100 * hi)
