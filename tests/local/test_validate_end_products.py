"""Tests for validate_end_products_have_bom() — turns the cryptic
NetworkXError into a clear validation message."""

from __future__ import annotations

import pandas as pd

from local.core.validation import validate_end_products_have_bom


def _pm_row(part, site, is_ep):
    return {"PartNumber": part, "Site": site, "Stage": "X", "IsEndProduct": is_ep}


def _bom_row(parent, p_site, child, c_site, qty=1):
    return {"AssemblyName": parent, "AssemblySite": p_site,
            "ComponentName": child, "ComponentSite": c_site, "Qty": qty}


def test_no_end_products_no_error():
    pm  = pd.DataFrame([_pm_row("RM-01", "S", False)])
    bom = pd.DataFrame(columns=["AssemblyName", "AssemblySite",
                                "ComponentName", "ComponentSite", "Qty"])
    assert validate_end_products_have_bom(pm, bom) == []


def test_end_product_with_bom_entry_passes():
    pm  = pd.DataFrame([
        _pm_row("FG-001", "DC-US", True),
        _pm_row("RM-01",  "PLANT", False),
    ])
    bom = pd.DataFrame([_bom_row("FG-001", "DC-US", "RM-01", "PLANT")])
    assert validate_end_products_have_bom(pm, bom) == []


def test_orphan_end_product_flagged():
    """End product declared but never appears as a parent in BOM — exact
    repro of the user-reported NetworkXError condition."""
    pm  = pd.DataFrame([
        _pm_row("SQJ142EP-T1_JE3-J", "9999", True),  # end product, never assembled
        _pm_row("DIE-XYZ", "9999", False),
    ])
    bom = pd.DataFrame([
        _bom_row("SOMETHING-ELSE", "9999", "DIE-XYZ", "9999"),
    ])
    errs = validate_end_products_have_bom(pm, bom)
    assert len(errs) == 1
    assert "SQJ142EP-T1_JE3-J@9999" in errs[0]
    assert "no BOM entry" in errs[0]


def test_multiple_orphans_summarized():
    pm  = pd.DataFrame([_pm_row(f"FG-{i:03d}", "S", True) for i in range(8)])
    bom = pd.DataFrame(columns=["AssemblyName", "AssemblySite",
                                "ComponentName", "ComponentSite", "Qty"])
    errs = validate_end_products_have_bom(pm, bom)
    assert len(errs) == 1
    assert "8 end product(s)" in errs[0]
    assert "and 3 more" in errs[0]  # 5 listed + 3 more


def test_isendproduct_string_TRUE_handled():
    """Excel often returns IsEndProduct as the string 'TRUE'/'FALSE' rather
    than a real bool — defensive coercion."""
    pm  = pd.DataFrame([{"PartNumber": "FG-1", "Site": "S", "Stage": "X", "IsEndProduct": "TRUE"}])
    bom = pd.DataFrame(columns=["AssemblyName", "AssemblySite",
                                "ComponentName", "ComponentSite", "Qty"])
    errs = validate_end_products_have_bom(pm, bom)
    assert len(errs) == 1
    assert "FG-1@S" in errs[0]


def test_nan_endproduct_rows_skipped():
    """Rows with NaN PartNumber or Site are skipped here — they're already
    flagged by validate_part_master, no need to duplicate-flag them."""
    pm  = pd.DataFrame([
        {"PartNumber": None, "Site": "S", "Stage": "X", "IsEndProduct": True},
        {"PartNumber": "FG", "Site": None, "Stage": "X", "IsEndProduct": True},
    ])
    bom = pd.DataFrame(columns=["AssemblyName", "AssemblySite",
                                "ComponentName", "ComponentSite", "Qty"])
    assert validate_end_products_have_bom(pm, bom) == []


def test_missing_columns_no_op():
    pm  = pd.DataFrame([{"X": 1}])  # no IsEndProduct column
    bom = pd.DataFrame(columns=["AssemblyName", "AssemblySite",
                                "ComponentName", "ComponentSite", "Qty"])
    assert validate_end_products_have_bom(pm, bom) == []
