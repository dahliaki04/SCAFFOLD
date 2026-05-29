# CLAUDE.md — SCAFFOLD

> Spec Version: 3.0 (Frozen) | Feature Plan: 72 features (49 P0 / 11 P1 / 12 P2)
> Codename: SCAFFOLD (鷹架) — supports, then removes itself

## Product Identity

SCAFFOLD is a **BOM transparency and visualization platform** — making supply chain structure visible without requiring large SCM systems. Consultants and planners feed customer BOM data (from Excel, CSV, or system exports) into a Local Tool (Python desktop), which validates structural integrity, computes risk metrics, anonymizes data, and outputs files that can optionally be uploaded to a SaaS platform (React web) for interactive visualization and editable report generation.

- **Repository**: `dahliaki04/SCAFFOLD`
- **License**: AGPL-3.0
- **Market**: Any manufacturer with BOMs — especially those without enterprise SCM/PLM
- **Philosophy**: Murphy's Law — the weakest link in the structure is the inherent risk
- **Design Principle**: Survivor-first — zero trust, offline-first, tools travel with you

## System Architecture

Two-segment disconnected architecture (privacy by design):

```
LOCAL TOOL (Python Desktop)                    SAAS PLATFORM (React Web)
─────────────────────────────                  ────────────────────────
Input → Validate → Risk Engine → Dual Ledger   Graph View (Sigma.js)
  ├ Excel (.xlsx)                               Sankey (D3.js)
  ├ CSV (.csv)                                  Diff Overlay
  └ System Export (ERP/MRP/PLM)                 Client-side Restore (key.scaf)
                                                PPT Export
Outputs:
  upload.json    → to SaaS (plaintext, masked)
  key.scaf       → stays local (AES-256)
  validated.xlsx → standalone value
  report.pdf     → standalone value
```

- `upload.json` is the **only file uploaded** — plaintext JSON, all values masked
- `key.scaf` **never leaves the client** — AES-256 encrypted, password protected
- Local Tool is fully functional offline (validated.xlsx + report.pdf have independent value)

## Development Roadmap

### Sprint Plan (8 weeks total)

| Sprint | Duration | Focus | P0 Count | Deliverable |
|--------|----------|-------|----------|-------------|
| S1 | 2 weeks | Local Core (`transformer.py`) | 16 | CLI: Input → upload.json + key.scaf |
| S2 | 2 weeks | Local Reports (`local_reports.py`) | 7 | validated.xlsx + reports (standalone value) |
| S3 | 2 weeks | SaaS MVP | 18 | Sigma.js Graph + Sankey + key restore |
| S4 | 2 weeks | Package & Ship | 8 | GUI + export + tier gate + PPT |

### Sprint 1 — Local Core (16 P0)

Build order: Read → Validate → Risk → Dual Ledger

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| L1-01 | V4 Input Reader | P0 | Read Part Master / BOM / Supplier Map via xlwings (Excel) or pandas (CSV/system export) behind I/O abstraction |
| L1-02 | Schema Validation | P0 | Check required fields, data types, column names |
| L1-03 | SubGroup UsageShare Check | P0 | Validate UsageShare sums to 1.0 per SubGroup |
| L1-04 | NetworkX DiGraph Build | P0 | Batch edge list from BOM, node key = (PartName, SiteID) |
| L1-05 | Circular BOM Detection | P0 | `nx.simple_cycles(G)`, iterative only |
| L1-06 | Orphan Detection | P0 | Set operations O(1): parts not in BOM, BOM refs not in parts |
| L1-08 | Smart Ignore | P0 | Skip `_SCAFFOLD_Error` columns when reading input |
| L1-09 | Max LeadTime Calculation | P0 | Multi-source → take Max(LT) per part as risk value |
| L1-10 | Auto-Activity Assignment | P0 | BOM-derived BUY/MAKE/TRANSFER: Assembly children→Make, same-part cross-site children→Transfer, leaf→Buy |
| L1-11 | Path Fingerprinting (DFS) | P0 | Per FG: iterative DFS → store site sequence |
| L1-12 | Pattern String Grouping | P0 | Pattern as dict key → O(1) grouping of FGs |
| L1-16 | SHA-256 Hasher | P0 | Hash PartName, SiteName, SupplierName |
| L1-17 | Stage Masking (S1/S2/S3...) | P0 | Replace real stage names with sequential IDs |
| L1-18 | Jitter Engine (±15%) | P0 | Noise ≠ 0, floor ±3, max(1, result) |
| L1-19 | upload.json Generator | P0 | SCAFFOLD standard JSON format (plaintext) |
| L1-20 | key.scaf Generator (AES) | P0 | MAGIC=b'SCAF' + zlib + Fernet(PBKDF2(password)) |
| L1-21 | orjson Integration | P0 | Replace stdlib json with orjson for 1M record perf |

