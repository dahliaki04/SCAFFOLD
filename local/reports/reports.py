"""L1-22: In-place Excel Validation / L1-23: Auto-timestamp Filenames /
L1-24: Network Summary Report / L1-25: PartSource Proposal /
L1-26: Proposal Readback / L1-27: PDF Audit Report.

Report generation for standalone local value (no SaaS required).
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import networkx as nx
import pandas as pd

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# L1-23: Auto-timestamp Filenames
# ---------------------------------------------------------------------------

def timestamped_filename(prefix: str, ext: str, now: datetime | None = None) -> str:
    """Generate a timestamped filename that never overwrites.

    Example: ``validated_20260209_143000.xlsx``
    """
    if now is None:
        now = datetime.now()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{stamp}.{ext}"


# ---------------------------------------------------------------------------
# L1-22: In-place Excel Validation
# ---------------------------------------------------------------------------

def validate_and_annotate(
    part_master_df: pd.DataFrame,
    bom_df: pd.DataFrame,
    supplier_map_df: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Validate input data and annotate errors in-place.

    Returns a dict of DataFrames (one per tab), each with an added
    ``_SCAFFOLD_Error`` column containing comma-separated error
    descriptions per row, or empty string if the row is clean.

    This output is written to the validated Excel file (L1-22).
    """
    from local.core.validation import (
        validate_bom,
        validate_part_master,
        validate_supplier_map,
    )

    pm = part_master_df.copy()
    bom = bom_df.copy()
    sup = supplier_map_df.copy()

    # --- Part Master row-level errors ---
    pm["_SCAFFOLD_Error"] = ""
    blank_pn = pm["PartNumber"].isna() | (pm["PartNumber"].astype(str).str.strip() == "")
    pm.loc[blank_pn, "_SCAFFOLD_Error"] = "Blank PartNumber"
    blank_site = pm["Site"].isna() | (pm["Site"].astype(str).str.strip() == "")
    pm.loc[blank_site, "_SCAFFOLD_Error"] = pm.loc[blank_site, "_SCAFFOLD_Error"].apply(
        lambda v: f"{v}; Blank Site".strip("; ") if v else "Blank Site"
    )

    # --- BOM row-level errors ---
    bom["_SCAFFOLD_Error"] = ""
    if "Qty" in bom.columns:
        bad_qty = bom["Qty"] <= 0
        bom.loc[bad_qty, "_SCAFFOLD_Error"] = "Qty <= 0"

    # Check SubGroup UsageShare per row
    if "SubGroup" in bom.columns and "UsageShare" in bom.columns:
        sg_rows = bom["SubGroup"].notna()
        nan_share = sg_rows & bom["UsageShare"].isna()
        bom.loc[nan_share, "_SCAFFOLD_Error"] = bom.loc[nan_share, "_SCAFFOLD_Error"].apply(
            lambda v: f"{v}; Missing UsageShare".strip("; ") if v else "Missing UsageShare"
        )

        # Check sums per SubGroup
        for sg_name, group in bom[sg_rows].groupby("SubGroup"):
            if group["UsageShare"].isna().any():
                continue
            total = group["UsageShare"].sum()
            if abs(total - 1.0) > 1e-6:
                idx = group.index
                bom.loc[idx, "_SCAFFOLD_Error"] = bom.loc[idx, "_SCAFFOLD_Error"].apply(
                    lambda v, sg=sg_name, t=total: (
                        f"{v}; SubGroup '{sg}' sums to {t:.4f}".strip("; ")
                        if v else f"SubGroup '{sg}' sums to {t:.4f}"
                    )
                )

    # Blank assembly/component names
    for col in ["AssemblyName", "ComponentName"]:
        if col in bom.columns:
            blank = bom[col].isna() | (bom[col].astype(str).str.strip() == "")
            bom.loc[blank, "_SCAFFOLD_Error"] = bom.loc[blank, "_SCAFFOLD_Error"].apply(
                lambda v, c=col: f"{v}; Blank {c}".strip("; ") if v else f"Blank {c}"
            )

    # --- Supplier Map row-level errors ---
    sup["_SCAFFOLD_Error"] = ""
    if "LeadTime" in sup.columns:
        bad_lt = sup["LeadTime"] <= 0
        sup.loc[bad_lt, "_SCAFFOLD_Error"] = "LeadTime <= 0"

    return {
        "Part Master": pm,
        "BOM Structure": bom,
        "Supplier Map": sup,
    }


# ---------------------------------------------------------------------------
# L1-24: Network Summary Report
# ---------------------------------------------------------------------------

