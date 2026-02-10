"""Tests for Sprint 2 — Local Reports.

L1-13: Single Source Detection
L1-14: Impact Analysis
L1-15: Site Dependency Map (P1)
L1-22: In-place Excel Validation
L1-23: Auto-timestamp Filenames
L1-24: Network Summary Report
L1-25: PartSource Proposal
L1-26: Proposal Readback
L1-27: PDF Audit Report (P1)
"""

from datetime import datetime

import networkx as nx
import pandas as pd
import pytest


# ===================================================================
# L1-13: Single Source Detection
# ===================================================================

class TestSingleSourceDetection:
    """L1-13: Flag parts with only one supplier."""

    def test_detects_single_source_parts(self, supplier_map_df):
        """Parts with exactly one supplier are flagged."""
        from local.core.risk import detect_single_source
        singles = detect_single_source(supplier_map_df)
        # RM-001 has 2 suppliers, RM-003 has 1
        assert "RM-003" in singles
        assert "RM-001" not in singles

    def test_multi_source_not_flagged(self, supplier_map_df):
        """Parts with multiple suppliers are not flagged."""
        from local.core.risk import detect_single_source
        singles = detect_single_source(supplier_map_df)
        assert "RM-005" not in singles  # has 2 suppliers
        assert "RM-020" not in singles  # has 2 suppliers

    def test_single_source_count(self, supplier_map_df):
        """Correct number of single-source parts identified."""
        from local.core.risk import detect_single_source
        singles = detect_single_source(supplier_map_df)
        # Count parts with exactly 1 supplier in test data
        counts = supplier_map_df.groupby("Part")["Supplier"].nunique()
        expected = set(counts[counts == 1].index)
        assert singles == expected

    def test_all_single_returns_all(self):
        """If every part has one supplier, all are flagged."""
        from local.core.risk import detect_single_source
        df = pd.DataFrame({
            "Part": ["A", "B", "C"],
            "Supplier": ["S1", "S2", "S3"],
            "LeadTime": [10, 20, 30],
        })
        assert detect_single_source(df) == {"A", "B", "C"}

    def test_none_single_returns_empty(self):
        """If every part has multiple suppliers, none flagged."""
        from local.core.risk import detect_single_source
        df = pd.DataFrame({
            "Part": ["A", "A", "B", "B"],
            "Supplier": ["S1", "S2", "S3", "S4"],
            "LeadTime": [10, 20, 30, 40],
        })
        assert detect_single_source(df) == set()


# ===================================================================
# L1-14: Impact Analysis
# ===================================================================

class TestImpactAnalysis:
    """L1-14: Supplier outage → affected product lines count."""

    def test_impact_all_suppliers_covered(self, supplier_map_df, digraph, end_products):
        """Every supplier has an impact entry."""
        from local.core.risk import analyze_supplier_impact
        impact = analyze_supplier_impact(supplier_map_df, digraph, end_products)
        expected_suppliers = set(supplier_map_df["Supplier"].unique())
        assert set(impact.keys()) == expected_suppliers

    def test_impact_has_required_fields(self, supplier_map_df, digraph, end_products):
        """Each impact entry has parts, affected_products, count."""
        from local.core.risk import analyze_supplier_impact
        impact = analyze_supplier_impact(supplier_map_df, digraph, end_products)
        for sup, data in impact.items():
            assert "parts" in data
            assert "affected_products" in data
            assert "count" in data

    def test_sup_a01_affects_fg001(self, supplier_map_df, digraph, end_products):
        """SUP-A01 supplies RM-001 and RM-002 which are in FG-001 BOM."""
        from local.core.risk import analyze_supplier_impact
        impact = analyze_supplier_impact(supplier_map_df, digraph, end_products)
        sup_a01 = impact["SUP-A01"]
        affected_parts = [p for p, s in sup_a01["affected_products"]]
        assert "FG-001" in affected_parts

    def test_sup_c01_affects_fg002_and_fg003(self, supplier_map_df, digraph, end_products):
        """SUP-C01 supplies RM-015 (FG-002 BOM) and RM-021 (FG-003 BOM)."""
        from local.core.risk import analyze_supplier_impact
        impact = analyze_supplier_impact(supplier_map_df, digraph, end_products)
        sup_c01 = impact["SUP-C01"]
        affected_parts = [p for p, s in sup_c01["affected_products"]]
        assert "FG-002" in affected_parts
        assert "FG-003" in affected_parts
        assert sup_c01["count"] == 2

    def test_impact_count_matches_list(self, supplier_map_df, digraph, end_products):
        """Count field matches length of affected_products list."""
        from local.core.risk import analyze_supplier_impact
        impact = analyze_supplier_impact(supplier_map_df, digraph, end_products)
        for sup, data in impact.items():
            assert data["count"] == len(data["affected_products"])

    def test_supplier_parts_correct(self, supplier_map_df, digraph, end_products):
        """SUP-A01 supplies RM-001 and RM-002."""
        from local.core.risk import analyze_supplier_impact
        impact = analyze_supplier_impact(supplier_map_df, digraph, end_products)
        assert sorted(impact["SUP-A01"]["parts"]) == ["RM-001", "RM-002"]


