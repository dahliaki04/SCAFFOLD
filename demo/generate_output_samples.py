#!/usr/bin/env python3
"""Generate local client output samples from the semiconductor demo data.

Usage:
    python demo/generate_output_samples.py [--output-dir DIR]

Produces human-readable sample outputs that demonstrate every file the
Local Tool generates:

    output_samples/
        network_summary.json       — L1-24: Network summary statistics
        audit_report_data.json     — L1-27: Structured data for PDF report
        part_source_proposal.csv   — L1-25: PartSource proposal (consultant review)
        validated_part_master.csv  — L1-22: Part Master with _SCAFFOLD_Error column
        validated_bom_structure.csv— L1-22: BOM with _SCAFFOLD_Error column
        validated_supplier_map.csv — L1-22: Supplier Map with _SCAFFOLD_Error column

These files show what the Local Tool produces *before* masking — the
standalone-value outputs a consultant receives without needing the SaaS.
For masked outputs (upload.json, key.scaf), see the parent demo/ directory.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from local.core.graph import build_digraph
from local.core.risk import (
    compute_max_leadtime,
    compute_paths,
    detect_single_source,
    extract_pattern,
    group_by_pattern,
)
from local.reports.reports import (
    generate_audit_report_data,
    generate_network_summary,
    generate_part_source_proposal,
    validate_and_annotate,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate SCAFFOLD local client output samples"
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).parent / "output_samples"),
        help="Output directory (default: demo/output_samples/)",
    )
    args = parser.parse_args()

    demo_dir = Path(__file__).parent
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Read CSV data ---
    print("Reading semiconductor demo data...")
    pm_df = pd.read_csv(demo_dir / "part_master.csv")
    pm_df["IsEndProduct"] = pm_df["IsEndProduct"].apply(
        lambda v: v if isinstance(v, bool) else str(v).upper() == "TRUE"
    )
    bom_df = pd.read_csv(demo_dir / "bom_structure.csv")
    sup_df = pd.read_csv(demo_dir / "supplier_map.csv")

    print(f"  {pm_df['PartNumber'].nunique()} parts, {pm_df['Site'].nunique()} sites")
    print(f"  {len(bom_df)} BOM edges, {len(sup_df)} supplier rows")

    # --- Build graph ---
    print("Building BOM graph...")
    G = build_digraph(bom_df)
    print(f"  {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # --- Identify end products ---
    end_products = set()
    for _, row in pm_df[pm_df["IsEndProduct"]].iterrows():
        end_products.add((row["PartNumber"], row["Site"]))
    print(f"  {len(end_products)} end products")

    # ================================================================
    # 1. Validated Excel tabs (L1-22) — output as CSV for readability
    # ================================================================
    print("\n--- Generating validated output (L1-22) ---")
    annotated = validate_and_annotate(pm_df, bom_df, sup_df)

    for tab_name, df in annotated.items():
        filename = f"validated_{tab_name.lower().replace(' ', '_')}.csv"
        filepath = out_dir / filename
        df.to_csv(filepath, index=False)
        error_count = (df["_SCAFFOLD_Error"].astype(str).str.strip() != "").sum()
        print(f"  {filepath.name}: {len(df)} rows, {error_count} errors")

    # ================================================================
    # 2. Network Summary (L1-24)
    # ================================================================
    print("\n--- Generating network summary (L1-24) ---")
    summary = generate_network_summary(G, pm_df, end_products, sup_df)
    summary_path = out_dir / "network_summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, default=str, ensure_ascii=False)
    )
    print(f"  {summary_path.name}: {summary['nodes']} nodes, "
          f"{summary['edges']} edges, depth {summary['max_depth']}")

    # ================================================================
    # 3. PartSource Proposal (L1-25)
    # ================================================================
    print("\n--- Generating PartSource proposal (L1-25) ---")
    proposal_df = generate_part_source_proposal(G, sup_df)
    proposal_path = out_dir / "part_source_proposal.csv"
    proposal_df.to_csv(proposal_path, index=False)
    make_count = (proposal_df["Activity"] == "Make").sum()
    buy_count = (proposal_df["Activity"] == "Buy").sum()
    transfer_count = (proposal_df["Activity"] == "Transfer").sum()
    single_src = proposal_df["SingleSource"].sum()
    print(f"  {proposal_path.name}: {len(proposal_df)} rows "
          f"(Make={make_count}, Buy={buy_count}, Transfer={transfer_count})")
    print(f"  Single-source entries: {single_src}")

    # ================================================================
    # 4. Audit Report Data (L1-27 — structured data before PDF render)
    # ================================================================
    print("\n--- Generating audit report data (L1-27) ---")
    report_data = generate_audit_report_data(summary, annotated)
    report_path = out_dir / "audit_report_data.json"
    report_path.write_text(
        json.dumps(report_data, indent=2, default=str, ensure_ascii=False)
    )
    print(f"  {report_path.name}: {len(report_data['findings'])} findings")

    # --- Summary ---
    print()
    print("=== Output samples ready ===")
    print(f"  Directory: {out_dir}")
    for f in sorted(out_dir.iterdir()):
        print(f"    {f.name:40s} ({f.stat().st_size:,} bytes)")
    print()
    print("These files demonstrate what the Local Tool produces:")
    print("  - validated_*.csv        In-place validation (red cells in Excel)")
    print("  - network_summary.json   BOM structure statistics")
    print("  - part_source_proposal.csv  Consultant review sheet")
    print("  - audit_report_data.json Structured data for PDF rendering")
    print()
    print("For masked outputs, see the parent demo/ directory:")
    print("  - upload.json            Masked data for SaaS upload")
    print("  - key.scaf               Encrypted restore key (password: scaffold-demo)")


if __name__ == "__main__":
    main()
