"""L1-01: V4 Excel Reader / L1-08: Smart Ignore.

Reads Part Master, BOM Structure, and Supplier Map tabs.
xlwings is used for Excel I/O; pandas DataFrames are the internal format.

normalize_input_dtypes() — see docstring there — fixes a class of cryptic
node-not-in-graph errors caused by pandas inferring float64 for Site/Part
columns whose values happen to be all numeric.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from pathlib import Path


# L1-08 ----------------------------------------------------------------

def filter_scaffold_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove any columns starting with ``_SCAFFOLD_`` (L1-08 Smart Ignore).

    When a validated Excel is re-fed into the tool, it may carry
    ``_SCAFFOLD_Error`` or similar columns from the previous run.
    This filter strips them so schema validation doesn't reject the file.
    """
    keep = [c for c in df.columns if not c.startswith("_SCAFFOLD_")]
    return df[keep]


# L1-01 ----------------------------------------------------------------

def read_part_master(path: Path, **kw) -> pd.DataFrame:
    """Read the *Part Master* tab from an Excel workbook via xlwings.

    Returns a cleaned :class:`~pandas.DataFrame` with columns
    ``PartNumber``, ``Site``, ``IsEndProduct``.
    """
    import xlwings as xw

    wb = xw.Book(str(path), **kw)
    try:
        sheet = wb.sheets["Part Master"]
        df = sheet.used_range.options(pd.DataFrame, index=False).value
    finally:
        wb.close()

    df = filter_scaffold_columns(df)
    return df


def read_bom(path: Path, **kw) -> pd.DataFrame:
    """Read the *BOM Structure* tab from an Excel workbook via xlwings.

    Returns a cleaned :class:`~pandas.DataFrame` with columns
    ``AssemblyName``, ``AssemblySite``, ``ComponentName``,
    ``ComponentSite``, ``Qty``, and optional ``SubGroup`` / ``UsageShare``.
    """
    import xlwings as xw

    wb = xw.Book(str(path), **kw)
    try:
        sheet = wb.sheets["BOM Structure"]
        df = sheet.used_range.options(pd.DataFrame, index=False).value
    finally:
        wb.close()

    df = filter_scaffold_columns(df)
    return df


def read_supplier_map(path: Path, **kw) -> pd.DataFrame:
    """Read the *Supplier Map* tab from an Excel workbook via xlwings.

    Returns a cleaned :class:`~pandas.DataFrame` with columns
    ``Part``, ``Supplier``, ``LeadTime``.
    """
    import xlwings as xw

    wb = xw.Book(str(path), **kw)
    try:
        sheet = wb.sheets["Supplier Map"]
        df = sheet.used_range.options(pd.DataFrame, index=False).value
    finally:
        wb.close()

    df = filter_scaffold_columns(df)
    return df


# ---------------------------------------------------------------------------
# Type normalization — fixes node-not-in-graph crashes from mixed dtypes
# ---------------------------------------------------------------------------

# Columns that participate in the (PartName, SiteID) tuple identity used as
# graph keys. Any dtype drift between tabs on these columns produces a
# cryptic NetworkXError downstream — coerce them to str up-front.
_PM_STR_COLS = ("PartNumber", "Site")
_BOM_STR_COLS = ("AssemblyName", "AssemblySite", "ComponentName", "ComponentSite")
_SUP_STR_COLS = ("Part", "Supplier")


def _coerce_str_value(v):
    """Coerce a scalar to string, preserving NaN and trimming trailing .0
    from whole-number floats (so 9999.0 → "9999", matching how the same
    code would be entered in a different tab as text).
    """
    if pd.isna(v):
        return v
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    s = str(v)
    return s.strip() if s else s


def _coerce_str_columns(df: pd.DataFrame, cols: tuple[str, ...]) -> pd.DataFrame:
    """Return df with the named columns coerced to string dtype (NaN preserved)."""
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            continue
        out[c] = out[c].apply(_coerce_str_value)
    return out


def normalize_input_dtypes(
    pm_df: pd.DataFrame,
    bom_df: pd.DataFrame,
    sup_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Coerce identity columns to string dtype across all three tabs.

    Why: node identity in the BOM graph is the tuple ``(PartName, SiteID)``.
    When a Site column contains only numeric-looking values (e.g. plant
    codes like ``9999``), pandas infers float64 and the tuple becomes
    ``("part", 9999.0)``. If the same site is stored as text in another
    tab, its tuple is ``("part", "9999")``. Python tuple equality is
    type-strict, so the two never match and downstream code raises a
    cryptic ``NetworkXError: The node ('part', 9999.0) is not in the
    digraph`` instead of a useful validation message.

    Run this immediately after reading, regardless of source format
    (Excel or CSV). NaN values are preserved so blank-cell validators
    still flag them.
    """
    return (
        _coerce_str_columns(pm_df, _PM_STR_COLS),
        _coerce_str_columns(bom_df, _BOM_STR_COLS),
        _coerce_str_columns(sup_df, _SUP_STR_COLS),
    )
