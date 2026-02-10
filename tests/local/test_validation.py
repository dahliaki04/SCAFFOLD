"""Tests for L1-02 (Schema Validation) and L1-03 (SubGroup UsageShare Check)."""

import pandas as pd
import pytest


# ===================================================================
# L1-02: Schema Validation
# ===================================================================

class TestSchemaValidation:
    """L1-02: Check required fields, data types, column names."""

    def test_part_master_valid(self, part_master_df: pd.DataFrame):
        """Valid Part Master passes schema check."""
        from local.core.validation import validate_part_master
        errors = validate_part_master(part_master_df)
        assert errors == []

    def test_part_master_missing_column(self, part_master_df: pd.DataFrame):
        """Missing required column raises error."""
        from local.core.validation import validate_part_master
        df = part_master_df.drop(columns=["Site"])
        errors = validate_part_master(df)
        assert len(errors) > 0
        assert any("Site" in e for e in errors)

    def test_part_master_empty_partnumber(self, part_master_df: pd.DataFrame):
        """Empty PartNumber values flagged."""
        from local.core.validation import validate_part_master
        df = part_master_df.copy()
        df.loc[0, "PartNumber"] = ""
        errors = validate_part_master(df)
        assert len(errors) > 0

    def test_bom_valid(self, bom_df: pd.DataFrame):
        """Valid BOM passes schema check."""
        from local.core.validation import validate_bom
        errors = validate_bom(bom_df)
        assert errors == []

    def test_bom_missing_column(self, bom_df: pd.DataFrame):
        """Missing required BOM column raises error."""
        from local.core.validation import validate_bom
        df = bom_df.drop(columns=["Qty"])
        errors = validate_bom(df)
        assert len(errors) > 0
        assert any("Qty" in e for e in errors)

    def test_bom_negative_qty(self, bom_df: pd.DataFrame):
        """Negative Qty flagged."""
        from local.core.validation import validate_bom
        df = bom_df.copy()
        df.loc[0, "Qty"] = -1
        errors = validate_bom(df)
        assert len(errors) > 0

    def test_supplier_map_valid(self, supplier_map_df: pd.DataFrame):
        """Valid Supplier Map passes schema check."""
        from local.core.validation import validate_supplier_map
        errors = validate_supplier_map(supplier_map_df)
        assert errors == []

    def test_supplier_map_missing_column(self, supplier_map_df: pd.DataFrame):
        """Missing required Supplier Map column raises error."""
        from local.core.validation import validate_supplier_map
        df = supplier_map_df.drop(columns=["LeadTime"])
        errors = validate_supplier_map(df)
        assert len(errors) > 0

    def test_supplier_map_zero_leadtime(self, supplier_map_df: pd.DataFrame):
        """Zero LeadTime flagged."""
        from local.core.validation import validate_supplier_map
        df = supplier_map_df.copy()
        df.loc[0, "LeadTime"] = 0
        errors = validate_supplier_map(df)
        assert len(errors) > 0


# ===================================================================
# L1-03: SubGroup UsageShare Check
# ===================================================================

class TestUsageShareValidation:
    """L1-03: Validate UsageShare sums to 1.0 per SubGroup."""

    def test_valid_subgroups(self, bom_df: pd.DataFrame):
        """Test data subgroups sum to 1.0."""
        from local.core.validation import validate_usage_share
        errors = validate_usage_share(bom_df)
        assert errors == []

    def test_subgroup_sum_not_one(self):
        """SubGroup shares not summing to 1.0 flagged."""
        from local.core.validation import validate_usage_share
        df = pd.DataFrame({
            "AssemblyName": ["A", "A"],
            "AssemblySite": ["S1", "S1"],
            "ComponentName": ["B", "C"],
            "ComponentSite": ["S1", "S1"],
            "Qty": [1, 1],
            "SubGroup": ["SG-BAD", "SG-BAD"],
            "UsageShare": [0.5, 0.3],  # sums to 0.8, not 1.0
        })
        errors = validate_usage_share(df)
        assert len(errors) > 0
        assert any("SG-BAD" in e for e in errors)

    def test_subgroup_with_nan_share(self):
        """SubGroup with missing UsageShare flagged."""
        from local.core.validation import validate_usage_share
        df = pd.DataFrame({
            "AssemblyName": ["A", "A"],
            "AssemblySite": ["S1", "S1"],
            "ComponentName": ["B", "C"],
            "ComponentSite": ["S1", "S1"],
            "Qty": [1, 1],
            "SubGroup": ["SG-NAN", "SG-NAN"],
            "UsageShare": [0.6, float("nan")],
        })
        errors = validate_usage_share(df)
        assert len(errors) > 0

    def test_no_subgroups_passes(self):
        """BOM with no SubGroups passes validation."""
        from local.core.validation import validate_usage_share
        df = pd.DataFrame({
            "AssemblyName": ["A"],
            "AssemblySite": ["S1"],
            "ComponentName": ["B"],
            "ComponentSite": ["S1"],
            "Qty": [1],
            "SubGroup": [float("nan")],
            "UsageShare": [float("nan")],
        })
        errors = validate_usage_share(df)
        assert errors == []

    def test_sg001_sums_correctly(self, bom_df: pd.DataFrame):
        """SG-001 in test data: 0.6 + 0.4 = 1.0."""
        sg = bom_df[bom_df["SubGroup"] == "SG-001"]
        assert abs(sg["UsageShare"].sum() - 1.0) < 1e-9

    def test_sg002_sums_correctly(self, bom_df: pd.DataFrame):
        """SG-002 in test data: 0.7 + 0.3 = 1.0."""
        sg = bom_df[bom_df["SubGroup"] == "SG-002"]
        assert abs(sg["UsageShare"].sum() - 1.0) < 1e-9