def generate_network_summary(
    G: nx.DiGraph,
    part_master_df: pd.DataFrame,
    end_products: set[tuple[str, str]],
    supplier_map_df: pd.DataFrame,
    bom_df: pd.DataFrame | None = None,
) -> dict:
    """Generate network summary statistics.

    Returns a dict with nodes, edges, depth, sites, patterns,
    and other high-level BOM structure metrics.
    """
    from local.core.risk import (
        compute_max_leadtime,
        compute_paths,
        detect_single_source,
        extract_pattern,
        group_by_pattern,
    )

    # Basic counts
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    sites = sorted(part_master_df["Site"].unique())

    # Depth per end product
    depths: dict[str, int] = {}
    for ep in end_products:
        paths = compute_paths(ep, G)
        max_depth = max(len(p) for p in paths)
        ep_label = f"{ep[0]}@{ep[1]}"
        depths[ep_label] = max_depth

    # Pattern groups
    groups = group_by_pattern(end_products, G)

    # Leaf / root counts
    leaves = [n for n in G.nodes() if G.out_degree(n) == 0]
    roots = [n for n in G.nodes() if G.in_degree(n) == 0]

    # Transfer edges
    transfer_edges = [
        (p, c) for p, c in G.edges()
        if p[0] == c[0] and p[1] != c[1]
    ]

    # Single source — L1-39: pass bom_df so SubGroup membership filters out
    # parts that already have an alternate component (auto or manual).
    single_source = detect_single_source(supplier_map_df, bom_df)

    # Max lead times
    max_lt = compute_max_leadtime(supplier_map_df)
    highest_lt_part = max(max_lt, key=max_lt.get) if max_lt else None

    return {
        "nodes": num_nodes,
        "edges": num_edges,
        "sites": sites,
        "site_count": len(sites),
        "end_products": len(end_products),
        "depths": depths,
        "max_depth": max(depths.values()) if depths else 0,
        "patterns": len(groups),
        "leaves": len(leaves),
        "roots": len(roots),
        "transfer_edges": len(transfer_edges),
        "single_source_parts": len(single_source),
        "highest_lt_part": highest_lt_part,
        "highest_lt_value": max_lt.get(highest_lt_part, 0) if highest_lt_part else 0,
    }


# ---------------------------------------------------------------------------
# L1-25: PartSource Proposal
# ---------------------------------------------------------------------------

