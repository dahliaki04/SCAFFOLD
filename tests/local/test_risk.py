"""Tests for L1-09 (Max LT), L1-10 (Auto-Activity), L1-11 (Path DFS), L1-12 (Pattern Grouping)."""

import networkx as nx
import pandas as pd
import pytest


# ===================================================================
# L1-09: Max LeadTime Calculation
# ===================================================================

class TestMaxLeadTime:
    """L1-09: Multi-source → take Max(LT) per part as risk value."""

    def test_max_lt_multi_source(self, supplier_map_df: pd.DataFrame):
        """RM-001 has SUP-A01(14) and SUP-A02(21) → max = 21."""
        from local.core.risk import compute_max_leadtime
        max_lt = compute_max_leadtime(supplier_map_df)
        assert max_lt["RM-001"] == 21

    def test_max_lt_single_source(self, supplier_map_df: pd.DataFrame):
        """RM-003 has SUP-B01(28) only → max = 28."""
        from local.core.risk import compute_max_leadtime
        max_lt = compute_max_leadtime(supplier_map_df)
        assert max_lt["RM-003"] == 28

    def test_max_lt_rm005(self, supplier_map_df: pd.DataFrame):
        """RM-005 has SUP-A03(10) and SUP-A04(15) → max = 15."""
        from local.core.risk import compute_max_leadtime
        max_lt = compute_max_leadtime(supplier_map_df)
        assert max_lt["RM-005"] == 15

    def test_max_lt_rm020(self, supplier_map_df: pd.DataFrame):
        """RM-020 has SUP-C03(10) and SUP-C04(18) → max = 18."""
        from local.core.risk import compute_max_leadtime
        max_lt = compute_max_leadtime(supplier_map_df)
        assert max_lt["RM-020"] == 18

    def test_max_lt_all_parts_covered(self, supplier_map_df: pd.DataFrame):
        """Every unique part in Supplier Map has a max LT entry."""
        from local.core.risk import compute_max_leadtime
        max_lt = compute_max_leadtime(supplier_map_df)
        expected_parts = set(supplier_map_df["Part"].unique())
        assert set(max_lt.keys()) == expected_parts

    def test_max_lt_all_positive(self, supplier_map_df: pd.DataFrame):
        """All max lead times are positive."""
        from local.core.risk import compute_max_leadtime
        max_lt = compute_max_leadtime(supplier_map_df)
        assert all(v > 0 for v in max_lt.values())


# ===================================================================
# L1-10: Auto-Activity Assignment
# ===================================================================

class TestAutoActivity:
    """L1-10: BOM-derived BUY/MAKE/TRANSFER assignment."""

    def test_make_node(self, digraph: nx.DiGraph):
        """FG-001@PLANT-A has assembly children → Make."""
        from local.core.risk import assign_activity
        assert assign_activity("FG-001", "PLANT-A", digraph) == "Make"

    def test_make_sub_assembly(self, digraph: nx.DiGraph):
        """SA-001@PLANT-A has assembly children → Make."""
        from local.core.risk import assign_activity
        assert assign_activity("SA-001", "PLANT-A", digraph) == "Make"

    def test_transfer_node_dc_east(self, digraph: nx.DiGraph):
        """FG-001@DC-EAST has only same-part cross-site child → Transfer."""
        from local.core.risk import assign_activity
        assert assign_activity("FG-001", "DC-EAST", digraph) == "Transfer"

    def test_transfer_node_wip003_planta(self, digraph: nx.DiGraph):
        """WIP-003@PLANT-A has only same-part cross-site child → Transfer."""
        from local.core.risk import assign_activity
        assert assign_activity("WIP-003", "PLANT-A", digraph) == "Transfer"

    def test_transfer_node_dc_west(self, digraph: nx.DiGraph):
        """FG-002@DC-WEST has only same-part cross-site child → Transfer."""
        from local.core.risk import assign_activity
        assert assign_activity("FG-002", "DC-WEST", digraph) == "Transfer"

    def test_transfer_node_wip005_plantb(self, digraph: nx.DiGraph):
        """WIP-005@PLANT-B has only same-part cross-site child → Transfer."""
        from local.core.risk import assign_activity
        assert assign_activity("WIP-005", "PLANT-B", digraph) == "Transfer"

    def test_buy_leaf_node(self, digraph: nx.DiGraph):
        """RM-001@PLANT-A is a leaf → Buy."""
        from local.core.risk import assign_activity
        assert assign_activity("RM-001", "PLANT-A", digraph) == "Buy"

    def test_buy_another_leaf(self, digraph: nx.DiGraph):
        """RM-015@PLANT-C is a leaf → Buy."""
        from local.core.risk import assign_activity
        assert assign_activity("RM-015", "PLANT-C", digraph) == "Buy"

    def test_make_wip003_plantb(self, digraph: nx.DiGraph):
        """WIP-003@PLANT-B has assembly children (RM-003, RM-004) → Make."""
        from local.core.risk import assign_activity
        assert assign_activity("WIP-003", "PLANT-B", digraph) == "Make"

    def test_make_fg003_plantc(self, digraph: nx.DiGraph):
        """FG-003@PLANT-C has assembly children → Make (not Transfer)."""
        from local.core.risk import assign_activity
        assert assign_activity("FG-003", "PLANT-C", digraph) == "Make"

    def test_make_wip005_plantc(self, digraph: nx.DiGraph):
        """WIP-005@PLANT-C has assembly children (RM-015, RM-016) → Make."""
        from local.core.risk import assign_activity
        assert assign_activity("WIP-005", "PLANT-C", digraph) == "Make"

    def test_all_rm_are_buy(self, digraph: nx.DiGraph):
        """Every RM-xxx node is a leaf → Buy."""
        from local.core.risk import assign_activity
        for node in digraph.nodes():
            part, site = node
            if part.startswith("RM-"):
                assert assign_activity(part, site, digraph) == "Buy", \
                    f"{part}@{site} should be Buy"