# ===================================================================
# L1-15: Site Dependency Map (P1)
# ===================================================================

class TestSiteDependencyMap:
    """L1-15: Factory relocation → which BOMs need change."""

    def test_all_sites_covered(self, digraph, end_products, part_master_df):
        """Every site with graph nodes has a dependency entry."""
        from local.core.risk import build_site_dependency_map
        site_map = build_site_dependency_map(digraph, end_products)
        graph_sites = {site for _, site in digraph.nodes()}
        assert set(site_map.keys()) == graph_sites

    def test_plant_a_affects_fg001(self, digraph, end_products):
        """PLANT-A relocation affects FG-001."""
        from local.core.risk import build_site_dependency_map
        site_map = build_site_dependency_map(digraph, end_products)
        affected_parts = [p for p, s in site_map["PLANT-A"]["affected_products"]]
        assert "FG-001" in affected_parts

    def test_plant_c_affects_fg002_and_fg003(self, digraph, end_products):
        """PLANT-C relocation affects FG-002 (via WIP-005) and FG-003."""
        from local.core.risk import build_site_dependency_map
        site_map = build_site_dependency_map(digraph, end_products)
        affected_parts = [p for p, s in site_map["PLANT-C"]["affected_products"]]
        assert "FG-003" in affected_parts
        assert "FG-002" in affected_parts

    def test_dc_east_affects_fg001_only(self, digraph, end_products):
        """DC-EAST only has FG-001, so only FG-001 affected."""
        from local.core.risk import build_site_dependency_map
        site_map = build_site_dependency_map(digraph, end_products)
        assert site_map["DC-EAST"]["count"] == 1
        affected_parts = [p for p, s in site_map["DC-EAST"]["affected_products"]]
        assert affected_parts == ["FG-001"]

    def test_site_map_has_required_fields(self, digraph, end_products):
        """Each entry has nodes, affected_products, count."""
        from local.core.risk import build_site_dependency_map
        site_map = build_site_dependency_map(digraph, end_products)
        for site, data in site_map.items():
            assert "nodes" in data
            assert "affected_products" in data
            assert "count" in data


# ===================================================================
# L1-22: In-place Excel Validation
# ===================================================================

