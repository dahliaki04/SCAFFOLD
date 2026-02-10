#!/usr/bin/env python3
"""Generate semiconductor demo files: upload.json + key.scaf.

Usage:
    python demo/generate_demo.py [--password PASSWORD] [--output-dir DIR]

Produces two files that demonstrate the full SCAFFOLD workflow:
    upload.json — masked data for the SaaS viewer
    key.scaf    — encrypted restore key (password default: "scaffold-demo")

Users can:
1. Upload upload.json to the SaaS viewer to see the masked graph
2. Drag-drop key.scaf and enter the password to unmask real labels
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from local.core.graph import build_digraph
from local.core.output import (
    generate_key_data,
    generate_key_scaf,
    generate_upload_json,
)

import orjson


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate SCAFFOLD semiconductor demo files"
    )
    parser.add_argument(
        "--password",
        default="scaffold-demo",
        help="Password for key.scaf encryption (default: scaffold-demo)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).parent),
        help="Output directory (default: demo/)",
    )
    args = parser.parse_args()

    demo_dir = Path(__file__).parent
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- Read CSV data ---
    print("Reading semiconductor BOM data...")
    pm_df = pd.read_csv(demo_dir / "part_master.csv")
    pm_df["IsEndProduct"] = pm_df["IsEndProduct"].apply(
        lambda v: v if isinstance(v, bool) else str(v).upper() == "TRUE"
    )
    bom_df = pd.read_csv(demo_dir / "bom_structure.csv")
    sup_df = pd.read_csv(demo_dir / "supplier_map.csv")

    parts = pm_df["PartNumber"].nunique()
    sites = pm_df["Site"].nunique()
    stages = pm_df["Stage"].nunique()
    print(f"  {parts} unique parts, {sites} sites, {stages} stages")
    print(f"  {len(bom_df)} BOM edges, {len(sup_df)} supplier rows")

    # --- Build graph ---
    print("Building BOM graph...")
    G = build_digraph(bom_df)
    print(f"  {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # --- Identify end products ---
    end_products = set()
    for _, row in pm_df[pm_df["IsEndProduct"]].iterrows():
        end_products.add((row["PartNumber"], row["Site"]))
    print(f"  {len(end_products)} end products: {[ep[0] for ep in end_products]}")

    # --- Generate upload.json (masked) ---
    print("Generating upload.json (masked)...")
    upload_data = generate_upload_json(G, pm_df, sup_df, end_products)
    upload_path = out_dir / "upload.json"
    upload_path.write_bytes(orjson.dumps(upload_data, option=orjson.OPT_INDENT_2))
    print(f"  Written: {upload_path} ({upload_path.stat().st_size:,} bytes)")

    # --- Generate key.scaf (encrypted restore key) ---
    print(f"Generating key.scaf (password: {args.password})...")
    key_data = generate_key_data(G, pm_df, sup_df)
    key_bytes = generate_key_scaf(key_data, password=args.password)
    key_path = out_dir / "key.scaf"
    key_path.write_bytes(key_bytes)
    print(f"  Written: {key_path} ({key_path.stat().st_size:,} bytes)")

    # --- Summary ---
    print()
    print("=== Demo files ready ===")
    print(f"  upload.json : {upload_path}")
    print(f"  key.scaf    : {key_path}")
    print()
    print("To try the demo:")
    print("  1. Open the SCAFFOLD SaaS viewer in your browser")
    print("  2. Drop upload.json into the viewer")
    print("  3. Explore the masked semiconductor BOM graph")
    print("  4. Drop key.scaf and enter password: scaffold-demo")
    print("  5. Real part names, sites, and stages are restored!")
    print()
    print("Semiconductor stages visible after unmask:")
    for masked, real in sorted(key_data["stages"].items()):
        print(f"    {masked} → {real}")


if __name__ == "__main__":
    main()