# ===================================================================
# L1-11: Path Fingerprinting (DFS)
# ===================================================================

class TestPathFingerprinting:
    """L1-11: Per FG — iterative DFS → store site sequence."""

    def test_fg001_path_depth(self, digraph: nx.DiGraph):
        """FG-001 deepest path has 7 levels."""
        from local.core.risk import compute_paths
        paths = compute_paths(("FG-001", "DC-EAST"), digraph)
        max_depth = max(len(p) for p in paths)
        assert max_depth == 7

    def test_fg002_path_depth(self, digraph: nx.DiGraph):
        """FG-002 deepest path has 6 levels."""
        from local.core.risk import compute_paths
        paths = compute_paths(("FG-002", "DC-WEST"), digraph)
        max_depth = max(len(p) for p in paths)
        assert max_depth == 6

    def test_fg003_path_depth(self, digraph: nx.DiGraph):
        """FG-003 deepest path has 3 levels."""
        from local.core.risk import compute_paths
        paths = compute_paths(("FG-003", "PLANT-C"), digraph)
        max_depth = max(len(p) for p in paths)
        assert max_depth == 3

    def test_fg001_path_starts_at_root(self, digraph: nx.DiGraph):
        """Every FG-001 path starts at (FG-001, DC-EAST)."""
        from local.core.risk import compute_paths
        paths = compute_paths(("FG-001", "DC-EAST"), digraph)
        for path in paths:
            assert path[0] == ("FG-001", "DC-EAST")

    def test_fg001_paths_end_at_leaves(self, digraph: nx.DiGraph):
        """Every FG-001 path ends at a leaf node (out-degree 0)."""
        from local.core.risk import compute_paths
        paths = compute_paths(("FG-001", "DC-EAST"), digraph)
        for path in paths:
            assert digraph.out_degree(path[-1]) == 0, \
                f"Path ending at {path[-1]} is not a leaf"

    def test_fg001_has_cross_site_path(self, digraph: nx.DiGraph):
        """FG-001 has at least one path crossing DC-EAST → PLANT-A → PLANT-B."""
        from local.core.risk import compute_paths
        paths = compute_paths(("FG-001", "DC-EAST"), digraph)
        sites_in_paths = [tuple(site for _, site in p) for p in paths]
        has_cross = any(
            "DC-EAST" in s and "PLANT-A" in s and "PLANT-B" in s
            for s in sites_in_paths
        )
        assert has_cross

    def test_paths_are_iterative(self):
        """Path computation must not use recursion (structural check)."""
        import inspect
        from local.core.risk import compute_paths
        source = inspect.getsource(compute_paths)
        # Should use stack-based iteration, not call itself
        assert "compute_paths" not in source.split("def compute_paths")[1], \
            "compute_paths appears to use recursion"


# ===================================================================
# L1-12: Pattern String Grouping
# ===================================================================

class TestPatternGrouping:
    """L1-12: Pattern as dict key → O(1) grouping of FGs."""

    def test_fg001_and_fg002_different_patterns(self, digraph: nx.DiGraph):
        """FG-001 and FG-002 have different site patterns."""
        from local.core.risk import compute_paths, extract_pattern

        paths_1 = compute_paths(("FG-001", "DC-EAST"), digraph)
        paths_2 = compute_paths(("FG-002", "DC-WEST"), digraph)

        pattern_1 = extract_pattern(paths_1)
        pattern_2 = extract_pattern(paths_2)

        assert pattern_1 != pattern_2

    def test_pattern_is_hashable(self, digraph: nx.DiGraph):
        """Pattern can be used as dict key."""
        from local.core.risk import compute_paths, extract_pattern

        paths = compute_paths(("FG-001", "DC-EAST"), digraph)
        pattern = extract_pattern(paths)

        # Must be usable as dict key
        d = {pattern: "FG-001"}
        assert d[pattern] == "FG-001"

    def test_group_by_pattern(self, digraph: nx.DiGraph, end_products: set):
        """Grouping end products by pattern produces correct groups."""
        from local.core.risk import compute_paths, extract_pattern, group_by_pattern

        groups = group_by_pattern(end_products, digraph)

        # 3 end products, each with unique structure → 3 groups (or fewer if patterns match)
        assert len(groups) >= 1
        total_fgs = sum(len(v) for v in groups.values())
        assert total_fgs == 3

    def test_identical_structures_group_together(self):
        """Two FGs with identical BOM structure share the same pattern."""
        from local.core.risk import compute_paths, extract_pattern

        # Build two identical mini BOMs
        G = nx.DiGraph()
        G.add_edges_from([
            (("FG-A", "S1"), ("RM-X", "S1")),
            (("FG-B", "S1"), ("RM-Y", "S1")),
        ])

        paths_a = compute_paths(("FG-A", "S1"), G)
        paths_b = compute_paths(("FG-B", "S1"), G)

        pattern_a = extract_pattern(paths_a)
        pattern_b = extract_pattern(paths_b)

        assert pattern_a == pattern_b