### Sprint 2 — Local Reports (7 P0 + 3 P1)

Build order: Reports + Proposals (standalone without SaaS)

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| L1-13 | Single Source Detection | P0 | Flag parts with only one supplier |
| L1-14 | Impact Analysis | P0 | Supplier outage → affected product lines count |
| L1-22 | In-place Excel Validation | P0 | Copy input → mark red cells → add `_SCAFFOLD_Error` column |
| L1-23 | Auto-timestamp Filenames | P0 | Never overwrite: `validated_20260209_143000.xlsx` |
| L1-24 | Network Summary Report | P0 | nodes/edges/depth/sites/patterns statistics |
| L1-25 | PartSource Proposal | P0 | Excel with checkbox for consultant review |
| L1-15 | Site Dependency Map | P1 | Factory relocation → which BOMs need change |
| L1-26 | Proposal Readback | P1 | Re-read consultant's checkbox decisions |
| L1-27 | PDF Structure Report | P1 | Standalone BOM structure transparency report |

### Sprint 3 — SaaS MVP (18 P0 + 2 P1)

Build order: Graph + Sankey + Restore

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| L2-01 | SCAFFOLD JSON Parser | P0 | Read upload.json into standard in-memory object |
| L2-02 | Sigma.js Adapter (toSigma) | P0 | Transform SCAFFOLD JSON → graphology Graph |
| L2-04 | Sigma.js WebGL Renderer | P0 | Initialize Sigma instance with graphology |
| L2-05 | Node Color by Stage | P0 | S1=blue, S2=green, S3=orange... palette |
| L2-06 | Node Size by Risk (Max LT) | P0 | Larger = higher Max LT |
| L2-07 | Lazy Loading (1000 nodes max) | P0 | Default expand 3 levels, click to load more |
| L2-09 | Hover Highlight Neighbors | P0 | Hover node → highlight connected nodes + edges |
| L2-10 | Search Node | P0 | Search bar with autocomplete (by hash or restored name) |
| L2-11 | Filter by Stage | P0 | S1-S6 checkbox, graphology `nodesBy` filter with undo |
| L2-14 | Subgraph View (select FG) | P0 | Click FG → graphology subgraph → focused view |
| L2-15 | Product List Panel | P0 | Right sidebar: list all FG nodes |
| L2-16 | D3.js Sankey Renderer | P0 | d3-sankey for product flow visualization |
| L2-17 | Product Path Sankey | P0 | Select FG → render multi-hop flow from paths data |
| L2-18 | Sankey Stage Labels | P0 | Show S1→S2→S4→S6 (or restored names) |
| L2-23 | key.scaf Drag & Drop | P0 | Drop zone in browser window |
| L2-24 | Password Prompt | P0 | Modal dialog for AES decryption password |
| L2-25 | Client-side AES Decrypt | P0 | Fernet decrypt + zlib decompress in browser JS |
| L2-26 | Live Label Restore | P0 | hash → real name, S1 → WAF, jitter → real value |
| L2-27 | Stage Color Update | P0 | After restore: update color legend with real stage names |
| L2-28 | Key Never Uploaded Guarantee | P0 | No network call when key is loaded (verifiable) |
| L2-08 | Semantic Zoom | P1 | Macro cluster → micro node progressive detail |
| L2-12 | Filter by Site | P1 | Hash checkbox; after restore: shows real site names |
| L2-13 | Filter by Depth | P1 | Slider: show BOM levels 1-N |

### Sprint 4 — Package & Ship (8 P0 + 3 P1)

