"""L1-01: V4 Excel Reader / L1-08: Smart Ignore.

Reads Part Master, BOM Structure, and Supplier Map tabs.
xlwings is used for Excel I/O; pandas DataFrames are the internal format.
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
    ``ComponentSite``, ``Qty``, and optional ``SubGroup`` / ``UsageShare``
    / ``Priority`` (L1-39 — when 2+ children of one parent carry a
    Priority value, the tool auto-derives a SubGroup for them).
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
