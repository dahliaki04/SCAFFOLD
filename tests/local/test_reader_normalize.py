"""Tests for normalize_input_dtypes() — the str-coercion that prevents the
NetworkX 'node not in digraph' crash when Site/Part columns are inferred
as float64."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from local.core.reader import normalize_input_dtypes, _coerce_str_value


class TestCoerceScalar:
    def test_nan_preserved(self):
        v = _coerce_str_value(float("nan"))
        assert isinstance(v, float) and math.isnan(v)

    def test_whole_float_drops_trailing_zero(self):
        assert _coerce_str_value(9999.0) == "9999"

    def test_non_whole_float_keeps_decimals(self):
        assert _coerce_str_value(12.5) == "12.5"

    def test_int_becomes_str(self):
        assert _coerce_str_value(42) == "42"

    def test_str_passes_through_with_strip(self):
        assert _coerce_str_value("  PLANT-A  ") == "PLANT-A"


class TestNormalizeInputDtypes:
    def test_repro_numeric_site_mismatch(self):
        """The exact failure pattern from the user-reported crash:
        Part Master has Site as numeric (9999.0), BOM Structure has it as
        string ('9999'). Without normalization the tuples don't match.
        """
        pm = pd.DataFrame([
            {"PartNumber": "SQJ142EP-T1_JE3-J", "Site": 9999.0,
             "Stage": "Final Test", "IsEndProduct": True},
        ])
        bom = pd.DataFrame([
            {"AssemblyName": "SQJ142EP-T1_JE3-J", "AssemblySite": "9999",
             "ComponentName": "DIE-XYZ", "ComponentSite": "9999", "Qty": 1},
        ])
        sup = pd.DataFrame([{"Part": "DIE-XYZ", "Supplier": "ACME", "LeadTime": 14}])

        # Before normalization: mismatch
        pm_key_pre  = (pm.loc[0, "PartNumber"], pm.loc[0, "Site"])
        bom_key_pre = (bom.loc[0, "AssemblyName"], bom.loc[0, "AssemblySite"])
        assert pm_key_pre != bom_key_pre, "pre-condition: tuples differ by type"

        # After normalization: match
        pm_out, bom_out, _ = normalize_input_dtypes(pm, bom, sup)
        pm_key  = (pm_out.loc[0, "PartNumber"], pm_out.loc[0, "Site"])
        bom_key = (bom_out.loc[0, "AssemblyName"], bom_out.loc[0, "AssemblySite"])
        assert pm_key == bom_key == ("SQJ142EP-T1_JE3-J", "9999")

    def test_nan_cells_preserved_for_validators(self):
        pm = pd.DataFrame([
            {"PartNumber": "X", "Site": "S", "Stage": "A", "IsEndProduct": True},
            {"PartNumber": None, "Site": "S", "Stage": "A", "IsEndProduct": False},
        ])
        bom = pd.DataFrame(columns=["AssemblyName", "AssemblySite", "ComponentName",
                                    "ComponentSite", "Qty"])
        sup = pd.DataFrame(columns=["Part", "Supplier", "LeadTime"])
        pm_out, _, _ = normalize_input_dtypes(pm, bom, sup)
        assert pd.isna(pm_out.loc[1, "PartNumber"]), "NaN must be preserved so blank-cell validators still fire"

    def test_missing_columns_no_op(self):
        # Bom_df missing AssemblySite shouldn't crash normalization
        pm = pd.DataFrame([{"PartNumber": "X", "Site": "S", "Stage": "A", "IsEndProduct": True}])
        bom = pd.DataFrame([{"AssemblyName": "X", "ComponentName": "Y", "Qty": 1}])  # no AssemblySite
        sup = pd.DataFrame(columns=["Part", "Supplier", "LeadTime"])
        pm_out, bom_out, _ = normalize_input_dtypes(pm, bom, sup)
        assert "AssemblySite" not in bom_out.columns  # absent stays absent

    def test_existing_strings_unchanged(self):
        pm = pd.DataFrame([{"PartNumber": "RM-01", "Site": "PLANT-A", "Stage": "X", "IsEndProduct": True}])
        bom = pd.DataFrame([{"AssemblyName": "RM-01", "AssemblySite": "PLANT-A",
                             "ComponentName": "RM-02", "ComponentSite": "PLANT-A", "Qty": 1}])
        sup = pd.DataFrame([{"Part": "RM-02", "Supplier": "ACME", "LeadTime": 7}])
        pm_out, bom_out, sup_out = normalize_input_dtypes(pm, bom, sup)
        assert pm_out.loc[0, "Site"] == "PLANT-A"
        assert bom_out.loc[0, "ComponentSite"] == "PLANT-A"