Build order: GUI + Export + Tier Gate + PPT

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| L1-28 | Kinaxis V7 Export Plugin | P0 | CSV export in RapidResponse V7 format |
| L1-29 | Generic CSV Export Plugin | P0 | Universal CSV export |
| L1-31 | Free Tier Gate | P0 | ≤5 products + ≤2,000 rows check at runtime |
| L1-32 | ttkbootstrap GUI | P0 | Dark mode desktop GUI (darkly theme) |
| L1-33 | PyInstaller Portable Build | P0 | `--onedir` + UPX compression |
| L2-29 | Rasterized PDF Export | P0 | Image-based PDF, anti-OCR (Light tier) |
| L2-31 | Editable PPT Export | P0 | Slide deck with editable text/charts (Heavy tier) |
| L2-32 | RSA Signature Verification | P0 | Digital signature for paid feature gate |
| L1-07 | Multi-format Input (xlsx/csv/system) | P1 | Support .xlsx, .csv, and system export input via I/O abstraction |
| L1-35 | SmartScreen Disclaimer | P1 | First-run warning, save EV cert cost |
| L1-38 | Sample Data + README | P1 | Demo dataset for onboarding |
| L2-30 | Layout Destruction (anti-OCR) | P1 | Micro-offset text positioning |

**PyInstaller build command (L1-33)**:
```
pyinstaller --noconfirm --onedir --windowed \
  --collect-all ttkbootstrap \
  --hidden-import pywin32 \
  --hidden-import pythoncom \
  --hidden-import orjson \
  main.py
```

### Sprint 5 — Post-MVP Additions

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| L1-39 | Auto-SubGroup from Priority | P1 | Optional `Priority` column on BOM Structure; when 2+ children of one parent carry a Priority value, the tool auto-derives a `SubGroup` (`AUTO-SG-{parent}-{site}`) and `UsageShare` (P1=1.0, P2+=0.0, sums to 1.0). Single-source detection (L1-13) is extended to skip parts that have an alternate in any SubGroup (manual or auto). |

**L1-39 details**:
- New module: `local/core/subgroup.py` — `derive_subgroups_from_priority()` and `parts_with_alternates()`
- New validation: `local/core/validation.py:validate_priority()` — positive integers, unique per parent
- Pipeline order: `validate_*` → `derive_subgroups_from_priority` → `build_digraph` → summary/output
- Risk integration: `detect_single_source(supplier_map_df, bom_df)` filters out parts in multi-member SubGroups
- Manual `SubGroup` always wins — never overwritten by auto-derivation
- Tests: `tests/local/test_subgroup.py` (18 cases)

### Phase 2+ (Deferred — 12 P2)

| ID | Feature | Description |
|----|---------|-------------|
| L1-30 | SAP IBP Export Plugin | Future plugin |
| L1-34 | xlwings Add-in Mode | Excel Add-in as IT bypass |
| L1-36 | Zero Network Calls Verify | Automated test: no outbound connections |
| L1-37 | 250k Synthetic Stress Test | Benchmark script for perf budget |
| L2-03 | Cosmograph Adapter (toCosmo) | For 250k+ full view |
| L2-19 | Upload Two JSONs | Baseline + Target upload |
| L2-20 | Diff Overlay (blue vs orange) | Superimposed graph comparison |
| L2-21 | Delta Metrics (ΔDepth, ΔRisk) | Quantified structural differences |
| L2-22 | New/Deleted Node Highlight | Green = added, Red = removed |
| L2-33 | SaaS UI Polish | UX refinement (sidebar, search) |
| L2-34 | Responsive Layout | Mobile/tablet support |

### Feature Count Summary

| Layer | Total | P0 | P1 | P2 |
|-------|-------|----|----|-----|
| Layer 1: Local Tool | 38 | 25 | 6 | 7 |
| Layer 2: SaaS Platform | 34 | 24 | 5 | 5 |
| **Total** | **72** | **49** | **11** | **12** |

## Tech Stack (Phase 1 — Locked)

**Runtime: Python 3.12.x** (binding constraint: networkx >=3.6 requires Python >=3.11)

### Local Tool (Python) — see `requirements.txt`

