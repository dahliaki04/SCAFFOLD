#!/usr/bin/env python3
"""SCAFFOLD Local Tool — Command-line interface.

Portable, offline-first pipeline:
    CSV/Excel → Validate → Risk Engine → Dual Ledger (upload.json + key.scaf)

Usage (CSV — three separate files):
    python -m local.cli --pm parts.csv --bom bom.csv --sup suppliers.csv \\
                        --password MY_PASSWORD --output-dir output/

Usage (Excel — single workbook with Part Master / BOM Structure / Supplier Map tabs):
    python -m local.cli --input data.xlsx --password MY_PASSWORD --output-dir output/

All processing happens locally. No network calls. No data leaves your machine.
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime


def _read_inputs(args: argparse.Namespace):
    """Read input data from either a single Excel workbook or three CSVs.

    L1-07: Multi-format Input — supports .xlsx (via xlwings) and .csv.
    """
    import pandas as pd

    if args.input:
        input_path = Path(args.input)
        ext = input_path.suffix.lower()
        if ext in (".xlsx", ".xls"):
            from local.core.reader import (
                read_part_master,
                read_bom,
                read_supplier_map,
            )
            pm_df = read_part_master(input_path)
            bom_df = read_bom(input_path)
            sup_df = read_supplier_map(input_path)
        elif ext == ".csv":
            raise SystemExit(
                "ERROR: --input with .csv requires three separate files. "
                "Use --pm, --bom, --sup instead."
            )
        else:
            raise SystemExit(f"ERROR: Unsupported input format: {ext}")
    else:
        pm_df = pd.read_csv(args.pm)
        bom_df = pd.read_csv(args.bom)
        sup_df = pd.read_csv(args.sup)

    # Normalize IsEndProduct to bool
    pm_df["IsEndProduct"] = pm_df["IsEndProduct"].apply(
        lambda v: v if isinstance(v, bool) else str(v).upper() == "TRUE"
    )
    # Coerce identity columns (PartName/Site/etc.) to string so node tuples
    # match across tabs regardless of how each cell was typed in Excel.
    from local.core.reader import normalize_input_dtypes
    pm_df, bom_df, sup_df = normalize_input_dtypes(pm_df, bom_df, sup_df)
    return pm_df, bom_df, sup_df


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="scaffold",
        description="SCAFFOLD — Supply chain structure audit tool (offline)",
    )
    # L1-07: Multi-format input — single Excel workbook OR three CSVs
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--input",
        help="Path to Excel workbook (.xlsx) with Part Master / BOM Structure / Supplier Map tabs",
    )
    input_group.add_argument(
        "--pm",
        help="Path to Part Master CSV file",
    )
    parser.add_argument(
        "--bom",
        help="Path to BOM Structure CSV file (required with --pm)",
    )
    parser.add_argument(
        "--sup",
        help="Path to Supplier Map CSV file (required with --pm)",
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
    parser.add_argument(
        "--license-key",
        default=None,
        help="License key string (SCAF-<TIER>-...) for tier gating",
    )
    parser.add_argument(
        "--export-kinaxis",
        action="store_true",
        help="Export Kinaxis V7 RapidResponse CSV",
    )
    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Export generic CSV",
    )
    args = parser.parse_args()

    # Validate that CSV mode has all three files
    if args.pm and (not args.bom or not args.sup):
        parser.error("--pm requires --bom and --sup")

    import pandas as pd
    import orjson

    from local.core.graph import build_digraph, detect_cycles, detect_orphans
    from local.core.validation import (
        validate_bom,
        validate_end_products_have_bom,
        validate_part_master,
        validate_supplier_map,
        validate_usage_share,
    )
    from local.core.output import (
        generate_key_data,
        generate_key_scaf,
        generate_upload_json,
    )
    from local.core.licensing import verify_license, TIER_FREE
    from local.reports.reports import (
        generate_network_summary,
        timestamped_filename,
    )

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 0: Verify license ────────────────────────────
    tier = TIER_FREE
    if args.license_key:
        tier_result = verify_license(args.license_key)
        if tier_result is None:
            print("WARNING: Invalid license key — falling back to Free tier")
        else:
            tier = tier_result
            print(f"License verified: {tier} tier")

    # ── Step 1: Read inputs ───────────────────────────────
    print("[1/6] Reading input files...")
    pm_df, bom_df, sup_df = _read_inputs(args)
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

    # L1-39 follow-up: orphan end products (declared in Part Master but with
    # no BOM entry as parent) are a *warning*, not a blocking error. Demand
    # sites separated from production sites (e.g. demand at 9999, production
    # at 1522 with no explicit transfer edge) is a valid real-world pattern.
    # compute_paths() guards against the underlying crash; we surface the
    # situation here so the user knows which end products won't appear in
    # path stats.
    warnings_ep = validate_end_products_have_bom(pm_df, bom_df)

    if errors:
        print(f"      FAILED — {len(errors)} validation errors:")
        for e in errors:
            print(f"        - {e}")
        sys.exit(1)
    print("      PASSED — all checks OK")

    for w in warnings_ep:
        print(f"      WARNING: {w}")
    if warnings_ep:
        print(
            "      (Orphan end products are skipped in path computation; "
            "the pipeline continues with partial results.)"
        )

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

    # ── L1-31: Free Tier Gate ────────────────────────────
    from local.core.licensing import TIER_FREE, TIER_LIGHT, TIER_HEAVY, check_free_tier_limits

    if tier == TIER_FREE:
        limit_error = check_free_tier_limits(pm_df, bom_df)
        if limit_error:
            print(f"      FREE TIER LIMIT: {limit_error}")
            print("      Upgrade to Light/Heavy tier for unlimited processing.")
            print("      Free tier outputs: validated.xlsx + report.pdf only.")
            # Free tier still gets validation + summary, but no upload.json/key.scaf
            print()
            print("=== SCAFFOLD pipeline complete (Free tier) ===")
            print(f"    Output directory: {out_dir}/")
            sys.exit(0)

    # ── Step 5: Generate upload.json ─────────────────────
    if tier == TIER_FREE:
        print("[5/6] Skipping upload.json (Free tier)")
    else:
        print("[5/6] Generating upload.json (masked)...")
        upload_data = generate_upload_json(G, pm_df, sup_df, end_products)
        # Embed tier signature if licensed
        if args.license_key and tier != TIER_FREE:
            from local.core.licensing import extract_tier_sig
            tier_sig = extract_tier_sig(args.license_key)
            if tier_sig:
                upload_data["meta"]["tier"] = tier
                upload_data["meta"]["tier_sig"] = tier_sig
        upload_path = out_dir / "upload.json"
        upload_path.write_bytes(
            orjson.dumps(upload_data, option=orjson.OPT_INDENT_2)
        )
        print(f"      Written: {upload_path} ({upload_path.stat().st_size:,} bytes)")

    # ── Step 6: Generate key.scaf ────────────────────────
    if tier not in (TIER_HEAVY,):
        print("[6/6] Skipping key.scaf (requires Heavy tier)")
    elif args.skip_key:
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

    # ── Export Plugins (L1-28 / L1-29) ───────────────────
    if args.export_kinaxis:
        print("Exporting Kinaxis V7 RapidResponse CSV...")
        from local.export.kinaxis_v7 import export_kinaxis_v7
        k_path = out_dir / timestamped_filename("kinaxis_v7", "csv")
        export_kinaxis_v7(G, pm_df, sup_df, bom_df, k_path)
        print(f"      Written: {k_path}")

    if args.export_csv:
        print("Exporting generic CSV...")
        from local.export.csv_export import export_generic_csv
        c_path = out_dir / timestamped_filename("export", "csv")
        export_generic_csv(G, pm_df, sup_df, bom_df, c_path)
        print(f"      Written: {c_path}")

    # ── Done ─────────────────────────────────────────────
    print()
    print("=== SCAFFOLD pipeline complete ===")
    print(f"    Output directory: {out_dir}/")
    print(f"    Tier: {tier}")


if __name__ == "__main__":
    main()
