"""Shared pytest fixtures for local tool tests.

Loads test data from CSV fixtures (bypassing xlwings for Linux CI).
xlwings I/O is tested separately on Windows CI runners.
"""

import pathlib

import networkx as nx
import pandas as pd
import pytest

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Raw DataFrames — loaded once per session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def part_master_df() -> pd.DataFrame:
    """Part Master tab: PartNumber, Site, IsEndProduct."""
    df = pd.read_csv(FIXTURES / "part_master.csv")
    # pandas may auto-convert TRUE/FALSE strings to booleans
    df["IsEndProduct"] = df["IsEndProduct"].apply(
        lambda v: v if isinstance(v, bool) else str(v).upper() == "TRUE"
    )
    return df


@pytest.fixture(scope="session")
def bom_df() -> pd.DataFrame:
    """BOM Structure tab: AssemblyName, AssemblySite, ComponentName, ComponentSite, Qty, SubGroup, UsageShare."""
    return pd.read_csv(FIXTURES / "bom_structure.csv")


@pytest.fixture(scope="session")
def supplier_map_df() -> pd.DataFrame:
    """Supplier Map tab: Part, Supplier, LeadTime."""
    return pd.read_csv(FIXTURES / "supplier_map.csv")


# ---------------------------------------------------------------------------
# Pre-built graph — batch edge list per CLAUDE.md spec
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def digraph(bom_df: pd.DataFrame) -> nx.DiGraph:
    """NetworkX DiGraph built from BOM via batch edge list (L1-04 spec)."""
    G = nx.DiGraph()
    edges = list(zip(
        zip(bom_df["AssemblyName"], bom_df["AssemblySite"]),
        zip(bom_df["ComponentName"], bom_df["ComponentSite"]),
    ))
    G.add_edges_from(edges)
    return G


# ---------------------------------------------------------------------------
# Derived helpers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def end_products(part_master_df: pd.DataFrame) -> set:
    """Set of (PartNumber, Site) tuples where IsEndProduct is True."""
    mask = part_master_df["IsEndProduct"]
    rows = part_master_df.loc[mask, ["PartNumber", "Site"]]
    return set(zip(rows["PartNumber"], rows["Site"]))


@pytest.fixture(scope="session")
def part_master_nodes(part_master_df: pd.DataFrame) -> set:
    """Set of all (PartNumber, Site) tuples from Part Master."""
    return set(zip(part_master_df["PartNumber"], part_master_df["Site"]))
