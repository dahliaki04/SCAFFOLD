"""Tests for the soft-warn behavior + defensive compute_paths against
orphan end products. Repros the user-reported pattern where the demand
site (9999) is intentionally separate from the production site (1522)."""

from __future__ import annotations

import networkx as nx
import pandas as pd

from local.core.risk import compute_paths, group_by_pattern
from local.reports.reports import generate_network_summary


def _build_demand_production_split_graph():
    """Mirror Brian's data: end product 'X' declared @9999, BOM has X @1522."""
    G = nx.DiGraph()
    G.add_edge(("IRF9640", "1522"), ("DIE-A", "1522"))
    G.add_edge(("DIE-A", "1522"), ("WAFER-7N", "FAB-TW"))
    return G


class TestComputePathsDefensive:
    def test_returns_empty_for_missing_start(self):
        G = _build_demand_production_split_graph()
        orphan = ("IRF9640", "9999")
        paths = compute_paths(orphan, G)
        assert paths == [], "must return [] not raise NetworkXError"

    def test_in_graph_node_still_works(self):
        G = _build_demand_production_split_graph()
        paths = compute_paths(("IRF9640", "1522"), G)
        assert len(paths) == 1
        assert paths[0] == [("IRF9640", "1522"), ("DIE-A", "1522"), ("WAFER-7N", "FAB-TW")]


class TestGroupByPatternToleratesOrphans:
    def test_orphan_ep_doesnt_crash_pattern_grouping(self):
        """group_by_pattern iterates end_products and calls compute_paths;
        with the defensive guard, orphans should land in an empty-pattern
        bucket instead of crashing."""
        G = _build_demand_production_split_graph()
        end_products = {("IRF9640", "9999"), ("IRF9640", "1522")}
        groups = group_by_pattern(end_products, G)
        # No crash. Both end products are accounted for somewhere.
        all_eps = [ep for products in groups.values() for ep in products]
        assert ("IRF9640", "9999") in all_eps
        assert ("IRF9640", "1522") in all_eps


class TestSummaryWithOrphanEPs:
    def test_orphan_ep_assigned_depth_zero(self):
        """generate_network_summary must not crash on max() of empty paths."""
        G = _build_demand_production_split_graph()
        pm = pd.DataFrame([
            {"PartNumber": "IRF9640", "Site": "9999", "Stage": "Final", "IsEndProduct": True},
            {"PartNumber": "IRF9640", "Site": "1522", "Stage": "Final", "IsEndProduct": False},
            {"PartNumber": "DIE-A",   "Site": "1522", "Stage": "Wafer", "IsEndProduct": False},
            {"PartNumber": "WAFER-7N","Site": "FAB-TW","Stage": "Wafer", "IsEndProduct": False},
        ])
        sup = pd.DataFrame([{"Part": "WAFER-7N", "Supplier": "TSMC", "LeadTime": 30}])
        end_products = {("IRF9640", "9999"), ("IRF9640", "1522")}

        summary = generate_network_summary(G, pm, end_products, sup)

        # No crash. Orphan ep gets depth 0; real ep has depth >0.
        assert summary["depths"]["IRF9640@9999"] == 0
        assert summary["depths"]["IRF9640@1522"] > 0