| Component | Library | Version | Constraint |
|-----------|---------|---------|------------|
| Excel I/O | `xlwings` | 0.33.20 | **NOT openpyxl** — xlwings required for Add-in mode + cell formatting |
| Data processing | `pandas` | 2.3.3 | Stay on 2.x — pandas 3.0 string dtype breaks xlwings |
| Graph engine | `networkx` | 3.6.1 | DiGraph only. Phase 2: Rust petgraph + PyO3 if > 1M edges |
| JSON I/O | `orjson` | 3.11.7 | **NOT standard json** — Rust-backed, 1M records < 3 sec |
| GUI | `ttkbootstrap` | 1.10.1 | Dark mode (darkly/cyborg/solar themes). Replaces unmaintained customtkinter |
| Encryption | `cryptography` | 46.0.4 | Fernet (AES-128-CBC) for key.scaf + RSA for PPT license |
| Hashing | `hashlib` | stdlib | SHA-256 for node masking |
| Packaging | `PyInstaller` | 6.18.0 | `--onedir` portable folder |

### SaaS Platform (React) — see `package.json`

| Component | Library | Version |
|-----------|---------|---------|
| Graph rendering | `sigma` + `graphology` | 3.0.2 / 0.26.0 |
| React bindings | `@react-sigma/core` | 5.0.6 |
| Sankey diagrams | `d3` + `d3-sankey` | 7.9.0 / 0.12.3 |
| Frontend framework | `react` | 19.2.4 |
| zlib (browser) | `pako` | 2.1.0 |

### Renderer Adapter Architecture

```
SCAFFOLD JSON → Adapter (toSigma / toCosmo / toCyto) → Renderer
```

Swap rendering engine by changing ~50-line adapter only. Core JSON format and business logic untouched.

### Tech Stack Risks & Gotchas

| Risk | Impact | Mitigation |
|------|--------|------------|
| **xlwings requires Excel COM** | Won't run on Linux / headless CI | Isolate xlwings behind I/O layer; test core logic on Linux, xlwings I/O on Windows CI runner only |
| **pandas 3.0 breaks xlwings** | String dtype change (`object` → `str`) breaks xlwings converters | Pin pandas 2.3.3; do not upgrade without retesting all xlwings DataFrame ops |
| **ttkbootstrap themes.json bundling** | PyInstaller may miss `themes.json` resource | Use `--collect-all ttkbootstrap` in PyInstaller command |
| **Fernet = AES-128-CBC, not AES-256** | Spec says "AES-256" but Fernet splits 32-byte key into 16B signing + 16B encryption | Acceptable security for this use case; document accurately |
| **D3 v7 is ESM-only** | No CommonJS — must use `import` syntax | Vite handles this natively; no special config needed |
| **sigma.js v3 breaking change** | v2 custom Programs API incompatible with v3 | Start on v3 from day one; do not reference v2 examples |
| **PyInstaller bundling** | xlwings needs `--hidden-import pywin32/pythoncom`; ttkbootstrap needs `--collect-all` | See PyInstaller command in S4 notes |

### Fernet Crypto Chain (Python ↔ Browser)

Python Fernet uses: PBKDF2-HMAC-SHA256 → 32-byte key → split into [16B HMAC-SHA256 signing key][16B AES-128-CBC encryption key].

**key.scaf binary format (updated)**:
```
MAGIC (b'SCAF', 4 bytes) + VERSION (uint16 LE, 2 bytes) + SALT (16 bytes) + Fernet token (base64url)
```

**Browser decryption (L2-25)**: Use native Web Crypto API (`crypto.subtle`) — no third-party crypto library needed:
1. Read SALT from key.scaf bytes 6-22
2. `crypto.subtle.deriveBits()` with PBKDF2-HMAC-SHA256, same salt + iterations
3. Parse Fernet token: Version(1B) + Timestamp(8B) + IV(16B) + Ciphertext + HMAC(32B)
4. `crypto.subtle.verify()` HMAC-SHA256 over everything except last 32 bytes
5. `crypto.subtle.decrypt()` AES-128-CBC with IV
6. `pako.inflate()` for zlib decompression
7. `JSON.parse()` the result

**PBKDF2 iterations**: Use 1,200,000 (current `cryptography` library recommendation, up from 480,000).

## Critical Engineering Constraints

These are **non-negotiable** rules. Violating any of these is a bug.

### Graph Engine