def generate_part_source_proposal(
    G: nx.DiGraph,
    supplier_map_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate a PartSource proposal for consultant review.

    Each row is a part + supplier combination with activity type,
    lead time, and columns for consultant checkbox decisions:
    ``Approved``, ``Notes``.
    """
    from local.core.risk import assign_activity, compute_max_leadtime

    rows: list[dict] = []
    max_lt = compute_max_leadtime(supplier_map_df)

    # Build supplier list per part
    suppliers_by_part = supplier_map_df.groupby("Part").apply(
        lambda g: list(zip(g["Supplier"], g["LeadTime"])),
        include_groups=False,
    ).to_dict()

    for node in sorted(G.nodes()):
        part, site = node
        activity = assign_activity(part, site, G)
        part_suppliers = suppliers_by_part.get(part, [])
        supplier_count = len(part_suppliers)
        part_max_lt = max_lt.get(part, 0)

        if part_suppliers:
            for sup, lt in part_suppliers:
                rows.append({
                    "PartNumber": part,
                    "Site": site,
                    "Activity": activity,
                    "Supplier": sup,
                    "LeadTime": lt,
                    "MaxLeadTime": part_max_lt,
                    "SupplierCount": supplier_count,
                    "SingleSource": supplier_count == 1,
                    "Approved": "",
                    "Notes": "",
                })
        else:
            rows.append({
                "PartNumber": part,
                "Site": site,
                "Activity": activity,
                "Supplier": "",
                "LeadTime": 0,
                "MaxLeadTime": part_max_lt,
                "SupplierCount": 0,
                "SingleSource": False,
                "Approved": "",
                "Notes": "",
            })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# L1-26: Proposal Readback
# ---------------------------------------------------------------------------

def read_proposal_decisions(proposal_df: pd.DataFrame) -> pd.DataFrame:
    """Re-read consultant's checkbox decisions from a filled proposal.

    Returns only rows where the consultant made a decision
    (Approved is non-empty).
    """
    mask = proposal_df["Approved"].notna() & (
        proposal_df["Approved"].astype(str).str.strip() != ""
    )
    return proposal_df[mask].copy()


# ---------------------------------------------------------------------------
# L1-27: PDF Audit Report
# ---------------------------------------------------------------------------

def generate_audit_report_data(
    summary: dict,
    validation_results: dict[str, pd.DataFrame],
) -> dict:
    """Prepare structured data for the PDF audit report.

    Collects network summary, validation error counts, and key
    findings into a dict suitable for rendering into PDF.

    Actual PDF rendering depends on a PDF library (e.g. reportlab)
    which is a Sprint 4 concern. This function prepares the content.
    """
    # Count validation errors per tab
    error_counts: dict[str, int] = {}
    for tab_name, df in validation_results.items():
        if "_SCAFFOLD_Error" in df.columns:
            errors = df["_SCAFFOLD_Error"].astype(str).str.strip()
            error_counts[tab_name] = (errors != "").sum()
        else:
            error_counts[tab_name] = 0

    total_errors = sum(error_counts.values())

    findings: list[str] = []
    if total_errors == 0:
        findings.append("All input data passed validation with zero errors.")
    else:
        findings.append(f"Found {total_errors} validation error(s) across input tabs.")

    if summary.get("single_source_parts", 0) > 0:
        findings.append(
            f"{summary['single_source_parts']} part(s) have only one supplier (single source risk)."
        )

    if summary.get("transfer_edges", 0) > 0:
        findings.append(
            f"{summary['transfer_edges']} inter-site transfer edge(s) detected in BOM."
        )

    findings.append(
        f"Deepest BOM path: {summary.get('max_depth', 0)} levels."
    )

    return {
        "title": "SCAFFOLD Structure Audit Report",
        "generated": datetime.now().isoformat(),
        "summary": summary,
        "validation_errors": error_counts,
        "total_errors": total_errors,
        "findings": findings,
    }


def render_audit_report_pdf(
    report_data: dict,
    output_path: Path,
) -> Path:
    """Render the audit report data to PDF using ReportLab (L1-27).

    Creates a standalone PDF with:
    * Title page with generation timestamp
    * Network summary statistics table
    * Validation error summary
    * Key findings list

    Returns the path to the written PDF file.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=25 * mm,
        bottomMargin=25 * mm,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "SCTitle",
        parent=styles["Title"],
        fontSize=22,
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "SCHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=18,
        spaceAfter=8,
    )
    body_style = styles["BodyText"]

    elements = []

    # ── Title ─────────────────────────────────────────────
    elements.append(Paragraph(report_data["title"], title_style))
    elements.append(Paragraph(
        f"Generated: {report_data['generated']}",
        body_style,
    ))
    elements.append(Spacer(1, 12))

    # ── Network Summary ───────────────────────────────────
    elements.append(Paragraph("Network Summary", heading_style))
    summary = report_data["summary"]
    summary_rows = [["Metric", "Value"]]
    display_keys = [
        ("nodes", "Total Nodes"),
        ("edges", "Total Edges"),
        ("end_products", "End Products"),
        ("site_count", "Sites"),
        ("max_depth", "Max BOM Depth"),
        ("patterns", "Unique Patterns"),
        ("leaves", "Leaf Nodes (Buy)"),
        ("roots", "Root Nodes"),
        ("transfer_edges", "Transfer Edges"),
        ("single_source_parts", "Single Source Parts"),
        ("highest_lt_part", "Highest Lead Time Part"),
        ("highest_lt_value", "Highest Lead Time (days)"),
    ]
    for key, label in display_keys:
        val = summary.get(key, "N/A")
        if isinstance(val, list):
            val = ", ".join(str(v) for v in val)
        summary_rows.append([label, str(val)])

    table = Table(summary_rows, colWidths=[150, 300])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#ecf0f1")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    # ── Validation Errors ─────────────────────────────────
    elements.append(Paragraph("Validation Summary", heading_style))
    error_rows = [["Tab", "Errors"]]
    for tab, count in report_data["validation_errors"].items():
        error_rows.append([tab, str(count)])
    error_rows.append(["Total", str(report_data["total_errors"])])

    err_table = Table(error_rows, colWidths=[200, 100])
    err_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#bdc3c7")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(err_table)
    elements.append(Spacer(1, 12))

    # ── Key Findings ──────────────────────────────────────
    elements.append(Paragraph("Key Findings", heading_style))
    for finding in report_data["findings"]:
        elements.append(Paragraph(f"\u2022 {finding}", body_style))
        elements.append(Spacer(1, 4))

    # ── Footer ────────────────────────────────────────────
    elements.append(Spacer(1, 24))
    footer_style = ParagraphStyle(
        "SCFooter",
        parent=body_style,
        fontSize=8,
        textColor=colors.grey,
    )
    elements.append(Paragraph(
        "SCAFFOLD v3.0 — Supply Chain Structure Audit. "
        "This report was generated offline. No data was transmitted.",
        footer_style,
    ))

    doc.build(elements)
    return output_path
