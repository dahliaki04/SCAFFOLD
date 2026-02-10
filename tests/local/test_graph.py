"""Tests for L1-04 (DiGraph Build), L1-05 (Cycle Detection), L1-06 (Orphan Detection)."""

import networkx as nx
import pandas as pd
import pytest


# ===================================================================
# L1-04: NetworkX DiGraph Build
# ===================================================================

class TestDiGraphBuild:
    """L1-04: Batch edge list from BOM, node key = (PartName, SiteID)."""

    def test_graph_is_digraph(self, digraph: nx.DiGraph):
        """Built graph is a directed graph."""
        assert isinstance(digraph, nx.DiGraph)

    def test_graph_node_count(self, digraph: nx.DiGraph):
        """Graph has 54 nodes (all Part+Site combos from BOM edges)."""
        # Nodes come from both parent and child side of BOM edges
        assert digraph.number_of_nodes() == 54

    def test_graph_edge_count(self, digraph: nx.DiGraph):
        """Graph has 51 edges (one per BOM row)."""
        assert digraph.number_of_edges() == 51

    def test_node_key_is_tuple(self, digraph: nx.DiGraph):
        """Every node key is a (PartName, SiteID) tuple."""
        for node in digraph.nodes():
            assert isinstance(node, tuple), f"Node {node} is not a tuple"
            assert len(node) == 2, f"Node {node} doesn't have exactly 2 elements"

    def test_transfer_edges_exist(self, digraph: nx.DiGraph):
        """Transfer edges present: same part, different site."""
        # FG-001@DC-EAST → FG-001@PLANT-A
        assert digraph.has_edge(("FG-001", "DC-EAST"), ("FG-001", "PLANT-A"))
        # WIP-003@PLANT-A → WIP-003@PLANT-B
        assert digraph.has_edge(("WIP-003", "PLANT-A"), ("WIP-003", "PLANT-B"))
        # FG-002@DC-WEST → FG-002@PLANT-B
        assert digraph.has_edge(("FG-002", "DC-WEST"), ("FG-002", "PLANT-B"))
        # WIP-005@PLANT-B → WIP-005@PLANT-C
        assert digraph.has_edge(("WIP-005", "PLANT-B"), ("WIP-005", "PLANT-C"))

    def test_assembly_edges_exist(self, digraph: nx.DiGraph):
        """Assembly edges present: different parts."""
        assert digraph.has_edge(("FG-001", "PLANT-A"), ("SA-001", "PLANT-A"))
        assert digraph.has_edge(("SA-001", "PLANT-A"), ("WIP-001", "PLANT-A"))
        assert digraph.has_edge(("FG-003", "PLANT-C"), ("WIP-006", "PLANT-C"))

    def test_leaf_nodes_have_no_successors(self, digraph: nx.DiGraph):
        """Raw material leaf nodes have zero out-degree."""
        leaves = [("RM-001", "PLANT-A"), ("RM-003", "PLANT-B"), ("RM-025", "PLANT-C")]
        for leaf in leaves:
            assert digraph.out_degree(leaf) == 0, f"{leaf} should be a leaf"

    def test_end_products_are_roots(self, digraph: nx.DiGraph):
        """End product nodes at DC sites have zero in-degree (graph roots)."""
        assert digraph.in_degree(("FG-001", "DC-EAST")) == 0
        assert digraph.in_degree(("FG-002", "DC-WEST")) == 0
        assert digraph.in_degree(("FG-003", "PLANT-C")) == 0

    def test_batch_build_matches_conftest(self, bom_df: pd.DataFrame, digraph: nx.DiGraph):
        """Graph built via batch edge list matches conftest fixture."""
        from local.core.graph import build_digraph
        G = build_digraph(bom_df)
        assert set(G.nodes()) == set(digraph.nodes())
        assert set(G.edges()) == set(digraph.edges())


# ===================================================================
# L1-05: Circular BOM Detection
# ===================================================================

class TestCycleDetection:
    """L1-05: nx.simple_cycles(G), iterative only."""

    def test_no_cycles_in_test_data(self, digraph: nx.DiGraph):
        """Test data is acyclic."""
        from local.core.graph import detect_cycles
        cycles = detect_cycles(digraph)
        assert cycles == []

    def test_detects_simple_cycle(self):
        """Injected A→B→C→A cycle is detected."""
        from local.core.graph import detect_cycles
        G = nx.DiGraph()
        G.add_edges_from([
            (("A", "S1"), ("B", "S1")),
            (("B", "S1"), ("C", "S1")),
            (("C", "S1"), ("A", "S1")),
        ])
        cycles = detect_cycles(G)
        assert len(cycles) == 1
        assert set(cycles[0]) == {("A", "S1"), ("B", "S1"), ("C", "S1")}

    def test_detects_self_loop(self):
        """Self-referencing edge detected as cycle."""
        from local.core.graph import detect_cycles
        G = nx.DiGraph()
        G.add_edge(("X", "S1"), ("X", "S1"))
        cycles = detect_cycles(G)
        assert len(cycles) == 1

    def test_detects_multiple_cycles(self):
        """Multiple independent cycles detected."""
        from local.core.graph import detect_cycles
        G = nx.DiGraph()
        G.add_edges_from([
            (("A", "S1"), ("B", "S1")),
            (("B", "S1"), ("A", "S1")),
            (("C", "S1"), ("D", "S1")),
            (("D", "S1"), ("C", "S1")),
        ])
        cycles = detect_cycles(G)
        assert len(cycles) == 2


# ===================================================================
# L1-06: Orphan Detection
# ===================================================================

class TestOrphanDetection:
    """L1-06: Set operations O(1) — parts not in BOM, BOM refs not in parts."""

    def test_no_orphans_in_test_data(self, digraph: nx.DiGraph, part_master_nodes: set):
        """All BOM nodes exist in Part Master."""
        from local.core.graph import detect_orphans
        result = detect_orphans(digraph, part_master_nodes)
        assert result["bom_not_in_parts"] == set()

    def test_no_unused_parts_in_test_data(self, digraph: nx.DiGraph, part_master_nodes: set):
        """All Part Master entries appear in BOM."""
        from local.core.graph import detect_orphans
        result = detect_orphans(digraph, part_master_nodes)
        assert result["parts_not_in_bom"] == set()

    def test_detects_bom_ref_not_in_parts(self):
        """Part referenced in BOM but missing from Part Master flagged."""
        from local.core.graph import detect_orphans
        G = nx.DiGraph()
        G.add_edge(("A", "S1"), ("GHOST", "S1"))
        parts = {("A", "S1")}
        result = detect_orphans(G, parts)
        assert ("GHOST", "S1") in result["bom_not_in_parts"]

    def test_detects_unused_part(self):
        """Part in Part Master but absent from BOM flagged."""
        from local.core.graph import detect_orphans
        G = nx.DiGraph()
        G.add_edge(("A", "S1"), ("B", "S1"))
        parts = {("A", "S1"), ("B", "S1"), ("UNUSED", "S1")}
        result = detect_orphans(G, parts)
        assert ("UNUSED", "S1") in result["parts_not_in_bom"]

    def test_orphan_detection_uses_set_ops(self):
        """Verify orphan detection result is set-based (O(1) per lookup)."""
        from local.core.graph import detect_orphans
        G = nx.DiGraph()
        G.add_edge(("A", "S1"), ("B", "S1"))
        parts = {("A", "S1"), ("B", "S1")}
        result = detect_orphans(G, parts)
        assert isinstance(result["bom_not_in_parts"], set)
        assert isinstance(result["parts_not_in_bom"], set)
