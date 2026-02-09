# CLAUDE.md — SCAFFOLD

> Spec Version: 3.0 (Frozen) | Feature Plan: 72 features (49 P0 / 11 P1 / 12 P2)
> Codename: SCAFFOLD (鷹架) — supports, then removes itself

## Product Identity

SCAFFOLD is a **supply chain static structure audit and visualization platform**. Consultants and planners drop customer BOM data into a Local Tool (Python desktop), which validates structural integrity, computes risk metrics, anonymizes data, and outputs files that can optionally be uploaded to a SaaS platform (React web) for interactive visualization and editable report generation.

- **Repository**: `dahliaki04/SCAFFOLD`
- **License**: AGPL-3.0
- **Market**: Any manufacturer with BOMs
- **Philosophy**: Murphy's Law — the weakest link in the structure is the inherent risk
- **Design Principle**: Survivor-first — zero trust, offline-first, tools travel with you

## System Architecture

Two-segment disconnected architecture (privacy by design):

```
LOCAL TOOL (Python Desktop)                    SAAS PLATFORM (React Web)
─────────────────────────────                  ────────────────────────
Excel → Validate → Risk Engine → Dual Ledger   Graph View (Sigma.js)
                                                Sankey (D3.js)
Outputs:                                        Diff Overlay
  upload.json  → to SaaS (plaintext, masked)    Client-side Restore (key.scaf)
  key.scaf     → stays local (AES-256)          PPT Export
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
| S1 | 2 weeks | Local Core (`transformer.py`) | 16 | CLI: Excel → upload.json + key.scaf |
| S2 | 2 weeks | Local Reports (`local_reports.py`) | 7 | validated.xlsx + reports (standalone value) |
| S3 | 2 weeks | SaaS MVP | 18 | Sigma.js Graph + Sankey + key restore |
| S4 | 2 weeks | Package & Ship | 8 | GUI + export + tier gate + PPT |

### Sprint 1 — Local Core (16 P0)

Build order: Read → Validate → Risk → Dual Ledger

| ID | Feature | Priority | Description |
|----|---------|----------|-------------|
| L1-01 | V4 Excel Reader | P0 | Read Part Master / BOM / Supplier Map tabs via xlwings |
| L1-02 | Schema Validation | P0 | Check required fields, data types, column names |
| L1-03 | SubGroup UsageShare Check | P0 | Validate UsageShare sums to 1.0 per SubGroup |
| L1-04 | NetworkX DiGraph Build | P0 | Batch edge list from BOM, node key = (PartName, SiteID) |
| L1-05 | Circular BOM Detection | P0 | `nx.simple_cycles(G)`, iterative only |
| L1-06 | Orphan Detection | P0 | Set operations O(1): parts not in BOM, BOM refs not in parts |
| L1-08 | Smart Ignore | P0 | Skip `_SCAFFOLD_Error` columns when reading input |
| L1-09 | Max LeadTime Calculation | P0 | Multi-source → take Max(LT) per part as risk value |
| L1-10 | Auto-Activity Assignment | P0 | Rule-based BUY/MAKE/TRANSFER from BOM structure |
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
| L1-27 | PDF Audit Report | P1 | Standalone structure audit report |

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
| L1-32 | customtkinter GUI | P0 | Dark mode desktop GUI |
| L1-33 | PyInstaller Portable Build | P0 | `--onedir` + UPX compression |
| L2-29 | Rasterized PDF Export | P0 | Image-based PDF, anti-OCR (Light tier) |
| L2-31 | Editable PPT Export | P0 | Slide deck with editable text/charts (Heavy tier) |
| L2-32 | RSA Signature Verification | P0 | Digital signature for paid feature gate |
| L1-07 | Multi-format Input (xlsx/csv) | P1 | Support .xlsx and .csv input |
| L1-35 | SmartScreen Disclaimer | P1 | First-run warning, save EV cert cost |
| L1-38 | Sample Data + README | P1 | Demo dataset for onboarding |
| L2-30 | Layout Destruction (anti-OCR) | P1 | Micro-offset text positioning |

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

### Local Tool (Python)

| Component | Library | Constraint |
|-----------|---------|------------|
| Excel I/O | `xlwings` | **NOT openpyxl** — xlwings required for Add-in mode + cell formatting |
| Data processing | `pandas` | Phase 2: Polars if CSV > 500MB |
| Graph engine | `networkx` | DiGraph only. Phase 2: Rust petgraph + PyO3 if > 1M edges |
| JSON I/O | `orjson` | **NOT standard json** — Rust-backed, 1M records < 3 sec |
| GUI | `customtkinter` | Dark mode |
| Encryption | `cryptography` | AES-256 (key.scaf) + RSA (PPT license) |
| Hashing | `hashlib` | SHA-256 for node masking |
| Packaging | `PyInstaller` + `UPX` | `--onedir` portable folder |

### SaaS Platform (React)

| Component | Library |
|-----------|---------|
| Graph rendering | `sigma.js` + `graphology` (WebGL) |
| Sankey diagrams | `D3.js` + `d3-sankey` (SVG) |
| Frontend framework | `React` |

### Renderer Adapter Architecture

```
SCAFFOLD JSON → Adapter (toSigma / toCosmo / toCyto) → Renderer
```

Swap rendering engine by changing ~50-line adapter only. Core JSON format and business logic untouched.

## Critical Engineering Constraints

These are **non-negotiable** rules. Violating any of these is a bug.

### Graph Engine

```python
# Node key = (PartName, SiteID) tuple — ALWAYS
node = ("WIP-01", "PLANT1")  # ≠ ("WIP-01", "PLANT2")

# Build graph via batch edge list — NEVER iterrows()
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
# Content: MAGIC + version (uint16 LE) + Fernet(PBKDF2(password)).encrypt(zlib.compress(orjson.dumps(data)))
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

Users prepare data in this format; the Local Tool validates it.

| Tab | Key Fields | Required | Logic |
|-----|-----------|----------|-------|
| Part Master | PartNumber, Site | Required | Defines nodes and sites |
| BOM Structure | Parent, Component, Qty | Required | Defines parent-child edges |
| | SubGroup, UsageShare | Optional | Alternate parts; shares must sum to 1.0 |
| Supplier Map | Part, Supplier, LeadTime | Required | Max Rule: same part, multiple suppliers → take max LT |

## upload.json Format

```json
{
  "meta": { "version": "3.0", "generated": "ISO-8601" },
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

## Three-Tier Monetization

| Tier | Gate | Local Output | SaaS Output |
|------|------|-------------|-------------|
| Free | ≤5 products + ≤2,000 rows | validated.xlsx + report.pdf | Masked browse only |
| Light | Unlimited | + upload.json | + Rasterized PDF |
| Heavy | Unlimited | + key.scaf | + Editable PPT + Export Plugin |

## Project Structure (Target)

```
SCAFFOLD/
├── local/                  # Local Tool (Python)
│   ├── core/               # Validation, risk engine, graph ops
│   ├── masking/            # Dual-ledger: hasher, jitter, stage masking
│   ├── export/             # Plugin architecture (Kinaxis V7, CSV, SAP IBP)
│   ├── gui/                # customtkinter UI
│   └── reports/            # validated.xlsx, report.pdf generation
├── saas/                   # SaaS Platform (React)
│   ├── adapters/           # Renderer adapters (toSigma, toCosmo, etc.)
│   ├── components/         # Graph, Sankey, Diff, Restore, PPT export
│   └── public/
├── tests/                  # Test suite
├── requirements.txt        # Python dependencies
├── package.json            # Node dependencies
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