```python
# Node key = (PartName, SiteID) tuple — ALWAYS
node = ("WIP-01", "PLANT1")  # ≠ ("WIP-01", "PLANT2")

# Build graph via batch edge list — NEVER iterrows()
# BOM contains both assembly edges and transfer edges (same table)
#   Assembly: FG-001@PLANT1 → WIP-01@PLANT1  (different parts)
#   Transfer: FG-001@DC-01  → FG-001@PLANT1  (same part, different sites)
G = nx.DiGraph()
edges = list(zip(
    zip(bom['AssemblyName'], bom['AssemblySite']),
    zip(bom['ComponentName'], bom['ComponentSite'])
))
G.add_edges_from(edges)

# ALL traversals MUST be iterative (stack/queue) — NO recursion
# Cycle detection: nx.simple_cycles(G)
# Orphan detection: set operations O(1) — NO loops
```

### Masking Protocol (Dual-Ledger)

upload.json must contain **zero human-readable business terms**.

| Field | upload.json | Method |
|-------|------------|--------|
| PartName, SiteName, SupplierName | SHA-256 hash | Hash |
| Stage | S1, S2, S3... | Sequential index (hides industry fingerprint) |
| LeadTime, Qty | Jitter ±15% (≠0, floor ±3) | Noise |
| BOM Topology, Depth | Preserved (plaintext) | Structure alone can't identify |
| Parent-Child | hash → hash | Follows PartName |

```python
# Jitter Engine — noise MUST be non-zero
def apply_jitter(real_val):
    range_val = max(3, int(real_val * 0.15))  # at least ±3 or 15%
    noise = random.choice([i for i in range(-range_val, range_val + 1) if i != 0])
    return max(1, real_val + noise)
```

### key.scaf Binary Format

```python
MAGIC = b'SCAF'
VERSION = 3
# Layout: MAGIC(4B) + version(uint16 LE, 2B) + salt(16B) + Fernet(PBKDF2(password, salt, 1200000)).encrypt(zlib.compress(orjson.dumps(data)))
# SALT must be stored in the file — browser needs it for PBKDF2 derivation
# Fernet internally uses AES-128-CBC + HMAC-SHA256 (not AES-256)
```

### Performance Budget

| Operation | 250k rows | 1M rows |
|-----------|-----------|---------|
| JSON parse (orjson) | < 1s | < 3s |
| Build graph | < 3s | < 5s |
| Cycle detection | < 5s | < 8s |
| Chain walk (all FG) | < 5s | < 8s |
| Pattern extraction | < 2s | < 3s |
| **Total pipeline** | **< 15s** | **< 25s** |

## Data Standard (V4 Schema)

Users prepare data in this format; the Local Tool validates it. Data can come from manual Excel files, CSV exports, or system exports (ERP/MRP/PLM). The schema is the same regardless of input source — the I/O layer normalizes all inputs into the same internal DataFrames.

| Tab | Key Fields | Required | Logic |
|-----|-----------|----------|-------|
| Part Master | PartNumber, Site, IsEndProduct | Required | Defines nodes, sites, and demand entry points |
| BOM Structure | AssemblyName, AssemblySite, ComponentName, ComponentSite, Qty | Required | Defines parent-child edges |
| | SubGroup, UsageShare | Optional | Alternate parts; shares must sum to 1.0 |
| Supplier Map | Part, Supplier, LeadTime | Required | Max Rule: same part, multiple suppliers → take max LT |

### BOM Edge Types

BOM contains two types of edges, both in the same table:

| Edge Type | Condition | Example | Meaning |
|-----------|-----------|---------|---------|
| **Assembly** | Parent.Part ≠ Child.Part | `FG-001@PLANT1 → WIP-01@PLANT1` | Manufacturing relationship |
| **Transfer** | Parent.Part = Child.Part, Parent.Site ≠ Child.Site | `FG-001@DC-01 → FG-001@PLANT1` | Inter-site supply (demand deepening) |

Transfer edges model inter-site supply directly in the graph — no separate Transfer Map tab needed.

### Auto-Activity Assignment (L1-10)

Activity type is derived entirely from BOM edge structure:

