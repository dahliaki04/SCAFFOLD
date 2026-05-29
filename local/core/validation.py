"""L1-02: Schema Validation / L1-03: SubGroup UsageShare Check.
L1-39: Priority column validation (precondition for auto-SubGroup derivation).

Validates structural integrity of input DataFrames before graph construction.
Returns lists of human-readable error strings (empty list = valid).
"""

from __future__ import annotations

import math

import pandas as pd

# ---------------------------------------------------------------------------
# L1-02: Schema Validation
# ---------------------------------------------------------------------------

_PART_MASTER_REQUIRED = ["PartNumber", "Site", "Stage", "IsEndProduct"]
_BOM_REQUIRED = ["AssemblyName", "AssemblySite", "ComponentName", "ComponentSite", "Qty"]
_SUPPLIER_MAP_REQUIRED = ["Part", "Supplier", "LeadTime"]


def validate_part_master(df: pd.DataFrame) -> list[str]:
    """Validate Part Master tab schema and data quality."""
    errors: list[str] = []

    # Required columns
    for col in _PART_MASTER_REQUIRED:
        if col not in df.columns:
            errors.append(f"Part Master: missing required column '{col}'")

    if errors:
        return errors  # can't check data if columns are missing

    # Blank PartNumber
    blank_mask = df["PartNumber"].isna() | (df["PartNumber"].astype(str).str.strip() == "")
    n_blank = blank_mask.sum()
    if n_blank > 0:
        errors.append(f"Part Master: {n_blank} row(s) with blank PartNumber")

    # Blank Site
    blank_site = df["Site"].isna() | (df["Site"].astype(str).str.strip() == "")
    n_blank_site = blank_site.sum()
    if n_blank_site > 0:
        errors.append(f"Part Master: {n_blank_site} row(s) with blank Site")

    return errors


def validate_bom(df: pd.DataFrame) -> list[str]:
    """Validate BOM Structure tab schema and data quality."""
    errors: list[str] = []

    for col in _BOM_REQUIRED:
        if col not in df.columns:
            errors.append(f"BOM Structure: missing required column '{col}'")

    if errors:
        return errors

    # Qty must be positive
    bad_qty = df["Qty"] <= 0
    n_bad = bad_qty.sum()
    if n_bad > 0:
        errors.append(f"BOM Structure: {n_bad} row(s) with Qty <= 0")

    # Blank assembly/component names
    for col in ["AssemblyName", "ComponentName"]:
        blank = df[col].isna() | (df[col].astype(str).str.strip() == "")
        n = blank.sum()
        if n > 0:
            errors.append(f"BOM Structure: {n} row(s) with blank {col}")

    return errors


def validate_supplier_map(df: pd.DataFrame) -> list[str]:
    """Validate Supplier Map tab schema and data quality."""
    errors: list[str] = []

    for col in _SUPPLIER_MAP_REQUIRED:
        if col not in df.columns:
            errors.append(f"Supplier Map: missing required column '{col}'")

    if errors:
        return errors

    # LeadTime must be positive
    bad_lt = df["LeadTime"] <= 0
    n_bad = bad_lt.sum()
    if n_bad > 0:
        errors.append(f"Supplier Map: {n_bad} row(s) with LeadTime <= 0")

    return errors


# ---------------------------------------------------------------------------
# L1-03: SubGroup UsageShare Check
# ---------------------------------------------------------------------------

def validate_usage_share(df: pd.DataFrame) -> list[str]:
    """Validate that UsageShare sums to 1.0 per SubGroup.

    Rows without a SubGroup are ignored. A SubGroup with any NaN
    UsageShare values is flagged as an error.
    """
    errors: list[str] = []

    if "SubGroup" not in df.columns or "UsageShare" not in df.columns:
        return errors

    # Filter to rows that have a SubGroup
    sg_rows = df[df["SubGroup"].notna()].copy()
    if sg_rows.empty:
        return errors

    for sg_name, group in sg_rows.groupby("SubGroup"):
        # Check for NaN UsageShare within a SubGroup
        if group["UsageShare"].isna().any():
            errors.append(
                f"SubGroup '{sg_name}': contains missing UsageShare values"
            )
            continue

        total = group["UsageShare"].sum()
        if abs(total - 1.0) > 1e-6:
            errors.append(
                f"SubGroup '{sg_name}': UsageShare sums to {total:.4f}, expected 1.0"
            )

    return errors


# ---------------------------------------------------------------------------
# L1-39: Priority column validation
# ---------------------------------------------------------------------------

def validate_priority(df: pd.DataFrame) -> list[str]:
    """Validate the optional Priority column on BOM Structure.

    Run *before* SubGroup derivation. Catches user-input errors that
    would corrupt the auto-derived SubGroups:

    * Priority values must be positive integers (1, 2, 3, ...).
    * Within one parent (AssemblyName, AssemblySite), priorities must
      be unique — duplicate priorities make the alternate ordering
      ambiguous.

    A parent with only one priority-tagged row is not an error (it
    just won't generate a SubGroup), and rows with no Priority are
    ignored entirely.
    """
    errors: list[str] = []

    if "Priority" not in df.columns:
        return errors

    priority_rows = df[df["Priority"].notna()]
    if priority_rows.empty:
        return errors

    # Each non-null priority must be a positive integer
    for idx, p in priority_rows["Priority"].items():
        try:
            pi = int(p)
        except (TypeError, ValueError):
            errors.append(f"BOM row {idx}: Priority '{p}' is not an integer")
            continue
        if pi != float(p):
            errors.append(f"BOM row {idx}: Priority {p} is not a whole number")
            continue
        if pi < 1:
            errors.append(f"BOM row {idx}: Priority {pi} must be >= 1")

    # No duplicate priorities under one parent
    parent_groups = priority_rows.groupby(["AssemblyName", "AssemblySite"])
    for (pname, psite), grp in parent_groups:
        dups = grp["Priority"][grp["Priority"].duplicated(keep=False)].tolist()
        if dups:
            errors.append(
                f"Parent {pname}@{psite}: duplicate Priority values {sorted(set(int(d) for d in dups))}"
            )

    return errors
