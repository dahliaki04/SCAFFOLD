"""L1-02: Schema Validation / L1-03: SubGroup UsageShare Check.

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
# Cross-tab integrity: end products must appear in BOM as parents
# ---------------------------------------------------------------------------

def validate_end_products_have_bom(
    pm_df: pd.DataFrame,
    bom_df: pd.DataFrame,
) -> list[str]:
    """Every IsEndProduct=True row must appear as an ``AssemblyName`` in BOM.

    Without this check, an end product declared in Part Master but with
    no BOM entry as parent slips through validation, ends up in the
    ``end_products`` set, and then crashes ``compute_paths`` /
    ``group_by_pattern`` with::

        NetworkXError: The node ('SQJ142EP-T1_JE3-J', 9999.0) is not
        in the digraph

    This validator turns that opaque failure into a clear, actionable
    user-facing message at the validation gate, naming the orphan end
    products so the consultant knows exactly which rows to fix.
    """
    errors: list[str] = []

    if "IsEndProduct" not in pm_df.columns:
        return errors
    if "AssemblyName" not in bom_df.columns or "AssemblySite" not in bom_df.columns:
        return errors

    # Coerce IsEndProduct to bool defensively (handles "TRUE"/"FALSE" strings)
    is_ep = pm_df["IsEndProduct"].apply(
        lambda v: v if isinstance(v, bool) else str(v).strip().upper() == "TRUE"
    )
    end_products = pm_df[is_ep]
    if end_products.empty:
        return errors

    # Set of (parent_name, parent_site) tuples that appear as assemblies in BOM
    parents = set(zip(bom_df["AssemblyName"], bom_df["AssemblySite"]))

    orphans: list[str] = []
    for _, row in end_products.iterrows():
        pn, site = row.get("PartNumber"), row.get("Site")
        if pd.isna(pn) or pd.isna(site):
            continue  # already flagged by validate_part_master
        if (pn, site) not in parents:
            orphans.append(f"{pn}@{site}")

    if orphans:
        sample = ", ".join(orphans[:5])
        more = f" (and {len(orphans) - 5} more)" if len(orphans) > 5 else ""
        errors.append(
            f"Part Master: {len(orphans)} end product(s) declared with no BOM entry "
            f"as parent — would crash path computation: {sample}{more}"
        )

    return errors
