"""L1-28: Kinaxis V7 Export Plugin.

Exports BOM data in RapidResponse V7 CSV format for Kinaxis integration.
The output follows the Kinaxis RapidResponse import template structure.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    import networkx as nx


def export_kinaxis_v7(
    G: "nx.DiGraph",
    part_master_df: pd.DataFrame,
    supplier_map_df: pd.DataFrame,
    bom_df: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Export data in Kinaxis RapidResponse V7 CSV format.

    The V7 format uses these columns:
    - Part: Part identifier
    - Site: Site/plant location
    - ParentPart: Assembly parent (empty for top-level)
    - ParentSite: Assembly parent site
    - Quantity: BOM quantity
    - LeadTime: Max supplier lead time
    - Activity: Make/Buy/Transfer (BOM-derived)
    - Supplier: Primary supplier name
    - Category: Part category (stage from Part Master)

    Returns the path to the written file.
    """
    from local.core.risk import assign_activity, compute_max_leadtime

    max_lt = compute_max_leadtime(supplier_map_df)

    # Build supplier lookup: part → primary supplier (first by lead time)
    primary_supplier: dict[str, str] = {}
    for part, group in supplier_map_df.groupby("Part"):
        # Primary = supplier with max lead time (worst case)
        best = group.loc[group["LeadTime"].idxmax()]
        primary_supplier[part] = best["Supplier"]

    # Build stage lookup
    stage_lookup: dict[tuple[str, str], str] = {}
    for _, row in part_master_df.iterrows():
        stage_lookup[(row["PartNumber"], row["Site"])] = row.get("Stage", "")

    rows: list[dict] = []
    for _, row in bom_df.iterrows():
        child_part = row["ComponentName"]
        child_site = row["ComponentSite"]
        parent_part = row["AssemblyName"]
        parent_site = row["AssemblySite"]
        qty = row["Qty"]

        activity = assign_activity(child_part, child_site, G)
        lt = max_lt.get(child_part, 0)
        supplier = primary_supplier.get(child_part, "")
        category = stage_lookup.get((child_part, child_site), "")

        rows.append({
            "Part": child_part,
            "Site": child_site,
            "ParentPart": parent_part,
            "ParentSite": parent_site,
            "Quantity": qty,
            "LeadTime": lt,
            "Activity": activity,
            "Supplier": supplier,
            "Category": category,
        })

    # Add top-level end products (no parent)
    for node in G.nodes():
        part, site = node
        if G.in_degree(node) == 0:
            activity = assign_activity(part, site, G)
            lt = max_lt.get(part, 0)
            supplier = primary_supplier.get(part, "")
            category = stage_lookup.get((part, site), "")
            rows.append({
                "Part": part,
                "Site": site,
                "ParentPart": "",
                "ParentSite": "",
                "Quantity": 1,
                "LeadTime": lt,
                "Activity": activity,
                "Supplier": supplier,
                "Category": category,
            })

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    return output_path
