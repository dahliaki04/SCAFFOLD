"""L1-09: Max LeadTime / L1-10: Auto-Activity / L1-11: Path Fingerprinting / L1-12: Pattern Grouping.

Risk engine: computes supply chain risk metrics from the BOM graph.
All traversals are iterative (stack-based) — no recursion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import networkx as nx
import pandas as pd

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# L1-09: Max LeadTime Calculation
# ---------------------------------------------------------------------------

def compute_max_leadtime(supplier_map_df: pd.DataFrame) -> dict[str, int]:
    """Compute max lead time per part from Supplier Map.

    When a part has multiple suppliers, the **maximum** lead time is
    taken as the risk value (worst-case scenario).

    Returns ``{part_name: max_lead_time}``.
    """
    return supplier_map_df.groupby("Part")["LeadTime"].max().to_dict()


# ---------------------------------------------------------------------------
# L1-10: Auto-Activity Assignment
# ---------------------------------------------------------------------------

def assign_activity(part: str, site: str, G: nx.DiGraph) -> str:
    """Derive activity type from BOM graph structure.

    Decision order (per CLAUDE.md spec):

    1. Has assembly children (child.Part ≠ parent.Part) → **Make**
    2. Has only same-part cross-site children → **Transfer**
    3. Leaf node (no children) → **Buy**
    """
    children = list(G.successors((part, site)))
    if not children:
        return "Buy"
    has_assembly = any(cp != part for cp, cs in children)
    if has_assembly:
        return "Make"
    return "Transfer"


# ---------------------------------------------------------------------------
# L1-11: Path Fingerprinting (DFS) — ITERATIVE
# ---------------------------------------------------------------------------

def compute_paths(
    start: tuple[str, str],
    G: nx.DiGraph,
) -> list[list[tuple[str, str]]]:
    """Compute all root-to-leaf paths from *start* via iterative DFS.

    Each path is a list of ``(PartName, SiteID)`` tuples from the
    start node to a leaf (out-degree 0).

    Uses an explicit stack — **no recursion**.
    """
    paths: list[list[tuple[str, str]]] = []
    # Stack entries: (current_node, path_so_far)
    stack: list[tuple[tuple[str, str], list[tuple[str, str]]]] = [
        (start, [start])
    ]

    while stack:
        node, path = stack.pop()
        children = list(G.successors(node))
        if not children:
            # Leaf — record complete path
            paths.append(path)
        else:
            for child in children:
                stack.append((child, path + [child]))

    return paths


# ---------------------------------------------------------------------------
# L1-12: Pattern String Grouping
# ---------------------------------------------------------------------------

def extract_pattern(
    paths: list[list[tuple[str, str]]],
) -> tuple[tuple[str, ...], ...]:
    """Extract the site-sequence pattern from a set of paths.

    The pattern captures the **structural shape** of the BOM: the
    sequence of sites visited along each root-to-leaf path, with
    part names abstracted away.  Two end products with identical BOM
    structures (same site sequences) share the same pattern.

    Returns a hashable tuple-of-tuples suitable as a dict key.
    """
    site_sequences = []
    for path in paths:
        sites = tuple(site for _part, site in path)
        site_sequences.append(sites)
    # Sort for canonical ordering so comparison is order-independent
    return tuple(sorted(site_sequences))


def group_by_pattern(
    end_products: set[tuple[str, str]],
    G: nx.DiGraph,
) -> dict[tuple, list[tuple[str, str]]]:
    """Group end products by their site-sequence pattern.

    Returns ``{pattern: [list of (PartName, SiteID) end products]}``.
    Uses pattern as dict key for O(1) grouping.
    """
    groups: dict[tuple, list[tuple[str, str]]] = {}
    for ep in end_products:
        paths = compute_paths(ep, G)
        pattern = extract_pattern(paths)
        groups.setdefault(pattern, []).append(ep)
    return groups