```
            Part+Site
                │
                ▼
    ┌───────────────────────────┐
    │ Has children where        │
    │ child.Part ≠ parent.Part? │   ← Assembly children
    └─────────────┬─────────────┘
             YES  │  NO
             ▼    │
          ┌──────┐│
          │ MAKE ││
          └──────┘│
                  ▼
    ┌───────────────────────────┐
    │ Has children where        │
    │ child.Part = parent.Part  │   ← Same part, different site
    │ child.Site ≠ parent.Site? │
    └─────────────┬─────────────┘
             YES  │  NO
             ▼    │
       ┌──────────┐│
       │ TRANSFER ││
       └──────────┘│
                   ▼
               ┌───────┐
               │  BUY  │
               └───────┘
```

```python
# L1-10: Auto-Activity — derived from BOM graph structure
def assign_activity(part, site, G):
    children = list(G.successors((part, site)))
    if not children:
        return "Buy"          # leaf node, purchased from supplier
    has_assembly = any(cp != part for cp, cs in children)
    if has_assembly:
        return "Make"         # has different-part children = manufacturing
    return "Transfer"         # only same-part cross-site children = demand point
```

**Rules summary**:

| # | Condition | Type | SourceID |
|---|-----------|------|----------|
| 1 | Has assembly children (different part) | **Make** | `Internal` |
| 2 | Has only same-part cross-site children | **Transfer** | `{MfgSite} → {DemandSite}` |
| 3 | Leaf node (no children) | **Buy** | `{SupplierID} → {Site}` |

`IsEndProduct` is **not** used for Make/Buy/Transfer assignment — activity is fully BOM-derived.
`IsEndProduct` (boolean on Part Master) marks demand entry points: used by L1-11 Path Fingerprinting as DFS start nodes, and by L1-31 Free Tier Gate to count end products (≤5 in Free tier).

## Demo Input Files

Sample input files for onboarding and testing (L1-38). All demo files live in `samples/`.

### Sample Excel Input (`samples/demo_bom.xlsx`)

Three tabs matching the V4 Schema:

**Tab 1: Part Master**

| PartNumber | Site | IsEndProduct | Stage |
|------------|------|-------------|-------|
| FG-001 | DC-01 | TRUE | Finished Goods |
| FG-001 | PLANT1 | FALSE | Finished Goods |
| WIP-01 | PLANT1 | FALSE | Work In Process |
| WIP-02 | PLANT1 | FALSE | Work In Process |
| RM-01 | PLANT1 | FALSE | Raw Material |
| RM-02 | PLANT2 | FALSE | Raw Material |

**Tab 2: BOM Structure**

| AssemblyName | AssemblySite | ComponentName | ComponentSite | Qty | SubGroup | UsageShare |
|--------------|-------------|---------------|--------------|-----|----------|------------|
| FG-001 | DC-01 | FG-001 | PLANT1 | 1 | | |
| FG-001 | PLANT1 | WIP-01 | PLANT1 | 2 | | |
| FG-001 | PLANT1 | WIP-02 | PLANT1 | 1 | | |
| WIP-01 | PLANT1 | RM-01 | PLANT1 | 3 | GRP-A | 0.6 |
| WIP-01 | PLANT1 | RM-02 | PLANT2 | 3 | GRP-A | 0.4 |

**Tab 3: Supplier Map**

| Part | Supplier | LeadTime |
|------|----------|----------|
| RM-01 | SUP-A | 14 |
| RM-01 | SUP-B | 21 |
| RM-02 | SUP-C | 30 |

### Sample CSV Input (`samples/demo_parts.csv`, `samples/demo_bom.csv`, `samples/demo_suppliers.csv`)

Same schema as the Excel tabs, one CSV per tab. Used for system export workflows.

### Sample System Export (`samples/demo_system_export/`)

Directory containing flat files in a common ERP extract format. The I/O layer normalizes these into the same internal DataFrames as Excel/CSV input.

| File | Maps to | Notes |
|------|---------|-------|
| `items.csv` | Part Master | System field names mapped via config |
| `structures.csv` | BOM Structure | Parent/child relationships |
| `vendors.csv` | Supplier Map | Supplier lead time data |

**Field mapping config** (`samples/demo_system_export/field_map.json`):
```json
{
  "items": { "ITEM_ID": "PartNumber", "FACILITY": "Site", "IS_FG": "IsEndProduct", "CATEGORY": "Stage" },
  "structures": { "PARENT": "AssemblyName", "PARENT_FAC": "AssemblySite", "CHILD": "ComponentName", "CHILD_FAC": "ComponentSite", "QTY_PER": "Qty" },
  "vendors": { "ITEM_ID": "Part", "VENDOR_ID": "Supplier", "LT_DAYS": "LeadTime" }
}
```

