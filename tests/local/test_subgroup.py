"""Tests for L1-39: Auto-derive SubGroups from Priority column."""

from __future__ import annotations

import pandas as pd
import pytest

from local.core.subgroup import (
    AUTO_SUBGROUP_PREFIX,
    derive_subgroups_from_priority,
    parts_with_alternates,
)
from local.core.validation import validate_priority


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _bom_row(parent, p_site, child, c_site, qty=1, sg=None, share=None, prio=None):
    return {
        "AssemblyName": parent,
        "AssemblySite": p_site,
        "ComponentName": child,
        "ComponentSite": c_site,
        "Qty": qty,
        "SubGroup": sg,
        "UsageShare": share,
        "Priority": prio,
    }


# ---------------------------------------------------------------------------
# derive_subgroups_from_priority
# ---------------------------------------------------------------------------

class TestDerivation:
    def test_no_priority_column_passes_through_unchanged(self):
        df = pd.DataFrame([
            {"AssemblyName": "A", "AssemblySite": "S1", "ComponentName": "B",
             "ComponentSite": "S1", "Qty": 1},
        ])
        out, proposals = derive_subgroups_from_priority(df)
        assert proposals == []
        assert "Priority" not in out.columns
        assert len(out) == 1

    def test_two_priorities_under_one_parent_creates_one_subgroup(self):
        df = pd.DataFrame([
            _bom_row("A", "S1", "X", "S1", prio=1),
            _bom_row("A", "S1", "Y", "S1", prio=2),
        ])
        out, proposals = derive_subgroups_from_priority(df)
        assert len(proposals) == 1
        sg = proposals[0]
        assert sg.subgroup_name == f"{AUTO_SUBGROUP_PREFIX}A-S1"
        assert len(sg.members) == 2
        # Out has SubGroup filled, P1 -> 1.0, P2 -> 0.0 (sums to 1.0)
        assigned = out[out["SubGroup"].notna()]
        assert set(assigned["SubGroup"].unique()) == {f"{AUTO_SUBGROUP_PREFIX}A-S1"}
        assert assigned["UsageShare"].sum() == pytest.approx(1.0)

    def test_single_priority_row_is_not_a_group(self):
        df = pd.DataFrame([
            _bom_row("A", "S1", "X", "S1", prio=1),
            _bom_row("A", "S1", "Y", "S1"),  # no priority
        ])
        out, proposals = derive_subgroups_from_priority(df)
        assert proposals == []
        # Neither row should have SubGroup populated
        assert out["SubGroup"].isna().all()

    def test_manual_subgroup_takes_precedence(self):
        df = pd.DataFrame([
            _bom_row("A", "S1", "X", "S1", sg="MY-GRP", share=0.6, prio=1),
            _bom_row("A", "S1", "Y", "S1", sg="MY-GRP", share=0.4, prio=2),
        ])
        out, proposals = derive_subgroups_from_priority(df)
        # No auto proposal — manual SubGroup wins
        assert proposals == []
        assert set(out["SubGroup"].unique()) == {"MY-GRP"}
        # Original shares preserved
        assert out.loc[0, "UsageShare"] == pytest.approx(0.6)
        assert out.loc[1, "UsageShare"] == pytest.approx(0.4)

    def test_three_priorities_p1_gets_full_share(self):
        df = pd.DataFrame([
            _bom_row("A", "S1", "X", "S1", prio=1),
            _bom_row("A", "S1", "Y", "S1", prio=2),
            _bom_row("A", "S1", "Z", "S1", prio=3),
        ])
        out, proposals = derive_subgroups_from_priority(df)
        assert len(proposals) == 1
        # P1 = 1.0, P2 = 0.0, P3 = 0.0 → sums to 1.0
        assigned = out[out["SubGroup"].notna()].copy()
        assert assigned["UsageShare"].sum() == pytest.approx(1.0)
        p1_row = assigned[assigned["Priority"] == 1].iloc[0]
        assert p1_row["UsageShare"] == pytest.approx(1.0)

    def test_multiple_parents_yield_separate_groups(self):
        df = pd.DataFrame([
            _bom_row("A", "S1", "X", "S1", prio=1),
            _bom_row("A", "S1", "Y", "S1", prio=2),
            _bom_row("B", "S2", "M", "S2", prio=1),
            _bom_row("B", "S2", "N", "S2", prio=2),
        ])
        _, proposals = derive_subgroups_from_priority(df)
        assert len(proposals) == 2
        names = {p.subgroup_name for p in proposals}
        assert names == {
            f"{AUTO_SUBGROUP_PREFIX}A-S1",
            f"{AUTO_SUBGROUP_PREFIX}B-S2",
        }

    def test_idempotent(self):
        df = pd.DataFrame([
            _bom_row("A", "S1", "X", "S1", prio=1),
            _bom_row("A", "S1", "Y", "S1", prio=2),
        ])
        out1, _ = derive_subgroups_from_priority(df)
        out2, _ = derive_subgroups_from_priority(out1)
        # After first pass SubGroup is set, so second pass treats rows as
        # manual and skips them. Result is byte-identical.
        pd.testing.assert_frame_equal(out1, out2)

    def test_subgroup_satisfies_existing_l1_03_validator(self):
        from local.core.validation import validate_usage_share
        df = pd.DataFrame([
            _bom_row("A", "S1", "X", "S1", prio=1),
            _bom_row("A", "S1", "Y", "S1", prio=2),
            _bom_row("A", "S1", "Z", "S1", prio=3),
        ])
        out, _ = derive_subgroups_from_priority(df)
        # The auto-derived SubGroup must pass the sum-to-1 rule
        assert validate_usage_share(out) == []