class TestInPlaceValidation:
    """L1-22: Copy input → mark errors → add _SCAFFOLD_Error column."""

    def test_clean_data_no_errors(self, part_master_df, bom_df, supplier_map_df):
        """Clean test data produces empty _SCAFFOLD_Error columns."""
        from local.reports.reports import validate_and_annotate
        result = validate_and_annotate(part_master_df, bom_df, supplier_map_df)
        for tab_name, df in result.items():
            assert "_SCAFFOLD_Error" in df.columns
            errors = df["_SCAFFOLD_Error"].astype(str).str.strip()
            non_empty = errors[errors != ""]
            assert len(non_empty) == 0, f"{tab_name} has unexpected errors: {non_empty.tolist()}"

    def test_blank_partnumber_flagged(self, part_master_df, bom_df, supplier_map_df):
        """Blank PartNumber gets error annotation."""
        from local.reports.reports import validate_and_annotate
        pm = part_master_df.copy()
        pm.loc[0, "PartNumber"] = ""
        result = validate_and_annotate(pm, bom_df, supplier_map_df)
        pm_errors = result["Part Master"]["_SCAFFOLD_Error"]
        assert "Blank PartNumber" in pm_errors.iloc[0]

    def test_negative_qty_flagged(self, part_master_df, bom_df, supplier_map_df):
        """Negative Qty gets error annotation."""
        from local.reports.reports import validate_and_annotate
        bom = bom_df.copy()
        bom.loc[0, "Qty"] = -5
        result = validate_and_annotate(part_master_df, bom, supplier_map_df)
        bom_errors = result["BOM Structure"]["_SCAFFOLD_Error"]
        assert "Qty <= 0" in bom_errors.iloc[0]

    def test_zero_leadtime_flagged(self, part_master_df, bom_df, supplier_map_df):
        """Zero LeadTime gets error annotation."""
        from local.reports.reports import validate_and_annotate
        sup = supplier_map_df.copy()
        sup.loc[0, "LeadTime"] = 0
        result = validate_and_annotate(part_master_df, bom_df, sup)
        sup_errors = result["Supplier Map"]["_SCAFFOLD_Error"]
        assert "LeadTime <= 0" in sup_errors.iloc[0]

    def test_returns_all_three_tabs(self, part_master_df, bom_df, supplier_map_df):
        """Result contains Part Master, BOM Structure, Supplier Map."""
        from local.reports.reports import validate_and_annotate
        result = validate_and_annotate(part_master_df, bom_df, supplier_map_df)
        assert set(result.keys()) == {"Part Master", "BOM Structure", "Supplier Map"}

    def test_original_data_preserved(self, part_master_df, bom_df, supplier_map_df):
        """Original columns are preserved alongside _SCAFFOLD_Error."""
        from local.reports.reports import validate_and_annotate
        result = validate_and_annotate(part_master_df, bom_df, supplier_map_df)
        assert "PartNumber" in result["Part Master"].columns
        assert "AssemblyName" in result["BOM Structure"].columns
        assert "Supplier" in result["Supplier Map"].columns


# ===================================================================
# L1-23: Auto-timestamp Filenames
# ===================================================================

class TestAutoTimestampFilenames:
    """L1-23: Never overwrite: validated_YYYYMMDD_HHMMSS.xlsx."""

    def test_format_correct(self):
        """Filename follows prefix_YYYYMMDD_HHMMSS.ext pattern."""
        from local.reports.reports import timestamped_filename
        now = datetime(2026, 2, 9, 14, 30, 0)
        name = timestamped_filename("validated", "xlsx", now=now)
        assert name == "validated_20260209_143000.xlsx"

    def test_different_times_different_names(self):
        """Two calls at different times produce different filenames."""
        from local.reports.reports import timestamped_filename
        t1 = datetime(2026, 2, 9, 14, 30, 0)
        t2 = datetime(2026, 2, 9, 14, 30, 1)
        assert timestamped_filename("out", "xlsx", now=t1) != \
               timestamped_filename("out", "xlsx", now=t2)

    def test_custom_prefix_and_extension(self):
        """Supports different prefixes and extensions."""
        from local.reports.reports import timestamped_filename
        now = datetime(2026, 1, 1, 0, 0, 0)
        assert timestamped_filename("report", "pdf", now=now) == "report_20260101_000000.pdf"
        assert timestamped_filename("proposal", "csv", now=now) == "proposal_20260101_000000.csv"

    def test_default_uses_current_time(self):
        """Without explicit time, uses current datetime."""
        from local.reports.reports import timestamped_filename
        name = timestamped_filename("test", "txt")
        # Should contain today's date
        today = datetime.now().strftime("%Y%m%d")
        assert today in name


# ===================================================================
# L1-24: Network Summary Report
# ===================================================================

