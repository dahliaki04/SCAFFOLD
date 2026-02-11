"""Tests for L1-27 (PDF Audit Report rendering)."""

import tempfile
from pathlib import Path

import pandas as pd
import pytest


class TestPDFAuditReport:
    """L1-27: PDF Audit Report with ReportLab rendering."""

    def test_render_creates_pdf_file(self, digraph, part_master_df, supplier_map_df, end_products):
        """render_audit_report_pdf creates a valid PDF file."""
        from local.reports.reports import (
            generate_network_summary,
            validate_and_annotate,
            generate_audit_report_data,
            render_audit_report_pdf,
        )
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        validation = validate_and_annotate(part_master_df, pd.read_csv(
            Path(__file__).parent / "fixtures" / "bom_structure.csv"
        ), supplier_map_df)
        report_data = generate_audit_report_data(summary, validation)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.pdf"
            result = render_audit_report_pdf(report_data, path)
            assert result.exists()
            assert result.stat().st_size > 0

    def test_pdf_starts_with_magic_bytes(self, digraph, part_master_df, supplier_map_df, end_products):
        """PDF file starts with %PDF- header."""
        from local.reports.reports import (
            generate_network_summary,
            validate_and_annotate,
            generate_audit_report_data,
            render_audit_report_pdf,
        )
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        validation = validate_and_annotate(part_master_df, pd.read_csv(
            Path(__file__).parent / "fixtures" / "bom_structure.csv"
        ), supplier_map_df)
        report_data = generate_audit_report_data(summary, validation)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.pdf"
            render_audit_report_pdf(report_data, path)
            content = path.read_bytes()
            assert content[:5] == b"%PDF-"

    def test_pdf_has_pages(self, digraph, part_master_df, supplier_map_df, end_products):
        """PDF contains at least one page object."""
        from local.reports.reports import (
            generate_network_summary,
            validate_and_annotate,
            generate_audit_report_data,
            render_audit_report_pdf,
        )
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        validation = validate_and_annotate(part_master_df, pd.read_csv(
            Path(__file__).parent / "fixtures" / "bom_structure.csv"
        ), supplier_map_df)
        report_data = generate_audit_report_data(summary, validation)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.pdf"
            render_audit_report_pdf(report_data, path)
            content = path.read_bytes().decode("latin-1")
            # ReportLab PDFs contain /Page type objects
            assert "/Type /Page" in content

    def test_render_with_zero_errors(self, digraph, part_master_df, supplier_map_df, end_products):
        """PDF renders correctly when there are no validation errors."""
        from local.reports.reports import (
            generate_network_summary,
            validate_and_annotate,
            generate_audit_report_data,
            render_audit_report_pdf,
        )
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        # Clean data has zero errors
        validation = validate_and_annotate(part_master_df, pd.read_csv(
            Path(__file__).parent / "fixtures" / "bom_structure.csv"
        ), supplier_map_df)
        report_data = generate_audit_report_data(summary, validation)
        assert report_data["total_errors"] == 0

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.pdf"
            result = render_audit_report_pdf(report_data, path)
            assert result.exists()

    def test_render_with_errors(self, digraph, part_master_df, supplier_map_df, end_products):
        """PDF renders correctly when there are validation errors."""
        from local.reports.reports import (
            generate_network_summary,
            generate_audit_report_data,
            render_audit_report_pdf,
        )
        summary = generate_network_summary(digraph, part_master_df, end_products, supplier_map_df)
        # Manually inject errors
        report_data = generate_audit_report_data(summary, {
            "Part Master": pd.DataFrame({"_SCAFFOLD_Error": ["Blank PartNumber", "", "Blank Site"]}),
            "BOM Structure": pd.DataFrame({"_SCAFFOLD_Error": ["", ""]}),
            "Supplier Map": pd.DataFrame({"_SCAFFOLD_Error": [""]}),
        })
        assert report_data["total_errors"] == 2

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "report.pdf"
            result = render_audit_report_pdf(report_data, path)
            assert result.exists()
            assert result.stat().st_size > 0
