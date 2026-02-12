#!/usr/bin/env python3
"""Generate demo diff data for L2-19 BOM comparison feature.

Scenario 1: "GPU line technology upgrade"
  Baseline: Current demo BOM (6 end products, semiconductor supply chain)
  Target:   Modified BOM after mid-path component swap:
    - REMOVED: GPU-INTERPOSER@OSAT-MY replaced by new CoWoS bridge technology
    - ADDED:   COWOS-BRIDGE@OSAT-MY (next-gen interposer replacement)
    - MODIFIED: GPU-UNDERFILL lead time decreased (dual-sourced now)
    - MODIFIED: PHOTOMASK-EUV lead time increased (capacity crunch)
    - MODIFIED: MICROBUMP qty increased (higher density design)
    - MODIFIED: PHOTORESIST qty increased (more layers)

Scenario 2: "MOD-WIFI-6 assembly relocates OSAT-MY → OSAT-CN (re-shoring)"
  Product site switch with local sourcing at the new site:
    - REMOVED: MOD-WIFI-6@OSAT-MY and all OSAT-MY component nodes
              (DIE-WIFI, DIE-BT, FILTER-BAW, AIP-SUBSTRATE)
    - REMOVED: All edges from OSAT-MY assembly flow
    - ADDED:   MOD-WIFI-6@OSAT-CN (new assembly point)
    - ADDED:   Re-sourced components at OSAT-CN (DIE-WIFI, DIE-BT,
              FILTER-BAW, AIP-SUBSTRATE)
    - ADDED:   EMI-SHIELD@OSAT-CN (extra local sourcing — new component
              required for CN regulatory compliance, not in original BOM)
    - ADDED:   New local suppliers (BROADCOM-CN, ESPRESSIF, MURATA-CN,
              SHENNAN-CIRCUITS, LAIRD-CN)

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
    # REMOVE mid-path component: GPU-INTERPOSER@OSAT-MY
    # (Replaced by CoWoS bridge technology — see ADD section)
    # ─────────────────────────────────────────────────────
    old_interposer_hash = node_hash("GPU-INTERPOSER", "OSAT-MY")

    # Remove the node
    target["nodes"].pop(old_interposer_hash, None)
    target["risk"].pop(old_interposer_hash, None)

    # Remove edges referencing the old interposer
    target["edges"] = [
        e for e in target["edges"]
        if e["parent"] != old_interposer_hash and e["child"] != old_interposer_hash
    ]

    # Update paths: replace old interposer hash with new one in GPU paths
    gpu_ep_hash = node_hash("IC-7NM-GPU", "DC-US")
    new_bridge_hash = node_hash("COWOS-BRIDGE", "OSAT-MY")

    if gpu_ep_hash in target["paths"]:
        updated_paths = []
        for path in target["paths"][gpu_ep_hash]:
            updated_path = [
                new_bridge_hash if h == old_interposer_hash else h
                for h in path
            ]
            updated_paths.append(updated_path)
        target["paths"][gpu_ep_hash] = updated_paths

    # Clean up suppliers: replace old interposer references
    for sup_hash, sup_info in target["suppliers"].items():
        sup_info["supplied_nodes"] = [
            new_bridge_hash if n == old_interposer_hash else n
            for n in sup_info["supplied_nodes"]
        ]

    # ─────────────────────────────────────────────────────
    # ADD replacement: COWOS-BRIDGE@OSAT-MY
    # (Next-gen CoWoS bridge replaces traditional interposer)
    # ─────────────────────────────────────────────────────
    osat_my_hash = site_hash("OSAT-MY")

    # Get the old interposer's attributes from baseline for reference
    old_attrs = baseline["nodes"].get(old_interposer_hash, {})
    old_depth = old_attrs.get("depth", 3)
    old_stage = old_attrs.get("stage", "S1")

    # New node: same depth/stage as old interposer, but longer lead time
    # (new technology = higher lead time initially)
    target["nodes"][new_bridge_hash] = {
        "stage": old_stage,
        "lt": 32,       # higher than old ~25, new tech supply chain
        "depth": old_depth,
        "site": osat_my_hash,
    }
    target["risk"][new_bridge_hash] = {
        "max_lt": 32,
        "single_source": True,  # new tech, only one qualified supplier
        "depth": old_depth,
    }

    # Re-add the edge: GPU assembly at OSAT-MY → COWOS-BRIDGE
    gpu_osat_hash = node_hash("IC-7NM-GPU", "OSAT-MY")
    target["edges"].append({
        "parent": gpu_osat_hash,
        "child": new_bridge_hash,
        "qty": 1,
    })

    # Add supplier for the new CoWoS bridge
    cowos_sup_hash = sha256_hash("TSMC-COWOS")
    target["suppliers"][cowos_sup_hash] = {
        "supplied_nodes": [new_bridge_hash],
        "affected_products": [gpu_ep_hash],
        "impact_count": 1,
    }

    # ─────────────────────────────────────────────────────
    # MODIFY existing nodes (GPU line lead time changes)
    # ─────────────────────────────────────────────────────

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
    # CASE 2: Site switch — MOD-WIFI-6 assembly OSAT-MY → OSAT-CN
    # (Re-shoring: relocate assembly, add extra local sourcing)
    # ─────────────────────────────────────────────────────

    # --- Hashes for existing MOD-WIFI-6 nodes at OSAT-MY ---
    wifi_ep_hash = node_hash("MOD-WIFI-6", "DC-US")
    wifi_ft_hash = node_hash("MOD-WIFI-6", "FT-SG")
    wifi_osat_my_hash = node_hash("MOD-WIFI-6", "OSAT-MY")
    die_wifi_my_hash = node_hash("DIE-WIFI", "OSAT-MY")
    die_bt_my_hash = node_hash("DIE-BT", "OSAT-MY")
    filter_baw_my_hash = node_hash("FILTER-BAW", "OSAT-MY")
    aip_sub_my_hash = node_hash("AIP-SUBSTRATE", "OSAT-MY")

    # --- Hashes for new nodes at OSAT-CN ---
    wifi_osat_cn_hash = node_hash("MOD-WIFI-6", "OSAT-CN")
    die_wifi_cn_hash = node_hash("DIE-WIFI", "OSAT-CN")
    die_bt_cn_hash = node_hash("DIE-BT", "OSAT-CN")
    filter_baw_cn_hash = node_hash("FILTER-BAW", "OSAT-CN")
    aip_sub_cn_hash = node_hash("AIP-SUBSTRATE", "OSAT-CN")
    emi_shield_cn_hash = node_hash("EMI-SHIELD", "OSAT-CN")

    osat_cn_site_hash = site_hash("OSAT-CN")

    # --- REMOVE: Old OSAT-MY assembly flow ---
    # All 5 nodes are exclusive to MOD-WIFI-6 at OSAT-MY
    removed_my_hashes = {
        wifi_osat_my_hash, die_wifi_my_hash, die_bt_my_hash,
        filter_baw_my_hash, aip_sub_my_hash,
    }
    for h in removed_my_hashes:
        target["nodes"].pop(h, None)
        target["risk"].pop(h, None)

    # Remove all edges referencing the old OSAT-MY nodes
    target["edges"] = [
        e for e in target["edges"]
        if e["parent"] not in removed_my_hashes
        and e["child"] not in removed_my_hashes
    ]

    # --- ADD: New assembly point at OSAT-CN ---
    target["nodes"][wifi_osat_cn_hash] = {
        "stage": "S1", "lt": 0, "depth": 2, "site": osat_cn_site_hash,
    }
    target["risk"][wifi_osat_cn_hash] = {
        "max_lt": 0, "single_source": False, "depth": 2,
    }

    # --- ADD: Re-sourced components at OSAT-CN ---
    # DIE-WIFI: local distributor, slightly shorter LT than MY (was ~56)
    target["nodes"][die_wifi_cn_hash] = {
        "stage": "S1", "lt": 48, "depth": 3, "site": osat_cn_site_hash,
    }
    target["risk"][die_wifi_cn_hash] = {
        "max_lt": 48, "single_source": False, "depth": 3,
    }

    # DIE-BT: local alternative (Espressif) — resolves single-source risk!
    target["nodes"][die_bt_cn_hash] = {
        "stage": "S1", "lt": 22, "depth": 3, "site": osat_cn_site_hash,
    }
    target["risk"][die_bt_cn_hash] = {
        "max_lt": 22, "single_source": False, "depth": 3,
    }

    # FILTER-BAW: local sourcing
    target["nodes"][filter_baw_cn_hash] = {
        "stage": "S1", "lt": 20, "depth": 3, "site": osat_cn_site_hash,
    }
    target["risk"][filter_baw_cn_hash] = {
        "max_lt": 20, "single_source": False, "depth": 3,
    }

    # AIP-SUBSTRATE: local PCB manufacturer (single source initially)
    target["nodes"][aip_sub_cn_hash] = {
        "stage": "S1", "lt": 30, "depth": 3, "site": osat_cn_site_hash,
    }
    target["risk"][aip_sub_cn_hash] = {
        "max_lt": 30, "single_source": True, "depth": 3,
    }

    # EMI-SHIELD: extra local sourcing — new component for CN compliance
    # (not in baseline BOM at all — required at OSAT-CN only)
    target["nodes"][emi_shield_cn_hash] = {
        "stage": "S1", "lt": 12, "depth": 3, "site": osat_cn_site_hash,
    }
    target["risk"][emi_shield_cn_hash] = {
        "max_lt": 12, "single_source": True, "depth": 3,
    }

    # --- ADD: New edges at OSAT-CN ---
    # Transfer: FT-SG → OSAT-CN (replaces FT-SG → OSAT-MY)
    target["edges"].append({
        "parent": wifi_ft_hash, "child": wifi_osat_cn_hash, "qty": 2,
    })
    # Assembly: OSAT-CN → components
    target["edges"].append({
        "parent": wifi_osat_cn_hash, "child": die_wifi_cn_hash, "qty": 4,
    })
    target["edges"].append({
        "parent": wifi_osat_cn_hash, "child": die_bt_cn_hash, "qty": 3,
    })
    target["edges"].append({
        "parent": wifi_osat_cn_hash, "child": filter_baw_cn_hash, "qty": 3,
    })
    target["edges"].append({
        "parent": wifi_osat_cn_hash, "child": aip_sub_cn_hash, "qty": 2,
    })
    target["edges"].append({
        "parent": wifi_osat_cn_hash, "child": emi_shield_cn_hash, "qty": 1,
    })

    # --- UPDATE: Paths for MOD-WIFI-6 ---
    if wifi_ep_hash in target["paths"]:
        # Keep paths that don't go through old OSAT-MY, remove ones that do
        new_paths = [
            path for path in target["paths"][wifi_ep_hash]
            if wifi_osat_my_hash not in path
        ]
        # Add new paths through OSAT-CN (including EMI-SHIELD — new)
        for leaf_hash in [die_wifi_cn_hash, die_bt_cn_hash,
                          filter_baw_cn_hash, aip_sub_cn_hash,
                          emi_shield_cn_hash]:
            new_paths.append([
                wifi_ep_hash, wifi_ft_hash, wifi_osat_cn_hash, leaf_hash,
            ])
        target["paths"][wifi_ep_hash] = new_paths

    # --- UPDATE: Suppliers ---
    # Remove old OSAT-MY node references from existing suppliers
    for sup_hash, sup_info in target["suppliers"].items():
        sup_info["supplied_nodes"] = [
            n for n in sup_info["supplied_nodes"]
            if n not in removed_my_hashes
        ]

    # Clean up suppliers left with empty supplied_nodes
    target["suppliers"] = {
        k: v for k, v in target["suppliers"].items()
        if v["supplied_nodes"]
    }

    # Add new local suppliers for OSAT-CN components
    target["suppliers"][sha256_hash("BROADCOM-CN")] = {
        "supplied_nodes": [die_wifi_cn_hash],
        "affected_products": [wifi_ep_hash],
        "impact_count": 1,
    }
    target["suppliers"][sha256_hash("ESPRESSIF")] = {
        "supplied_nodes": [die_bt_cn_hash],
        "affected_products": [wifi_ep_hash],
        "impact_count": 1,
    }
    target["suppliers"][sha256_hash("MURATA-CN")] = {
        "supplied_nodes": [filter_baw_cn_hash],
        "affected_products": [wifi_ep_hash],
        "impact_count": 1,
    }
    target["suppliers"][sha256_hash("SHENNAN-CIRCUITS")] = {
        "supplied_nodes": [aip_sub_cn_hash],
        "affected_products": [wifi_ep_hash],
        "impact_count": 1,
    }
    target["suppliers"][sha256_hash("LAIRD-CN")] = {
        "supplied_nodes": [emi_shield_cn_hash],
        "affected_products": [wifi_ep_hash],
        "impact_count": 1,
    }

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
    print(f"  Added:     {len(added)} node(s)")
    print(f"  Removed:   {len(removed)} node(s)")
    print(f"  Modified:  {modified} node(s)")
    print(f"  Unchanged: {len(common) - modified} node(s)")
    print(f"  Products:  {len(baseline['paths'])} → {len(target['paths'])} (no change)")
    print(f"\nCase 1 — GPU tech upgrade:")
    print(f"  GPU-INTERPOSER@OSAT-MY removed → COWOS-BRIDGE@OSAT-MY added")
    print(f"  GPU-UNDERFILL LT decreased, PHOTOMASK-EUV LT increased")
    print(f"\nCase 2 — MOD-WIFI-6 site switch (OSAT-MY → OSAT-CN):")
    print(f"  5 nodes removed (OSAT-MY assembly flow)")
    print(f"  6 nodes added (OSAT-CN assembly + EMI-SHIELD extra sourcing)")


if __name__ == "__main__":
    main()
