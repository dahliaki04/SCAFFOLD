"""L1-04: NetworkX DiGraph Build / L1-05: Cycle Detection / L1-06: Orphan Detection.

Graph construction and structural validation.
Node key = (PartName, SiteID) tuple — always.
"""

from __future__ import annotations

import networkx as nx
import pandas as pd


# ---------------------------------------------------------------------------
# L1-04: NetworkX DiGraph Build
# ---------------------------------------------------------------------------

def build_digraph(bom_df: pd.DataFrame) -> nx.DiGraph:
    """Build a directed graph from BOM via batch edge list.

    Node key is ``(PartName, SiteID)`` tuple.  Both assembly edges
    (different parts) and transfer edges (same part, different sites)
    are represented in the same graph.

    Never uses ``iterrows()`` — batch zip only.
    """
    G = nx.DiGraph()
    edges = list(zip(
        zip(bom_df["AssemblyName"], bom_df["AssemblySite"]),
        zip(bom_df["ComponentName"], bom_df["ComponentSite"]),
    ))
    G.add_edges_from(edges)
    return G


# ---------------------------------------------------------------------------
# L1-05: Circular BOM Detection
# ---------------------------------------------------------------------------

def detect_cycles(G: nx.DiGraph) -> list[list[tuple]]:
    """Return all simple cycles in the graph.

    Uses ``nx.simple_cycles`` which is iterative internally.
    Returns an empty list if the graph is acyclic.
    """
    return list(nx.simple_cycles(G))


# ---------------------------------------------------------------------------
# L1-06: Orphan Detection
# ---------------------------------------------------------------------------

def detect_orphans(
    G: nx.DiGraph,
    part_master_nodes: set[tuple[str, str]],
) -> dict[str, set[tuple[str, str]]]:
    """Detect orphan nodes via set operations (O(1) per lookup).

    Returns a dict with two keys:

    * ``bom_not_in_parts`` — nodes in BOM graph but missing from Part Master
    * ``parts_not_in_bom`` — nodes in Part Master but absent from BOM graph
    """
    graph_nodes = set(G.nodes())
    return {
        "bom_not_in_parts": graph_nodes - part_master_nodes,
        "parts_not_in_bom": part_master_nodes - graph_nodes,
    }