## Local Client Output Files

All output files generated by the Local Tool. Files are timestamped (L1-23) and never overwrite previous runs.

### upload.json — Masked Structure File

- **Purpose**: Anonymized BOM structure for SaaS visualization
- **Generated by**: L1-19 (upload.json Generator)
- **Contains**: Zero human-readable business terms — all names hashed, values jittered, stages masked
- **Destination**: Uploaded to SaaS platform (the **only** file that leaves the client)
- **Tier**: Light and Heavy only (Free tier does not generate this file)
- **Filename pattern**: `upload_YYYYMMDD_HHMMSS.json`

```json
{
  "meta": { "version": "3.0", "generated": "ISO-8601", "tier": "Heavy", "tier_sig": "<RSA signature>" },
  "nodes": {
    "hash_id": { "stage": "S4", "lt": 47, "depth": 3, "site": "hash_site" }
  },
  "edges": [
    { "parent": "hash_id", "child": "hash_id2", "qty": 3 }
  ],
  "paths": {
    "hash_fg": ["hash_a", "hash_b", "hash_c"]
  },
  "risk": {
    "hash_id": { "max_lt": 47, "single_source": false, "depth": 3 }
  }
}
```

### key.scaf — Encryption Key File

- **Purpose**: Maps hashed/masked values back to real names and values
- **Generated by**: L1-20 (key.scaf Generator)
- **Contains**: AES-encrypted reverse mapping (hash→real name, S1→real stage, jittered→real value)
- **Destination**: **Never leaves the client** — stays on consultant's machine
- **Tier**: Heavy only
- **Filename pattern**: `key_YYYYMMDD_HHMMSS.scaf`
- **Binary format**: `MAGIC(4B) + VERSION(uint16 LE, 2B) + SALT(16B) + Fernet token`
- **Decryption**: Password-based (PBKDF2, 1,200,000 iterations) — see Fernet Crypto Chain section

### validated.xlsx — Annotated Input Workbook

- **Purpose**: Copy of the original input with validation errors marked in-place
- **Generated by**: L1-22 (In-place Excel Validation)
- **Contains**: Original data + red-highlighted error cells + `_SCAFFOLD_Error` column per tab
- **Destination**: Stays local — standalone deliverable even without SaaS
- **Tier**: All tiers (Free, Light, Heavy)
- **Filename pattern**: `validated_YYYYMMDD_HHMMSS.xlsx`
- **Value**: Consultants can hand this to customers as immediate feedback

### report.pdf — Structure Report

- **Purpose**: Standalone BOM structure transparency report
- **Generated by**: L1-27 (PDF Structure Report)
- **Contains**: Network summary stats, risk metrics, single-source flags, site dependency overview
- **Destination**: Stays local — standalone deliverable
- **Tier**: All tiers (Free, Light, Heavy)
- **Filename pattern**: `report_YYYYMMDD_HHMMSS.pdf`

### Output File Summary

| File | Tier | Leaves Client | Encrypted | Masked | Standalone Value |
|------|------|--------------|-----------|--------|-----------------|
| `validated.xlsx` | All | No | No | No (original data) | Yes |
| `report.pdf` | All | No | No | N/A (summary stats) | Yes |
| `upload.json` | Light+ | Yes (to SaaS) | No | Yes (fully masked) | No (needs SaaS) |
| `key.scaf` | Heavy | **Never** | Yes (AES) | N/A (contains mappings) | No (used with SaaS) |

## Three-Tier Monetization

| Tier | Gate | Local Output | SaaS Output |
|------|------|-------------|-------------|
| Free | ≤5 products + ≤2,000 rows | validated.xlsx + report.pdf | Masked browse only |
| Light | Unlimited | + upload.json | + Rasterized PDF |
| Heavy | Unlimited | + key.scaf | + Editable PPT + Export Plugin |

### Licensing Architecture

**Offline-first RSA license keys** — zero network calls from the Local Tool.

