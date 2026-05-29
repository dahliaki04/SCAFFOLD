"""L1-29: Generic CSV Export Plugin.

Universal CSV export of the full BOM analysis in a flat, tool-agnostic format.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    import networkx as nx


def export_generic_csv(
    G: "nx.DiGraph",
    part_master_df: pd.DataFrame,
    supplier_map_df: pd.DataFrame,
    bom_df: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Export a flat CSV with full BOM analysis results.

    Columns:
    - PartNumber, Site: Node identity
    - Activity: Make/Buy/Transfer (BOM-derived)
    - MaxLeadTime: Worst-case lead time across all suppliers
    - SupplierCount: Number of suppliers for this part
    - SingleSource: True if only one supplier
    - Depth: BOM depth from nearest end product
    - IsEndProduct: From Part Master
    - Stage: From Part Master
    - Suppliers: Comma-separated list of supplier names

    Returns the path to the written file.
    """
    from local.core.risk import (
        assign_activity,
        compute_max_leadtime,
        detect_single_source,
    )

    max_lt = compute_max_leadtime(supplier_map_df)
    # L1-39: bom_df enables the SubGroup-aware filter — parts with an
    # alternate component are no longer flagged as single-source even
    # when their supplier is unique.
    single_src = detect_single_source(supplier_map_df, bom_df)

    # Build lookups
    stage_lookup: dict[tuple[str, str], str] = {}
    is_ep_lookup: dict[tuple[str, str], bool] = {}
    for _, row in part_master_df.iterrows():
        key = (row["PartNumber"], row["Site"])
        stage_lookup[key] = row.get("Stage", "")
        is_ep_lookup[key] = bool(row.get("IsEndProduct", False))

    # Supplier list per part
    suppliers_by_part: dict[str, list[str]] = {}
    for _, row in supplier_map_df.iterrows():
        suppliers_by_part.setdefault(row["Part"], []).append(row["Supplier"])

    # Compute depths via BFS from end products
    import networkx as nx

    end_products = {n for n in G.nodes() if is_ep_lookup.get(n, False)}
    depths: dict[tuple[str, str], int] = {}
    for ep in end_products:
        lengths = nx.single_source_shortest_path_length(G, ep)
        for node, d in lengths.items():
            depths[node] = max(depths.get(node, 0), d)
    for node in G.nodes():
        depths.setdefault(node, 0)

    rows: list[dict] = []
    for node in sorted(G.nodes()):
        part, site = node
        activity = assign_activity(part, site, G)
        lt = max_lt.get(part, 0)
        sups = suppliers_by_part.get(part, [])

        rows.append({
            "PartNumber": part,
            "Site": site,
            "Activity": activity,
            "MaxLeadTime": lt,
            "SupplierCount": len(sups),
            "SingleSource": part in single_src,
            "Depth": depths.get(node, 0),
            "IsEndProduct": is_ep_lookup.get(node, False),
            "Stage": stage_lookup.get(node, ""),
            "Suppliers": "; ".join(sorted(set(sups))),
        })

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    return output_path