# ---------------------------------------------------------------------------
# parts_with_alternates
# ---------------------------------------------------------------------------

class TestPartsWithAlternates:
    def test_empty_bom(self):
        df = pd.DataFrame(columns=["AssemblyName", "AssemblySite", "ComponentName",
                                   "ComponentSite", "Qty", "SubGroup", "UsageShare"])
        assert parts_with_alternates(df) == set()

    def test_no_subgroup_column(self):
        df = pd.DataFrame([{"AssemblyName": "A", "AssemblySite": "S",
                            "ComponentName": "X", "ComponentSite": "S", "Qty": 1}])
        assert parts_with_alternates(df) == set()

    def test_solo_subgroup_member_is_not_an_alternate(self):
        df = pd.DataFrame([
            _bom_row("A", "S", "X", "S", sg="G1", share=1.0),
        ])
        # A SubGroup with only one component is not really a group; no alternates
        assert parts_with_alternates(df) == set()

    def test_two_member_subgroup_returns_both(self):
        df = pd.DataFrame([
            _bom_row("A", "S", "X", "S", sg="G1", share=0.5),
            _bom_row("A", "S", "Y", "S", sg="G1", share=0.5),
        ])
        assert parts_with_alternates(df) == {"X", "Y"}


# ---------------------------------------------------------------------------
# validate_priority
# ---------------------------------------------------------------------------

class TestPriorityValidation:
    def test_no_priority_column_is_valid(self):
        df = pd.DataFrame([{"AssemblyName": "A", "AssemblySite": "S",
                            "ComponentName": "X", "ComponentSite": "S", "Qty": 1}])
        assert validate_priority(df) == []

    def test_empty_priority_column_is_valid(self):
        df = pd.DataFrame([_bom_row("A", "S", "X", "S")])
        assert validate_priority(df) == []

    def test_clean_priorities_pass(self):
        df = pd.DataFrame([
            _bom_row("A", "S", "X", "S", prio=1),
            _bom_row("A", "S", "Y", "S", prio=2),
        ])
        assert validate_priority(df) == []

    def test_duplicate_priorities_under_one_parent_flagged(self):
        df = pd.DataFrame([
            _bom_row("A", "S", "X", "S", prio=1),
            _bom_row("A", "S", "Y", "S", prio=1),  # duplicate
        ])
        errs = validate_priority(df)
        assert len(errs) == 1
        assert "A@S" in errs[0] and "duplicate" in errs[0].lower()

    def test_same_priority_under_different_parents_is_ok(self):
        df = pd.DataFrame([
            _bom_row("A", "S", "X", "S", prio=1),
            _bom_row("A", "S", "Y", "S", prio=2),
            _bom_row("B", "S", "M", "S", prio=1),  # different parent — fine
            _bom_row("B", "S", "N", "S", prio=2),
        ])
        assert validate_priority(df) == []

    def test_zero_or_negative_priority_flagged(self):
        df = pd.DataFrame([
            _bom_row("A", "S", "X", "S", prio=0),
            _bom_row("B", "S", "Y", "S", prio=-1),
        ])
        errs = validate_priority(df)
        assert len(errs) == 2
        assert all(">= 1" in e for e in errs)
