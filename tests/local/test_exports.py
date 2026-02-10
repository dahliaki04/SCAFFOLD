"""Tests for L1-28 (Kinaxis V7 Export) and L1-29 (Generic CSV Export)."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest


# ===================================================================
# L1-28: Kinaxis V7 Export Plugin
# ===================================================================

class TestKinaxisV7Export:
    """L1-28: CSV export in RapidResponse V7 format."""

    def test_export_creates_file(self, digraph, part_master_df, supplier_map_df, bom_df):
        """Kinaxis export creates a CSV file."""
        from local.export.kinaxis_v7 import export_kinaxis_v7
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "kinaxis.csv"
            result = export_kinaxis_v7(digraph, part_master_df, supplier_map_df, bom_df, path)
            assert result.exists()
            assert result.stat().st_size > 0

    def test_export_has_required_columns(self, digraph, part_master_df, supplier_map_df, bom_df):
        """Kinaxis CSV has V7-format columns."""
        from local.export.kinaxis_v7 import export_kinaxis_v7
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "kinaxis.csv"
            export_kinaxis_v7(digraph, part_master_df, supplier_map_df, bom_df, path)
            df = pd.read_csv(path)
            required_cols = {"Part", "Site", "ParentPart", "ParentSite",
                             "Quantity", "LeadTime", "Activity", "Supplier", "Category"}
            assert required_cols.issubset(set(df.columns))

    def test_export_contains_all_bom_edges(self, digraph, part_master_df, supplier_map_df, bom_df):
        """Kinaxis CSV has at least as many rows as BOM edges."""
        from local.export.kinaxis_v7 import export_kinaxis_v7
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "kinaxis.csv"
            export_kinaxis_v7(digraph, part_master_df, supplier_map_df, bom_df, path)
            df = pd.read_csv(path)
            # Should have BOM rows + root nodes
            assert len(df) >= len(bom_df)

    def test_export_activity_values(self, digraph, part_master_df, supplier_map_df, bom_df):
        """Activity column contains only Make/Buy/Transfer."""
        from local.export.kinaxis_v7 import export_kinaxis_v7
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "kinaxis.csv"
            export_kinaxis_v7(digraph, part_master_df, supplier_map_df, bom_df, path)
            df = pd.read_csv(path)
            valid_activities = {"Make", "Buy", "Transfer"}
            assert set(df["Activity"].unique()).issubset(valid_activities)

    def test_export_root_nodes_no_parent(self, digraph, part_master_df, supplier_map_df, bom_df):
        """Root nodes have empty ParentPart."""
        from local.export.kinaxis_v7 import export_kinaxis_v7
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "kinaxis.csv"
            export_kinaxis_v7(digraph, part_master_df, supplier_map_df, bom_df, path)
            df = pd.read_csv(path)
            roots = df[df["ParentPart"].isna() | (df["ParentPart"] == "")]
            assert len(roots) > 0  # Should have at least some root nodes


# ===================================================================
# L1-29: Generic CSV Export Plugin
# ===================================================================

class TestGenericCSVExport:
    """L1-29: Universal CSV export."""

    def test_export_creates_file(self, digraph, part_master_df, supplier_map_df, bom_df):
        """Generic CSV export creates a file."""
        from local.export.csv_export import export_generic_csv
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "export.csv"
            result = export_generic_csv(digraph, part_master_df, supplier_map_df, bom_df, path)
            assert result.exists()
            assert result.stat().st_size > 0

    def test_export_has_required_columns(self, digraph, part_master_df, supplier_map_df, bom_df):
        """Generic CSV has analysis result columns."""
        from local.export.csv_export import export_generic_csv
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "export.csv"
            export_generic_csv(digraph, part_master_df, supplier_map_df, bom_df, path)
            df = pd.read_csv(path)
            required_cols = {"PartNumber", "Site", "Activity", "MaxLeadTime",
                             "SupplierCount", "SingleSource", "Depth", "IsEndProduct", "Stage"}
            assert required_cols.issubset(set(df.columns))

    def test_export_one_row_per_node(self, digraph, part_master_df, supplier_map_df, bom_df):
        """Generic CSV has exactly one row per graph node."""
        from local.export.csv_export import export_generic_csv
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "export.csv"
            export_generic_csv(digraph, part_master_df, supplier_map_df, bom_df, path)
            df = pd.read_csv(path)
            assert len(df) == digraph.number_of_nodes()

    def test_export_activity_values(self, digraph, part_master_df, supplier_map_df, bom_df):
        """Activity column contains only Make/Buy/Transfer."""
        from local.export.csv_export import export_generic_csv
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "export.csv"
            export_generic_csv(digraph, part_master_df, supplier_map_df, bom_df, path)
            df = pd.read_csv(path)
            valid_activities = {"Make", "Buy", "Transfer"}
            assert set(df["Activity"].unique()).issubset(valid_activities)

    def test_export_end_products_flagged(self, digraph, part_master_df, supplier_map_df, bom_df):
        """End products are correctly marked in IsEndProduct column."""
        from local.export.csv_export import export_generic_csv
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "export.csv"
            export_generic_csv(digraph, part_master_df, supplier_map_df, bom_df, path)
            df = pd.read_csv(path)
            ep_count = df[df["IsEndProduct"] == True].shape[0]
            assert ep_count >= 1  # Should have at least one end product

    def test_export_single_source_detected(self, digraph, part_master_df, supplier_map_df, bom_df):
        """Parts with single suppliers are flagged."""
        from local.export.csv_export import export_generic_csv
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "export.csv"
            export_generic_csv(digraph, part_master_df, supplier_map_df, bom_df, path)
            df = pd.read_csv(path)
            # Our test data has many single-source parts
            single_src = df[df["SingleSource"] == True]
            assert len(single_src) > 0

    def test_export_suppliers_column(self, digraph, part_master_df, supplier_map_df, bom_df):
        """Suppliers column contains supplier names."""
        from local.export.csv_export import export_generic_csv
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "export.csv"
            export_generic_csv(digraph, part_master_df, supplier_map_df, bom_df, path)
            df = pd.read_csv(path)
            assert "Suppliers" in df.columns
            # At least some rows should have supplier data
            non_empty = df[df["Suppliers"].notna() & (df["Suppliers"] != "")]
            assert len(non_empty) > 0
