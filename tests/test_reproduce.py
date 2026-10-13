"""The analysis reproduces the values reported in the article."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sleeppilot import analysis  # noqa: E402


@pytest.fixture(scope="module")
def R():
    return analysis.run()[0]


def close(a, b, tol=0.005):
    return abs(a - b) <= tol


def test_flow(R):
    f = R["flow"]
    assert (f["third_year"], f["third_year_poor"], f["joined_poor"], f["joined_good"]) == (132, 44, 32, 22)
    assert (f["poor_analysed"], f["good_analysed"], f["good_excluded_consent"]) == (24, 15, 1)
    assert (f["group_members"], f["submitted_any"], f["linked"], f["unlinked"]) == (59, 57, 54, 3)


def test_primary(R):
    p = R["primary"]
    assert close(p["mean_pre"], 7.875) and close(p["mean_post"], 3.5417)
    assert close(p["mean_diff"], -4.3333) and close(p["ci_low"], -5.519, 0.01) and close(p["ci_high"], -3.148, 0.01)


def test_regression_to_the_mean(R):
    rt = {x["rho"]: x for x in R["rtm"]}
    assert close(rt[0.0]["adjusted_poor"], -1.03, 0.01)
    assert close(rt[0.5]["adjusted_poor"], -2.68, 0.01)
    assert close(rt[0.87]["adjusted_poor"], -3.90, 0.01)
    assert close(R["rtm_parameters"]["cohort_mean"], 4.576, 0.001)


def test_scoring_versions(R):
    sv = R["scoring_versions"]
    assert close(sv["literal"]["mean_diff"], -3.79, 0.01)
    assert close(sv["sheet"]["mean_diff"], -3.58, 0.01)
    assert close(sv["mixed"]["mean_diff"], -3.04, 0.01)
    assert (sv["followup_forms_differing"], sv["n_shift_minus3"]) == (12, 10)


def test_sensitivity(R):
    assert R["above6"]["summary"]["n"] == 17 and close(R["above6"]["summary"]["mean_diff"], -4.65, 0.01)
    assert close(R["duplicates"]["later_eligibility"]["mean_diff"], -3.85, 0.01)
    assert close(R["missing"]["no_change"]["est"], -3.25, 0.01)
    assert close(R["status"]["completed"]["mean_diff"], -5.05, 0.01)
    assert close(R["status"]["not_completed"]["mean_diff"], -1.60, 0.01)
    assert close(R["good"]["psqi"]["mean_diff"], -1.40, 0.01)
