"""Tests for L1-01 (V4 Excel Reader) and L1-08 (Smart Ignore).

These tests validate data loading logic using CSV fixtures.
xlwings-specific I/O is tested on Windows CI only.
"""

import pandas as pd
import pytest


# ===================================================================
# L1-01: V4 Excel Reader — validates that data loads correctly
# ===================================================================

class TestExcelReader:
    """L1-01: Read Part Master / BOM / Supplier Map tabs."""

    def test_part_master_loads(self, part_master_df: pd.DataFrame):
        """Part Master loads with expected columns."""
        assert set(part_master_df.columns) >= {"PartNumber", "Site", "IsEndProduct"}

    def test_part_master_row_count(self, part_master_df: pd.DataFrame):
        """Part Master has 54 rows (50 unique parts, some at multiple sites)."""
        assert len(part_master_df) == 54

    def test_part_master_unique_parts(self, part_master_df: pd.DataFrame):
        """50 unique part numbers across all sites."""
        assert part_master_df["PartNumber"].nunique() == 50

    def test_part_master_sites(self, part_master_df: pd.DataFrame):
        """5 unique sites in test data."""
        sites = set(part_master_df["Site"].unique())
        assert sites == {"DC-EAST", "DC-WEST", "PLANT-A", "PLANT-B", "PLANT-C"}

    def test_part_master_end_products(self, part_master_df: pd.DataFrame):
        """3 end products flagged."""
        assert part_master_df["IsEndProduct"].sum() == 3

    def test_part_master_end_product_identities(self, end_products: set):
        """Correct end products identified."""
        assert end_products == {
            ("FG-001", "DC-EAST"),
            ("FG-002", "DC-WEST"),
            ("FG-003", "PLANT-C"),
        }

    def test_bom_loads(self, bom_df: pd.DataFrame):
        """BOM Structure loads with expected columns."""
        required = {"AssemblyName", "AssemblySite", "ComponentName", "ComponentSite", "Qty"}
        assert set(bom_df.columns) >= required

    def test_bom_row_count(self, bom_df: pd.DataFrame):
        """BOM has 51 edges."""
        assert len(bom_df) == 51

    def test_bom_has_optional_subgroup_fields(self, bom_df: pd.DataFrame):
        """SubGroup and UsageShare columns present."""
        assert "SubGroup" in bom_df.columns
        assert "UsageShare" in bom_df.columns

    def test_supplier_map_loads(self, supplier_map_df: pd.DataFrame):
        """Supplier Map loads with expected columns."""
        assert set(supplier_map_df.columns) >= {"Part", "Supplier", "LeadTime"}

    def test_supplier_map_row_count(self, supplier_map_df: pd.DataFrame):
        """Supplier Map has 35 rows (some parts have multiple suppliers)."""
        assert len(supplier_map_df) == 35

    def test_supplier_map_multi_source_parts(self, supplier_map_df: pd.DataFrame):
        """Some parts have multiple suppliers."""
        counts = supplier_map_df.groupby("Part").size()
        multi = counts[counts > 1]
        assert len(multi) >= 3  # RM-001, RM-005, RM-020

    def test_supplier_map_leadtime_positive(self, supplier_map_df: pd.DataFrame):
        """All lead times are positive integers."""
        assert (supplier_map_df["LeadTime"] > 0).all()


# ===================================================================
# L1-08: Smart Ignore — skip _SCAFFOLD_Error columns
# ===================================================================

class TestSmartIgnore:
    """L1-08: Skip _SCAFFOLD_Error columns when reading input."""

    def test_filter_scaffold_columns(self, part_master_df: pd.DataFrame):
        """Columns starting with _SCAFFOLD_ are filtered out."""
        from local.core.reader import filter_scaffold_columns

        # Simulate a DataFrame with _SCAFFOLD_Error columns injected
        df = part_master_df.copy()
        df["_SCAFFOLD_Error"] = "some error"
        df["_SCAFFOLD_Warning"] = "some warning"

        filtered = filter_scaffold_columns(df)

        assert "_SCAFFOLD_Error" not in filtered.columns
        assert "_SCAFFOLD_Warning" not in filtered.columns
        assert "PartNumber" in filtered.columns
        assert "Site" in filtered.columns

    def test_no_scaffold_columns_passthrough(self, part_master_df: pd.DataFrame):
        """Clean DataFrames pass through unchanged."""
        from local.core.reader import filter_scaffold_columns

        filtered = filter_scaffold_columns(part_master_df)
        assert list(filtered.columns) == list(part_master_df.columns)