class TestNetworkSummaryReport:
    """L1-24: nodes/edges/depth/sites/patterns statistics."""

    def test_summary_node_count(self, digraph, part_master_df, end_products, supplier_map_df):
        """Summary reports correct node count."""
        from local.reports.reports import generate_network_summary
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        assert summary["nodes"] == 54

    def test_summary_edge_count(self, digraph, part_master_df, end_products, supplier_map_df):
        """Summary reports correct edge count."""
        from local.reports.reports import generate_network_summary
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        assert summary["edges"] == 51

    def test_summary_site_count(self, digraph, part_master_df, end_products, supplier_map_df):
        """Summary reports 5 sites."""
        from local.reports.reports import generate_network_summary
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        assert summary["site_count"] == 5

    def test_summary_end_products(self, digraph, part_master_df, end_products, supplier_map_df):
        """Summary reports 3 end products."""
        from local.reports.reports import generate_network_summary
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        assert summary["end_products"] == 3

    def test_summary_max_depth(self, digraph, part_master_df, end_products, supplier_map_df):
        """Max depth is 7 (FG-001)."""
        from local.reports.reports import generate_network_summary
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        assert summary["max_depth"] == 7

    def test_summary_transfer_edges(self, digraph, part_master_df, end_products, supplier_map_df):
        """4 transfer edges in test data."""
        from local.reports.reports import generate_network_summary
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        assert summary["transfer_edges"] == 4

    def test_summary_single_source_parts(self, digraph, part_master_df, end_products, supplier_map_df):
        """Correct number of single-source parts."""
        from local.reports.reports import generate_network_summary
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        assert summary["single_source_parts"] > 0

    def test_summary_has_all_keys(self, digraph, part_master_df, end_products, supplier_map_df):
        """Summary has all expected keys."""
        from local.reports.reports import generate_network_summary
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        expected_keys = {
            "nodes", "edges", "sites", "site_count", "end_products",
            "depths", "max_depth", "patterns", "leaves", "roots",
            "transfer_edges", "single_source_parts",
            "highest_lt_part", "highest_lt_value",
        }
        assert set(summary.keys()) >= expected_keys


# ===================================================================
# L1-25: PartSource Proposal
# ===================================================================

class TestPartSourceProposal:
    """L1-25: Excel with checkbox for consultant review."""

    def test_proposal_has_required_columns(self, digraph, supplier_map_df):
        """Proposal has all expected columns."""
        from local.reports.reports import generate_part_source_proposal
        df = generate_part_source_proposal(digraph, supplier_map_df)
        expected = {"PartNumber", "Site", "Activity", "Supplier", "LeadTime",
                    "MaxLeadTime", "SupplierCount", "SingleSource", "Approved", "Notes"}
        assert set(df.columns) >= expected

    def test_proposal_covers_all_nodes(self, digraph, supplier_map_df):
        """Every graph node has at least one proposal row."""
        from local.reports.reports import generate_part_source_proposal
        df = generate_part_source_proposal(digraph, supplier_map_df)
        proposal_nodes = set(zip(df["PartNumber"], df["Site"]))
        assert proposal_nodes == set(digraph.nodes())

    def test_proposal_approved_column_empty(self, digraph, supplier_map_df):
        """Approved column starts empty for consultant to fill."""
        from local.reports.reports import generate_part_source_proposal
        df = generate_part_source_proposal(digraph, supplier_map_df)
        assert (df["Approved"] == "").all()

    def test_proposal_single_source_flagged(self, digraph, supplier_map_df):
        """Single-source parts have SingleSource=True."""
        from local.reports.reports import generate_part_source_proposal
        df = generate_part_source_proposal(digraph, supplier_map_df)
        rm003_rows = df[df["PartNumber"] == "RM-003"]
        assert rm003_rows["SingleSource"].all()

    def test_proposal_multi_source_not_flagged(self, digraph, supplier_map_df):
        """Multi-source parts have SingleSource=False."""
        from local.reports.reports import generate_part_source_proposal
        df = generate_part_source_proposal(digraph, supplier_map_df)
        rm001_rows = df[df["PartNumber"] == "RM-001"]
        assert not rm001_rows["SingleSource"].any()

    def test_proposal_activity_types(self, digraph, supplier_map_df):
        """Proposal includes Make, Buy, Transfer activity types."""
        from local.reports.reports import generate_part_source_proposal
        df = generate_part_source_proposal(digraph, supplier_map_df)
        activities = set(df["Activity"].unique())
        assert activities == {"Make", "Buy", "Transfer"}


# ===================================================================
# L1-26: Proposal Readback
# ===================================================================

