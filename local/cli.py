#!/usr/bin/env python3
"""SCAFFOLD Local Tool — Command-line interface.

Portable, offline-first pipeline:
    CSV/Excel → Validate → Risk Engine → Dual Ledger (upload.json + key.scaf)

Usage:
    python -m local.cli --pm parts.csv --bom bom.csv --sup suppliers.csv \\
                        --password MY_PASSWORD --output-dir output/

All processing happens locally. No network calls. No data leaves your machine.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="scaffold",
        description="SCAFFOLD — Supply chain structure audit tool (offline)",
    )
    parser.add_argument(
        "--pm",
        required=True,
        help="Path to Part Master CSV file",
    )
    parser.add_argument(
        "--bom",
        required=True,
        help="Path to BOM Structure CSV file",
    )
    parser.add_argument(
        "--sup",
        required=True,
        help="Path to Supplier Map CSV file",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Password for key.scaf encryption (Heavy tier only)",
    )
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Output directory (default: output/)",
    )
    parser.add_argument(
        "--skip-key",
        action="store_true",
        help="Skip key.scaf generation (Light tier)",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate inputs, do not generate outputs",
    )
    args = parser.parse_args()

    import pandas as pd
    import orjson

    from local.core.graph import build_digraph, detect_cycles, detect_orphans
    from local.core.validation import (
        validate_bom,
        validate_part_master,
        validate_supplier_map,
        validate_usage_share,
    )
    from local.core.output import (
        generate_key_data,
        generate_key_scaf,
        generate_upload_json,
    )
    from local.reports.reports import (
        generate_network_summary,
        timestamped_filename,
    )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Read CSV inputs ──────────────────────────
    print("[1/6] Reading input files...")
    pm_df = pd.read_csv(args.pm)
    pm_df["IsEndProduct"] = pm_df["IsEndProduct"].apply(
        lambda v: v if isinstance(v, bool) else str(v).upper() == "TRUE"
    )
    bom_df = pd.read_csv(args.bom)
    sup_df = pd.read_csv(args.sup)
    print(
        f"      Part Master: {len(pm_df)} rows | "
        f"BOM: {len(bom_df)} edges | "
        f"Suppliers: {len(sup_df)} rows"
    )

    # ── Step 2: Validate schema ──────────────────────────
    print("[2/6] Validating schema...")
    errors = []
    errors.extend(validate_part_master(pm_df))
    errors.extend(validate_bom(bom_df))
    errors.extend(validate_supplier_map(sup_df))
    errors.extend(validate_usage_share(bom_df))

    if errors:
        print(f"      FAILED — {len(errors)} validation errors:")
        for e in errors:
            print(f"        - {e}")
        sys.exit(1)
    print("      PASSED — all checks OK")

    if args.validate_only:
        print("\n      --validate-only: stopping here.")
        sys.exit(0)

    # ── Step 3: Build graph ──────────────────────────────
    print("[3/6] Building BOM graph...")
    G = build_digraph(bom_df)
    print(f"      {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    cycles = detect_cycles(G)
    if cycles:
        print(f"      WARNING: {len(cycles)} circular references detected!")
        for c in cycles[:3]:
            print(f"        {c}")

    pm_nodes = {
        (row["PartNumber"], row["Site"]) for _, row in pm_df.iterrows()
    }
    orphans = detect_orphans(G, pm_nodes)
    bom_only = orphans["bom_not_in_parts"]
    if bom_only:
        print(f"      WARNING: {len(bom_only)} BOM refs not in Part Master")

    end_products = set()
    for _, row in pm_df[pm_df["IsEndProduct"]].iterrows():
        end_products.add((row["PartNumber"], row["Site"]))
    print(f"      {len(end_products)} end products")

    # ── Step 4: Generate network summary ─────────────────
    print("[4/6] Computing risk metrics & network summary...")
    summary = generate_network_summary(G, pm_df, end_products, sup_df)
    summary_path = out_dir / timestamped_filename("summary", "txt")
    lines = [f"{k}: {v}" for k, v in summary.items()]
    summary_path.write_text("\n".join(lines))
    print(f"      Written: {summary_path}")
    for k, v in summary.items():
        print(f"        {k}: {v}")

    # ── Step 5: Generate upload.json ─────────────────────
    print("[5/6] Generating upload.json (masked)...")
    upload_data = generate_upload_json(G, pm_df, sup_df, end_products)
    upload_path = out_dir / "upload.json"
    upload_path.write_bytes(
        orjson.dumps(upload_data, option=orjson.OPT_INDENT_2)
    )
    print(f"      Written: {upload_path} ({upload_path.stat().st_size:,} bytes)")

    # ── Step 6: Generate key.scaf ────────────────────────
    if args.skip_key:
        print("[6/6] Skipping key.scaf (--skip-key)")
    elif not args.password:
        print("[6/6] Skipping key.scaf (no --password provided)")
    else:
        print("[6/6] Generating key.scaf (encrypted restore key)...")
        key_data = generate_key_data(G, pm_df, sup_df)
        key_bytes = generate_key_scaf(key_data, password=args.password)
        key_path = out_dir / "key.scaf"
        key_path.write_bytes(key_bytes)
        print(f"      Written: {key_path} ({key_path.stat().st_size:,} bytes)")

    # ── Done ─────────────────────────────────────────────
    print()
    print("=== SCAFFOLD pipeline complete ===")
    print(f"    Output directory: {out_dir}/")


if __name__ == "__main__":
    main()
