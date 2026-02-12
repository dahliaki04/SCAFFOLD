"""L1-09: Max LeadTime / L1-10: Auto-Activity / L1-11: Path Fingerprinting / L1-12: Pattern Grouping.
L1-13: Single Source Detection / L1-14: Impact Analysis / L1-15: Site Dependency Map.

Risk engine: computes supply chain risk metrics from the BOM graph.
All traversals are iterative (stack-based) — no recursion.
"""

from __future__ import annotations

from collections import deque
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


# ---------------------------------------------------------------------------
# L1-13: Single Source Detection
# ---------------------------------------------------------------------------

def detect_single_source(supplier_map_df: pd.DataFrame) -> set[str]:
    """Flag parts that have only one supplier (single source risk).

    Returns a set of part names with exactly one supplier.
    """
    counts = supplier_map_df.groupby("Part")["Supplier"].nunique()
    return set(counts[counts == 1].index)


# ---------------------------------------------------------------------------
# L1-14: Impact Analysis
# ---------------------------------------------------------------------------

def analyze_supplier_impact(
    supplier_map_df: pd.DataFrame,
    G: nx.DiGraph,
    end_products: set[tuple[str, str]],
) -> dict[str, dict]:
    """Compute impact of each supplier going offline.

    For each supplier, determines which parts it supplies, and then
    traces upward through the BOM graph to count how many end products
    (product lines) would be affected.

    Returns ``{supplier: {"parts": [...], "affected_products": [...], "count": N}}``.
    """
    # Build reverse graph for upward tracing (child → parent)
    R = G.reverse(copy=True)

    # Map supplier → parts (vectorized — no iterrows)
    supplier_parts: dict[str, set[str]] = {}
    unique_pairs = supplier_map_df[["Part", "Supplier"]].drop_duplicates()
    for part, supplier in zip(unique_pairs["Part"], unique_pairs["Supplier"]):
        supplier_parts.setdefault(supplier, set()).add(part)

    # Map part → all (part, site) nodes in graph
    part_nodes: dict[str, list[tuple[str, str]]] = {}
    for part, site in G.nodes():
        part_nodes.setdefault(part, []).append((part, site))

    ep_set = set(end_products)
    result: dict[str, dict] = {}

    for supplier, parts in supplier_parts.items():
        affected_eps: set[tuple[str, str]] = set()
        for part in parts:
            for node in part_nodes.get(part, []):
                # BFS upward through reverse graph to find reachable end products
                visited: set[tuple[str, str]] = set()
                queue: deque[tuple[str, str]] = deque([node])
                while queue:
                    current = queue.popleft()
                    if current in visited:
                        continue
                    visited.add(current)
                    if current in ep_set:
                        affected_eps.add(current)
                    for parent in R.successors(current):
                        if parent not in visited:
                            queue.append(parent)

        result[supplier] = {
            "parts": sorted(parts),
            "affected_products": sorted(affected_eps),
            "count": len(affected_eps),
        }

    return result


# ---------------------------------------------------------------------------
# L1-15: Site Dependency Map
# ---------------------------------------------------------------------------

def build_site_dependency_map(
    G: nx.DiGraph,
    end_products: set[tuple[str, str]],
) -> dict[str, dict]:
    """Map each site to the end products and BOMs that depend on it.

    Answers: "If factory X relocates, which BOMs need to change?"

    Returns ``{site: {"nodes": [...], "affected_products": [...], "count": N}}``.
    """
    R = G.reverse(copy=True)
    ep_set = set(end_products)

    # Group nodes by site
    site_nodes: dict[str, list[tuple[str, str]]] = {}
    for part, site in G.nodes():
        site_nodes.setdefault(site, []).append((part, site))

    result: dict[str, dict] = {}

    for site, nodes in site_nodes.items():
        affected_eps: set[tuple[str, str]] = set()
        for node in nodes:
            # BFS upward to find reachable end products
            visited: set[tuple[str, str]] = set()
            queue: deque[tuple[str, str]] = deque([node])
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                if current in ep_set:
                    affected_eps.add(current)
                for parent in R.successors(current):
                    if parent not in visited:
                        queue.append(parent)

        result[site] = {
            "nodes": sorted(nodes),
            "affected_products": sorted(affected_eps),
            "count": len(affected_eps),
        }

    return result