class TestProposalReadback:
    """L1-26: Re-read consultant's checkbox decisions."""

    def test_readback_filters_decisions(self):
        """Only rows with Approved filled are returned."""
        from local.reports.reports import read_proposal_decisions
        df = pd.DataFrame({
            "PartNumber": ["A", "B", "C"],
            "Approved": ["Yes", "", "No"],
            "Notes": ["ok", "", "reject"],
        })
        result = read_proposal_decisions(df)
        assert len(result) == 2
        assert set(result["PartNumber"]) == {"A", "C"}

    def test_readback_empty_proposal(self):
        """Proposal with no decisions returns empty DataFrame."""
        from local.reports.reports import read_proposal_decisions
        df = pd.DataFrame({
            "PartNumber": ["A", "B"],
            "Approved": ["", ""],
            "Notes": ["", ""],
        })
        result = read_proposal_decisions(df)
        assert len(result) == 0

    def test_readback_all_decided(self):
        """Fully filled proposal returns all rows."""
        from local.reports.reports import read_proposal_decisions
        df = pd.DataFrame({
            "PartNumber": ["A", "B"],
            "Approved": ["Yes", "No"],
            "Notes": ["good", "bad"],
        })
        result = read_proposal_decisions(df)
        assert len(result) == 2

    def test_readback_preserves_columns(self):
        """Original columns preserved in readback."""
        from local.reports.reports import read_proposal_decisions
        df = pd.DataFrame({
            "PartNumber": ["A"],
            "Site": ["S1"],
            "Activity": ["Buy"],
            "Approved": ["Yes"],
            "Notes": ["approve this"],
        })
        result = read_proposal_decisions(df)
        assert "Site" in result.columns
        assert "Activity" in result.columns


# ===================================================================
# L1-27: PDF Audit Report
# ===================================================================

class TestPDFAuditReport:
    """L1-27: Standalone structure audit report data generation."""

    def test_audit_report_structure(self, digraph, part_master_df, end_products, supplier_map_df, bom_df):
        """Audit report data has expected keys."""
        from local.reports.reports import (
            generate_audit_report_data,
            generate_network_summary,
            validate_and_annotate,
        )
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        validation = validate_and_annotate(part_master_df, bom_df, supplier_map_df)
        report = generate_audit_report_data(summary, validation)

        assert "title" in report
        assert "generated" in report
        assert "summary" in report
        assert "validation_errors" in report
        assert "total_errors" in report
        assert "findings" in report

    def test_audit_report_clean_data(self, digraph, part_master_df, end_products, supplier_map_df, bom_df):
        """Clean data produces zero total errors."""
        from local.reports.reports import (
            generate_audit_report_data,
            generate_network_summary,
            validate_and_annotate,
        )
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        validation = validate_and_annotate(part_master_df, bom_df, supplier_map_df)
        report = generate_audit_report_data(summary, validation)

        assert report["total_errors"] == 0
        assert any("zero errors" in f for f in report["findings"])

    def test_audit_report_findings_include_single_source(self, digraph, part_master_df, end_products, supplier_map_df, bom_df):
        """Findings mention single-source risk when present."""
        from local.reports.reports import (
            generate_audit_report_data,
            generate_network_summary,
            validate_and_annotate,
        )
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        validation = validate_and_annotate(part_master_df, bom_df, supplier_map_df)
        report = generate_audit_report_data(summary, validation)

        assert any("single source" in f.lower() for f in report["findings"])

    def test_audit_report_findings_include_transfers(self, digraph, part_master_df, end_products, supplier_map_df, bom_df):
        """Findings mention transfer edges when present."""
        from local.reports.reports import (
            generate_audit_report_data,
            generate_network_summary,
            validate_and_annotate,
        )
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        validation = validate_and_annotate(part_master_df, bom_df, supplier_map_df)
        report = generate_audit_report_data(summary, validation)

        assert any("transfer" in f.lower() for f in report["findings"])

    def test_audit_report_title(self, digraph, part_master_df, end_products, supplier_map_df, bom_df):
        """Report title is SCAFFOLD Structure Audit Report."""
        from local.reports.reports import (
            generate_audit_report_data,
            generate_network_summary,
            validate_and_annotate,
        )
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        validation = validate_and_annotate(part_master_df, bom_df, supplier_map_df)
        report = generate_audit_report_data(summary, validation)

        assert report["title"] == "SCAFFOLD Structure Audit Report"