```
Payment (LemonSqueezy) → Webhook → Serverless RSA signer → License key emailed
                                                                    │
                              Customer pastes key once into Local Tool
                                                                    │
                    ┌───────────────────────────────────────────────┤
                    ▼                                               ▼
              Local Tool                                     upload.json
              verifies RSA offline                           carries tier_sig
              gates which files are generated                     │
                                                                  ▼
                                                            SaaS verifies
                                                            tier_sig client-side
                                                            gates exports
```

**License key format** — self-contained RSA-signed string:
```
SCAF-<TIER>-<base64(JSON payload)>.<RSA-SHA256 signature>
Payload: { "tier": "Light|Heavy", "exp": "ISO-8601", "email": "..." }
```

**Tier proof in upload.json** — Local Tool embeds signed tier in output:
```json
{ "meta": { "version": "3.0", "tier": "Heavy", "tier_sig": "<RSA signature>" } }
```

**Gating flow**:
- **Local Tool** (L1-31): checks license → Free blocks upload.json generation; Light blocks key.scaf
- **SaaS** (L2-32): reads `meta.tier_sig` from upload.json → verifies RSA → unlocks exports
- Free users can't upload (no upload.json generated) → SaaS browse is demo/marketing only

**Infrastructure**: One serverless function (~30 lines) auto-signs keys on purchase webhook. Day-one alternative: manual `sign_license.py` script.

## Project Structure

```
SCAFFOLD/
├── local/                  # Local Tool (Python)
│   ├── core/               # Validation, risk engine, graph ops
│   ├── masking/            # Dual-ledger: hasher, jitter, stage masking
│   ├── export/             # Plugin architecture (Kinaxis V7, CSV, SAP IBP)
│   ├── gui/                # ttkbootstrap UI
│   └── reports/            # validated.xlsx, report.pdf generation
├── saas/                   # SaaS Platform (React)
│   ├── adapters/           # Renderer adapters (toSigma, toCosmo, etc.)
│   ├── components/         # Graph, Sankey, Diff, Restore, PPT export
│   └── public/
├── tests/                  # Test suite
│   ├── local/              # Python unit/integration tests
│   └── saas/               # JS/React tests
├── requirements.txt        # Python dependencies (pinned)
├── package.json            # Node dependencies (pinned)
├── CLAUDE.md               # This file
├── README.md
└── LICENSE                 # AGPL-3.0
```

## Development Conventions

### Branching

- Feature branches: `feature/`, `fix/`, `docs/`
- AI-assisted branches: `claude/<description>-<session-id>`

### Commits

- Imperative mood, under 72 characters (e.g., "Add cycle detection to validation pipeline")
- Body for non-trivial changes explaining *why*
- Reference feature IDs when implementing tracked features (e.g., "Implement L1-04: NetworkX DiGraph Build")

### Code Style

- Python: follow PEP 8, type hints encouraged
- JavaScript/React: follow project ESLint config when added
- No recursion in graph traversals — always iterative
- No `iterrows()` — always vectorized or batch operations
- Prefer readability over cleverness

### Security Rules

- Never commit secrets, credentials, or real customer BOM data
- upload.json must never contain human-readable business terms
- key.scaf content must always be encrypted (AES-256)
- All masking must be applied before any data leaves the local tool
- Jitter noise must be non-zero

## Phase 2+ Upgrade Triggers

| Trigger | Action |
|---------|--------|
| CSV > 500MB | Polars replaces Pandas |
| Graph > 1M edges | Rust petgraph + PyO3 |
| Pattern Diff too slow | Merkle Tree Hashing |
| SaaS needs 250k full view | Cosmograph replaces Sigma.js (adapter change only) |

## AI Assistant Guidelines

1. **Read before writing** — Always read existing files before modifying
2. **Respect constraints** — xlwings not openpyxl, orjson not json, iterative not recursive, batch not iterrows
3. **Respect the masking protocol** — Never weaken privacy guarantees in upload.json
4. **Performance matters** — 250k rows < 15 seconds total pipeline
5. **Use feature IDs** — Reference L1-XX / L2-XX in commits and code comments when implementing tracked features
6. **Follow sprint scope** — S1 features first, then S2, S3, S4 in order
7. **Minimal changes** — Only change what is requested
8. **Update this file** — When adding tooling or conventions, update CLAUDE.md
9. **Security first** — Never commit secrets or real customer data
10. **Test changes** — Run available tests/linters before committing
