# SCAFFOLD Demo Data

Semiconductor supply chain BOM data (6 end products, 71 parts, 8 sites, 59 suppliers) demonstrating the full SCAFFOLD pipeline from raw input through masked output.

---

## Demo Input Data

Three CSV files matching the V4 schema that users prepare:

### `part_master.csv` (71 rows)

Defines nodes in the supply chain graph.

| Column | Description | Example |
|--------|-------------|---------|
| PartNumber | Unique part identifier | `IC-7NM-SOC` |
| Site | Manufacturing/distribution site | `FAB-TW` |
| Stage | Supply chain stage | `Fabrication` |
| IsEndProduct | Demand entry point flag | `TRUE` / `FALSE` |

**End products**: IC-7NM-SOC, IC-28NM-MCU, MOD-5G-RF, IC-7NM-GPU, IC-28NM-IOT, MOD-WIFI-6

**Sites** (8): FAB-TW, FAB-US, BUMP-TW, OSAT-MY, OSAT-CN, FT-SG, DC-US, DC-EU

**Stages** (6): Fabrication, Circuit Probe, Bumping, Assembly, Final Test, Distribution

### `bom_structure.csv` (81 edges)

Defines parent-child relationships (assembly + transfer edges).

| Column | Description | Example |
|--------|-------------|---------|
| AssemblyName | Parent part | `IC-7NM-SOC` |
| AssemblySite | Parent site | `OSAT-MY` |
| ComponentName | Child part | `BUMPED-DIE-7NM` |
| ComponentSite | Child site | `OSAT-MY` |
| Qty | Quantity per assembly | `1` |
| SubGroup | Alternate group (optional) | `SG-001` |
| UsageShare | Share within SubGroup (optional) | `0.6` |

**Edge types**:
- Assembly: parent.Part != child.Part (e.g., `IC-7NM-SOC@OSAT-MY -> BUMPED-DIE-7NM@OSAT-MY`)
- Transfer: parent.Part = child.Part, different sites (e.g., `IC-7NM-SOC@DC-US -> IC-7NM-SOC@FT-SG`)

### `supplier_map.csv` (59 rows)

Maps parts to external suppliers with lead times.

| Column | Description | Example |
|--------|-------------|---------|
| Part | Part identifier | `SILICON-INGOT` |
| Supplier | Supplier name | `SUMCO` |
| LeadTime | Lead time in days | `30` |

**Max LT rule**: same part, multiple suppliers -> take max LT as risk value.
Example: SILICON-INGOT has 3 suppliers (SUMCO:30d, SHIN-ETSU:28d, SILTRONIC:35d) -> max LT = 35 days.

---

## Local Client Output Samples

Located in `output_samples/`. These demonstrate what the Local Tool produces **before masking** -- the standalone-value outputs a consultant receives without needing the SaaS platform.

### `output_samples/network_summary.json` (L1-24)

BOM structure statistics at a glance:

```json
{
  "nodes": 70,
  "edges": 80,
  "sites": ["BUMP-TW", "DC-EU", "DC-US", "FAB-TW", "FAB-US", "FT-SG", "OSAT-CN", "OSAT-MY"],
  "site_count": 8,
  "end_products": 6,
  "depths": {
    "IC-7NM-SOC@DC-US": 9,
    "IC-7NM-GPU@DC-US": 9,
    "IC-28NM-MCU@DC-EU": 7,
    "IC-28NM-IOT@DC-EU": 7,
    "MOD-5G-RF@DC-US": 4,
    "MOD-WIFI-6@DC-US": 4
  },
  "max_depth": 9,
  "patterns": 3,
  "leaves": 36,
  "roots": 6,
  "transfer_edges": 18,
  "single_source_parts": 14,
  "highest_lt_part": "DIE-RF-BOUGHT",
  "highest_lt_value": 60
}
```

### `output_samples/validated_*.csv` (L1-22)

In-place validation results. Each input tab is copied with an appended `_SCAFFOLD_Error` column. In the real `validated.xlsx`, error cells are highlighted red.

Files:
- `validated_part_master.csv` -- 70 rows, 0 errors (clean demo data)
- `validated_bom_structure.csv` -- 80 rows, 0 errors
- `validated_supplier_map.csv` -- 57 rows, 0 errors

For **error examples**, see `sample_errors/sample_results.json` which demonstrates every error category on intentionally broken data.

### `output_samples/part_source_proposal.csv` (L1-25)

PartSource proposal for consultant review. Each row is a part+supplier combination with BOM-derived activity type and blank `Approved` / `Notes` columns for consultant decisions.

