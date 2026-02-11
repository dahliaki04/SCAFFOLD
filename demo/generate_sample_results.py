#!/usr/bin/env python3
"""Generate sample_results.json from error-laden demo data.

Runs the SCAFFOLD validation + graph analysis pipeline against
intentionally broken input files in demo/sample_errors/ to produce
a results file that showcases every category of error the Local Tool
can detect.

Usage:
    python demo/generate_sample_results.py [--output-dir DIR]

Error categories demonstrated:
    1. Schema validation  — blank PartNumber, blank Site
    2. BOM data quality   — Qty <= 0, blank AssemblyName/ComponentName
    3. SubGroup integrity — UsageShare not summing to 1.0, missing UsageShare
    4. Supplier data      — LeadTime <= 0
    5. Circular BOM       — cycle: SEAL-KIT → ROTOR → STATOR → SEAL-KIT
    6. Orphan nodes       — BOM refs not in Part Master, Part Master not in BOM
    7. Risk findings      — single-source parts, high lead times
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from local.core.validation import (
    validate_part_master,
    validate_bom,
    validate_supplier_map,
    validate_usage_share,
)
from local.core.graph import build_digraph, detect_cycles, detect_orphans
from local.core.risk import (
    compute_max_leadtime,
    detect_single_source,
)
from local.reports.reports import validate_and_annotate


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate SCAFFOLD sample results from error-laden data"
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).parent / "sample_errors"),
        help="Output directory (default: demo/sample_errors/)",
    )
    args = parser.parse_args()

    sample_dir = Path(__file__).parent / "sample_errors"
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Read error-laden CSVs ─────────────────────────────
    print("Reading error-laden sample data...")
    pm_df = pd.read_csv(sample_dir / "part_master.csv")
    pm_df["IsEndProduct"] = pm_df["IsEndProduct"].apply(
        lambda v: v if isinstance(v, bool) else str(v).upper() == "TRUE"
    )
    bom_df = pd.read_csv(sample_dir / "bom_structure.csv")
    sup_df = pd.read_csv(sample_dir / "supplier_map.csv")
    print(f"  Part Master: {len(pm_df)} rows")
    print(f"  BOM Structure: {len(bom_df)} rows")
    print(f"  Supplier Map: {len(sup_df)} rows")

    results: dict = {
        "meta": {
            "version": "3.0",
            "type": "sample_results",
            "generated": datetime.now(timezone.utc).isoformat(),
            "description": (
                "SCAFFOLD validation results from intentionally broken "
                "sample data. Demonstrates every category of error the "
                "Local Tool can detect."
            ),
        },
        "input_summary": {
            "part_master_rows": len(pm_df),
            "bom_rows": len(bom_df),
            "supplier_map_rows": len(sup_df),
        },
        "schema_validation": {},
        "row_level_errors": {},
        "graph_analysis": {},
        "risk_findings": {},
    }

    # ── 1. Schema Validation (L1-02, L1-03) ──────────────
    print("\n--- Schema Validation ---")
    pm_errors = validate_part_master(pm_df)
    bom_errors = validate_bom(bom_df)
    sup_errors = validate_supplier_map(sup_df)
    usage_errors = validate_usage_share(bom_df)

    all_errors = pm_errors + bom_errors + sup_errors + usage_errors
    results["schema_validation"] = {
        "passed": len(all_errors) == 0,
        "total_errors": len(all_errors),
        "part_master_errors": pm_errors,
        "bom_errors": bom_errors,
        "supplier_map_errors": sup_errors,
        "usage_share_errors": usage_errors,
    }

    for e in all_errors:
        print(f"  ERROR: {e}")

    # ── 2. Row-Level Annotation (L1-22) ───────────────────
    print("\n--- Row-Level Error Annotation ---")
    annotated = validate_and_annotate(pm_df, bom_df, sup_df)

    row_errors: dict = {}
    for tab_name, df in annotated.items():
        error_col = df["_SCAFFOLD_Error"]
        flagged = df[error_col.astype(str).str.strip() != ""]
        error_rows = []
        for idx, row in flagged.iterrows():
            # Build a readable summary of the row
            row_summary = {}
            for col in df.columns:
                if col == "_SCAFFOLD_Error":
                    continue
                val = row[col]
                if pd.isna(val):
                    row_summary[col] = None
                else:
                    row_summary[col] = val
                    # Convert numpy types to native Python
                    if hasattr(val, "item"):
                        row_summary[col] = val.item()
            error_rows.append({
                "row_index": int(idx),
                "error": row["_SCAFFOLD_Error"],
                "data": row_summary,
            })
        row_errors[tab_name] = {
            "total_rows": len(df),
            "error_count": len(error_rows),
            "errors": error_rows,
        }
        if error_rows:
            print(f"  {tab_name}: {len(error_rows)} row(s) with errors")
            for er in error_rows:
                print(f"    Row {er['row_index']}: {er['error']}")

    results["row_level_errors"] = row_errors

    # ── 3. Graph Analysis (L1-04, L1-05, L1-06) ──────────
    print("\n--- Graph Analysis ---")

    # Build graph from the (possibly broken) BOM
    # Filter out rows with NaN in required columns to avoid crash
    bom_clean = bom_df.dropna(
        subset=["AssemblyName", "AssemblySite", "ComponentName", "ComponentSite"]
    ).copy()
    G = build_digraph(bom_clean)
    print(f"  Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # Cycle detection (L1-05)
    cycles = detect_cycles(G)
    cycle_strs = []
    for c in cycles:
        cycle_strs.append([f"{part}@{site}" for part, site in c])
    print(f"  Cycles: {len(cycles)} detected")
    for cs in cycle_strs:
        print(f"    {' -> '.join(cs)} -> {cs[0]}")

    # Orphan detection (L1-06)
    pm_nodes = set()
    for _, row in pm_df.iterrows():
        pn = row["PartNumber"]
        site = row["Site"]
        if pd.notna(pn) and pd.notna(site) and str(pn).strip() and str(site).strip():
            pm_nodes.add((str(pn).strip(), str(site).strip()))

    orphans = detect_orphans(G, pm_nodes)
    bom_not_in_parts = [
        f"{p}@{s}" for p, s in sorted(orphans["bom_not_in_parts"])
    ]
    parts_not_in_bom = [
        f"{p}@{s}" for p, s in sorted(orphans["parts_not_in_bom"])
    ]
    print(f"  BOM refs not in Part Master: {len(bom_not_in_parts)}")
    for o in bom_not_in_parts:
        print(f"    {o}")
    print(f"  Part Master entries not in BOM: {len(parts_not_in_bom)}")
    for o in parts_not_in_bom:
        print(f"    {o}")

    results["graph_analysis"] = {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "cycles": {
            "count": len(cycles),
            "details": cycle_strs,
        },
        "orphans": {
            "bom_not_in_parts": bom_not_in_parts,
            "parts_not_in_bom": parts_not_in_bom,
        },
    }

    # ── 4. Risk Findings (L1-09, L1-13) ──────────────────
    print("\n--- Risk Findings ---")

    max_lt = compute_max_leadtime(sup_df)
    single_source = sorted(detect_single_source(sup_df))

    # Parts with LeadTime <= 0 in supplier map (already flagged, but show in risk)
    bad_lt_parts = sorted(
        sup_df[sup_df["LeadTime"] <= 0]["Part"].unique().tolist()
    )

    print(f"  Single-source parts ({len(single_source)}):")
    for p in single_source:
        print(f"    {p} (max LT: {max_lt.get(p, 'N/A')} days)")
    print(f"  Parts with invalid LeadTime: {bad_lt_parts}")
    print(f"  Highest lead time: {max(max_lt.values())} days "
          f"({max(max_lt, key=max_lt.get)})")

    results["risk_findings"] = {
        "max_lead_times": {k: int(v) for k, v in max_lt.items()},
        "single_source_parts": single_source,
        "single_source_count": len(single_source),
        "invalid_leadtime_parts": bad_lt_parts,
        "highest_lt_part": max(max_lt, key=max_lt.get),
        "highest_lt_value": int(max(max_lt.values())),
    }

    # ── 5. Error Summary ─────────────────────────────────
    total_schema = len(all_errors)
    total_row = sum(v["error_count"] for v in row_errors.values())
    total_graph = len(cycles) + len(bom_not_in_parts) + len(parts_not_in_bom)
    total_risk = len(single_source) + len(bad_lt_parts)

    results["error_summary"] = {
        "schema_validation_errors": total_schema,
        "row_level_errors": total_row,
        "graph_structural_issues": total_graph,
        "risk_warnings": total_risk,
        "total_issues": total_schema + total_row + total_graph + total_risk,
        "categories": {
            "blank_fields": "Part Master has rows with blank PartNumber and blank Site",
            "invalid_quantities": "BOM has rows with Qty <= 0",
            "blank_references": "BOM has blank AssemblyName and ComponentName entries",
            "invalid_leadtimes": "Supplier Map has LeadTime <= 0 (ROTOR, STATOR)",
            "subgroup_integrity": "UsageShare does not sum to 1.0 (ALT-SEAL); missing UsageShare (ALT-SHAFT)",
            "circular_bom": "Cycle: SEAL-KIT@PLANT-A -> ROTOR@PLANT-A -> STATOR@PLANT-A -> SEAL-KIT@PLANT-A",
            "orphan_nodes": "BOM references parts not in Part Master (CASTING-RAW); Part Master has unused entries (ORPHAN-PART)",
            "single_source_risk": "Multiple parts have only one supplier",
        },
    }

    # ── 6. Write annotated output CSVs (simulates validated.xlsx) ──
    print("\n--- Writing annotated output CSVs ---")
    output_dir = out_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    tab_filenames = {
        "Part Master": "validated_part_master.csv",
        "BOM Structure": "validated_bom_structure.csv",
        "Supplier Map": "validated_supplier_map.csv",
    }
    for tab_name, df in annotated.items():
        fname = tab_filenames[tab_name]
        fpath = output_dir / fname
        df.to_csv(fpath, index=False)
        err_count = (df["_SCAFFOLD_Error"].astype(str).str.strip() != "").sum()
        print(f"  {fname}: {len(df)} rows, {err_count} with errors")

    # ── Write results ─────────────────────────────────────
    output_path = out_dir / "sample_results.json"
    output_path.write_text(
        json.dumps(results, indent=2, default=str, ensure_ascii=False)
    )
    print(f"\n=== Sample results written ===")
    print(f"    {output_path}")
    for fname in tab_filenames.values():
        print(f"    {output_dir / fname}")
    print(f"    Total issues found: {results['error_summary']['total_issues']}")


if __name__ == "__main__":
    main()
