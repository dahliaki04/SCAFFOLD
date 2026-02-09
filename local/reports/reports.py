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

    # Single source
    single_source = detect_single_source(supplier_map_df)

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