| Column | Description | Example |
|--------|-------------|---------|
| PartNumber | Part identifier | `SILICON-INGOT` |
| Site | Site | `FAB-TW` |
| Activity | BOM-derived: Make / Buy / Transfer | `Buy` |
| Supplier | Supplier name (blank for Make/Transfer) | `SUMCO` |
| LeadTime | Supplier lead time | `30` |
| MaxLeadTime | Max LT across all suppliers for this part | `35` |
| SupplierCount | Number of suppliers | `3` |
| SingleSource | True if only 1 supplier | `False` |
| Approved | Consultant checkbox (blank) | |
| Notes | Consultant notes (blank) | |

Summary: 96 rows (Make=22, Buy=62, Transfer=12), 14 single-source entries.

### `output_samples/audit_report_data.json` (L1-27)

Structured data that feeds into the PDF audit report. Contains the network summary, validation error counts, and key findings:

```json
{
  "title": "SCAFFOLD Structure Audit Report",
  "generated": "2026-02-11T...",
  "summary": { ... },
  "validation_errors": {
    "Part Master": "0",
    "BOM Structure": "0",
    "Supplier Map": "0"
  },
  "total_errors": "0",
  "findings": [
    "All input data passed validation with zero errors.",
    "14 part(s) have only one supplier (single source risk).",
    "18 inter-site transfer edge(s) detected in BOM.",
    "Deepest BOM path: 9 levels."
  ]
}
```

---

## Masked Output (Dual-Ledger)

Located in the parent `demo/` directory. These are the privacy-preserving outputs generated after the full masking pipeline.

### `upload.json` (93 KB) -- L1-19

Masked plaintext JSON safe for SaaS upload. Contains:

| Section | Contents | Privacy |
|---------|----------|---------|
| `meta` | Version, timestamp | Plaintext |
| `nodes` | 70 nodes with stage, lead time, depth, site | Names: SHA-256 hashed. Stages: S1-S6. Values: jittered +/-15% |
| `edges` | 80 parent-child edges with quantity | Hash-to-hash references. Qty jittered |
| `paths` | DFS paths from each end product to leaves | Hash sequences |
| `patterns` | Site-sequence patterns grouping similar products | Hashed site sequences |
| `risk` | Max LT, single-source flag, depth per node | Values jittered |
| `suppliers` | Supplier impact analysis (supplied nodes, affected products) | All hashes |

**Zero human-readable business terms** -- all part names, site names, and supplier names are SHA-256 hashed; stages are replaced with S1/S2/...; numeric values have non-zero jitter applied.

### `key.scaf` (7.8 KB) -- L1-20

AES-encrypted restore key. **Never leaves the client machine.**

- Binary format: `MAGIC(b'SCAF') + VERSION(3) + SALT(16B) + Fernet_token`
- Encrypted with PBKDF2-HMAC-SHA256 (1.2M iterations)
- Demo password: `scaffold-demo`
- Contains: hash-to-real-name mappings, stage labels (S1=Fabrication, etc.), real lead times, supplier names

---

## Error Showcase

Located in `sample_errors/`. Intentionally broken input data demonstrating every error category.

### `sample_errors/sample_results.json`

Validation results from the broken data showing 36 total issues:

| Category | Count | Examples |
|----------|-------|---------|
| Blank fields | 2 | Blank PartNumber, blank Site |
| Invalid quantities | 2 | Qty=0, Qty=-1 |
| Blank references | 2 | Blank AssemblyName, blank ComponentName |
| Invalid lead times | 2 | LeadTime=0, LeadTime=-2 |
| SubGroup integrity | 2 | UsageShare sums to 0.90, missing UsageShare |
| Circular BOM | 1 | SEAL-KIT -> ROTOR -> STATOR -> SEAL-KIT |
| Orphan nodes | 3 | BOM refs not in Part Master, Part Master not in BOM |
| Single-source risk | 11 | Multiple parts with only one supplier |

---

## Regenerating Demo Files

```bash
# Regenerate masked outputs (upload.json + key.scaf)
python demo/generate_demo.py --password scaffold-demo

# Regenerate local client output samples
python demo/generate_output_samples.py

# Regenerate error showcase results
python demo/generate_sample_results.py
```

---

## Quick Start

1. Review the **input data** (`part_master.csv`, `bom_structure.csv`, `supplier_map.csv`) to understand what users prepare
2. Review the **output samples** (`output_samples/`) to see standalone local value
3. Open `upload.json` in a text editor to see what masked data looks like
4. Upload `upload.json` to the SaaS viewer, then drag-drop `key.scaf` with password `scaffold-demo` to unmask
