#!/usr/bin/env python3
"""Generate demo diff data for L2-19 BOM comparison feature.

Scenario: "6 months later — Product line refresh"
  Baseline: Current demo BOM (6 end products, semiconductor supply chain)
  Target:   Modified BOM after strategic changes:
    - NEW: IC-5NM-AI accelerator product added (new product line)
    - REMOVED: IC-28NM-IOT discontinued (end-of-life)
    - MODIFIED: GPU line lead times changed (new supplier partnership)
    - MODIFIED: Some edge quantities adjusted (volume ramp)
    - NEW site: FAB-KR (new Korean fab for 5nm AI chip)

Uses the same SHA-256 hashing as the real SCAFFOLD pipeline (L1-16).
"""

import copy
import hashlib
import json
import os
import sys


def sha256_hash(value: str) -> str:
    """Match local/masking/hasher.py exactly."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def node_hash(part: str, site: str) -> str:
    """Match output.py _node_hash exactly."""
    return sha256_hash(f"{part}:{site}")


def site_hash(site: str) -> str:
    return sha256_hash(site)


def main():
    demo_dir = os.path.dirname(os.path.abspath(__file__))
    upload_path = os.path.join(demo_dir, "upload.json")

    with open(upload_path, "r") as f:
        baseline = json.load(f)

    # Deep copy for target modifications
    target = copy.deepcopy(baseline)
    target["meta"]["generated"] = "2026-08-11T00:41:26.981220+00:00"

    # ─────────────────────────────────────────────────────
    # Identify nodes to REMOVE (IC-28NM-IOT product line)
    # ─────────────────────────────────────────────────────
    iot_parts = [
        ("IC-28NM-IOT", "DC-EU"),
        ("IC-28NM-IOT", "FT-SG"),
        ("IC-28NM-IOT", "OSAT-CN"),
        ("TESTED-DIE-IOT", "OSAT-CN"),
        ("TESTED-DIE-IOT", "FAB-US"),
        ("WAFER-IOT", "FAB-US"),
        ("PHOTOMASK-IOT", "FAB-US"),
        # IOT-unique parts only (DFN leadframe, bond wire Cu, epoxy)
        ("DFN-LEADFRAME", "OSAT-CN"),
        ("BOND-WIRE-CU", "OSAT-CN"),
        ("EPOXY-COMPOUND", "OSAT-CN"),
    ]
    iot_hashes = {node_hash(p, s) for p, s in iot_parts}
    iot_ep_hash = node_hash("IC-28NM-IOT", "DC-EU")

    # Remove IOT nodes
    for h in iot_hashes:
        target["nodes"].pop(h, None)
        target["risk"].pop(h, None)

    # Remove IOT edges
    target["edges"] = [
        e for e in target["edges"]
        if e["parent"] not in iot_hashes and e["child"] not in iot_hashes
    ]

    # Remove IOT paths
    target["paths"].pop(iot_ep_hash, None)

    # Clean up patterns that reference the IOT product
    for pid, pat in list(target["patterns"].items()):
        pat["products"] = [p for p in pat["products"] if p != iot_ep_hash]
        if not pat["products"]:
            del target["patterns"][pid]

    # Clean up suppliers: remove IOT-only supplied nodes
    for sup_hash, sup_info in list(target["suppliers"].items()):
        sup_info["supplied_nodes"] = [
            n for n in sup_info["supplied_nodes"] if n not in iot_hashes
        ]
        sup_info["affected_products"] = [
            p for p in sup_info["affected_products"] if p != iot_ep_hash
        ]
        sup_info["impact_count"] = len(sup_info["affected_products"])
        # Don't remove suppliers entirely — they may still supply other lines

    # ─────────────────────────────────────────────────────
    # ADD new product: IC-5NM-AI (AI accelerator)
    # New site: FAB-KR for advanced 5nm fabrication
    # ─────────────────────────────────────────────────────
    fab_kr_hash = site_hash("FAB-KR")
    dc_us_hash = site_hash("DC-US")
    ft_sg_hash = site_hash("FT-SG")
    osat_my_hash = site_hash("OSAT-MY")
    bump_tw_hash = site_hash("BUMP-TW")

    # Stage mapping from the existing data:
    # S1 = Assembly, S2 = Bumping, S3 = Circuit Probe, S4 = Distribution,
    # S5 = Fabrication, S6 = Final Test

    new_parts = [
        # (part, site, stage, lt, depth)
        ("IC-5NM-AI", "DC-US", "S4", 0, 0),          # End product at DC
        ("IC-5NM-AI", "FT-SG", "S6", 0, 1),          # Final test
        ("IC-5NM-AI", "OSAT-MY", "S1", 0, 2),         # Assembly
        ("BUMPED-DIE-AI", "OSAT-MY", "S1", 0, 3),     # Assembly
        ("BUMPED-DIE-AI", "BUMP-TW", "S2", 0, 4),     # Bumping
        ("TESTED-DIE-AI", "BUMP-TW", "S2", 0, 5),     # Bumping (transfer)
        ("TESTED-DIE-AI", "FAB-KR", "S3", 0, 6),      # Circuit Probe — NEW FAB!
        ("WAFER-AI", "FAB-KR", "S5", 0, 7),           # Fabrication
        ("PHOTOMASK-AI", "FAB-KR", "S5", 48, 8),      # New EUV mask
        ("AI-INTERPOSER", "OSAT-MY", "S1", 22, 3),    # CoWoS interposer
        ("HBM-STACK", "OSAT-MY", "S1", 35, 3),        # HBM memory stack
    ]

    site_map = {
        "DC-US": dc_us_hash,
        "FT-SG": ft_sg_hash,
        "OSAT-MY": osat_my_hash,
        "BUMP-TW": bump_tw_hash,
        "FAB-KR": fab_kr_hash,
    }

    for part, site, stage, lt, depth in new_parts:
        h = node_hash(part, site)
        target["nodes"][h] = {
            "stage": stage,
            "lt": lt,
            "depth": depth,
            "site": site_map[site],
        }
        target["risk"][h] = {
            "max_lt": lt,
            "single_source": part in ("PHOTOMASK-AI", "HBM-STACK"),  # new critical
            "depth": depth,
        }

    # New edges for IC-5NM-AI supply chain
    new_edges = [
        # Transfer: DC-US ← FT-SG
        ("IC-5NM-AI", "DC-US", "IC-5NM-AI", "FT-SG", 1),
        # Transfer: FT-SG ← OSAT-MY
        ("IC-5NM-AI", "FT-SG", "IC-5NM-AI", "OSAT-MY", 1),
        # Assembly: OSAT-MY ← children
        ("IC-5NM-AI", "OSAT-MY", "BUMPED-DIE-AI", "OSAT-MY", 1),
        ("IC-5NM-AI", "OSAT-MY", "AI-INTERPOSER", "OSAT-MY", 1),
        ("IC-5NM-AI", "OSAT-MY", "HBM-STACK", "OSAT-MY", 4),
        # Transfer: BUMPED-DIE-AI OSAT-MY ← BUMP-TW
        ("BUMPED-DIE-AI", "OSAT-MY", "BUMPED-DIE-AI", "BUMP-TW", 1),
        # Assembly: BUMP-TW
        ("BUMPED-DIE-AI", "BUMP-TW", "TESTED-DIE-AI", "BUMP-TW", 1),
        # Reuse existing SOLDER-BUMP from bumping
        ("BUMPED-DIE-AI", "BUMP-TW", "SOLDER-BUMP", "BUMP-TW", 6000),
        # Transfer: TESTED-DIE-AI BUMP-TW ← FAB-KR
        ("TESTED-DIE-AI", "BUMP-TW", "TESTED-DIE-AI", "FAB-KR", 1),
        # Assembly: FAB-KR
        ("TESTED-DIE-AI", "FAB-KR", "WAFER-AI", "FAB-KR", 1),
        ("WAFER-AI", "FAB-KR", "PHOTOMASK-AI", "FAB-KR", 1),
        # Reuse SILICON-INGOT (but at new site FAB-KR — would need new node)
        # Test equipment reuse
        ("IC-5NM-AI", "FT-SG", "TEST-SOCKET-ADV", "FT-SG", 1),
        ("IC-5NM-AI", "FT-SG", "MARKING-INK", "FT-SG", 1),
    ]

    for ap, as_, cp, cs, qty in new_edges:
        target["edges"].append({
            "parent": node_hash(ap, as_),
            "child": node_hash(cp, cs),
            "qty": qty,
        })

    # New paths for IC-5NM-AI
    ai_ep_hash = node_hash("IC-5NM-AI", "DC-US")
    target["paths"][ai_ep_hash] = [
        [
            node_hash("IC-5NM-AI", "DC-US"),
            node_hash("IC-5NM-AI", "FT-SG"),
            node_hash("IC-5NM-AI", "OSAT-MY"),
            node_hash("BUMPED-DIE-AI", "OSAT-MY"),
            node_hash("BUMPED-DIE-AI", "BUMP-TW"),
            node_hash("TESTED-DIE-AI", "BUMP-TW"),
            node_hash("TESTED-DIE-AI", "FAB-KR"),
            node_hash("WAFER-AI", "FAB-KR"),
            node_hash("PHOTOMASK-AI", "FAB-KR"),
        ],
    ]

    # New supplier entries for AI parts
    new_suppliers = {
        "SAMSUNG-FAB": {
            "parts": [("WAFER-AI", "FAB-KR")],
            "impact": [ai_ep_hash],
        },
        "ASML-LITHO": {
            "parts": [("PHOTOMASK-AI", "FAB-KR")],
            "impact": [ai_ep_hash],
        },
        "SK-HYNIX": {
            "parts": [("HBM-STACK", "OSAT-MY")],
            "impact": [ai_ep_hash],
        },
    }

    for sup_name, info in new_suppliers.items():
        sup_hash = sha256_hash(sup_name)
        supplied = [node_hash(p, s) for p, s in info["parts"]]
        if sup_hash in target["suppliers"]:
            # Existing supplier — append
            target["suppliers"][sup_hash]["supplied_nodes"].extend(supplied)
            target["suppliers"][sup_hash]["affected_products"].extend(info["impact"])
            target["suppliers"][sup_hash]["impact_count"] = len(
                set(target["suppliers"][sup_hash]["affected_products"])
            )
        else:
            target["suppliers"][sup_hash] = {
                "supplied_nodes": supplied,
                "affected_products": info["impact"],
                "impact_count": len(info["impact"]),
            }

    # ─────────────────────────────────────────────────────
    # MODIFY existing nodes (GPU line lead time changes)
    # ─────────────────────────────────────────────────────

    # GPU interposer: lead time increased (supply constraint)
    gpu_interposer_hash = node_hash("GPU-INTERPOSER", "OSAT-MY")
    if gpu_interposer_hash in target["nodes"]:
        target["nodes"][gpu_interposer_hash]["lt"] = 30  # was ~25
    if gpu_interposer_hash in target["risk"]:
        target["risk"][gpu_interposer_hash]["max_lt"] = 30

    # GPU underfill: lead time decreased (dual-sourced now)
    gpu_underfill_hash = node_hash("GPU-UNDERFILL", "OSAT-MY")
    if gpu_underfill_hash in target["nodes"]:
        target["nodes"][gpu_underfill_hash]["lt"] = 5  # was ~7
    if gpu_underfill_hash in target["risk"]:
        target["risk"][gpu_underfill_hash]["max_lt"] = 5

    # PHOTOMASK-EUV: longer lead time (capacity crunch)
    pm_euv_hash = node_hash("PHOTOMASK-EUV", "FAB-TW")
    if pm_euv_hash in target["nodes"]:
        target["nodes"][pm_euv_hash]["lt"] = 62  # was ~55
    if pm_euv_hash in target["risk"]:
        target["risk"][pm_euv_hash]["max_lt"] = 62

    # MICROBUMP qty change: 8000 → 10000 (higher density design)
    for edge in target["edges"]:
        if (edge["parent"] == node_hash("BUMPED-DIE-GPU", "BUMP-TW")
            and edge["child"] == node_hash("MICROBUMP", "BUMP-TW")):
            edge["qty"] = 10000

    # PHOTORESIST qty change at FAB-TW for GPU: 4 → 5 (more layers)
    for edge in target["edges"]:
        if (edge["parent"] == node_hash("WAFER-GPU", "FAB-TW")
            and edge["child"] == node_hash("PHOTORESIST", "FAB-TW")):
            edge["qty"] = 5

    # ─────────────────────────────────────────────────────
    # Write output files
    # ─────────────────────────────────────────────────────
    baseline_path = os.path.join(demo_dir, "diff_baseline.json")
    target_path = os.path.join(demo_dir, "diff_target.json")

    with open(baseline_path, "w") as f:
        json.dump(baseline, f, indent=2)
    print(f"Wrote {baseline_path}")
    print(f"  Nodes: {len(baseline['nodes'])}, Edges: {len(baseline['edges'])}, Products: {len(baseline['paths'])}")

    with open(target_path, "w") as f:
        json.dump(target, f, indent=2)
    print(f"Wrote {target_path}")
    print(f"  Nodes: {len(target['nodes'])}, Edges: {len(target['edges'])}, Products: {len(target['paths'])}")

    # Quick diff summary
    b_nodes = set(baseline["nodes"].keys())
    t_nodes = set(target["nodes"].keys())
    added = t_nodes - b_nodes
    removed = b_nodes - t_nodes
    common = b_nodes & t_nodes
    modified = 0
    for h in common:
        bn = baseline["nodes"][h]
        tn = target["nodes"][h]
        if bn["lt"] != tn["lt"] or bn["depth"] != tn["depth"] or bn["stage"] != tn["stage"]:
            modified += 1

    print(f"\nDiff summary:")
    print(f"  Added:     {len(added)} nodes (IC-5NM-AI product line)")
    print(f"  Removed:   {len(removed)} nodes (IC-28NM-IOT discontinued)")
    print(f"  Modified:  {modified} nodes (lead time / attribute changes)")
    print(f"  Unchanged: {len(common) - modified} nodes")


if __name__ == "__main__":
    main()
