# CLAUDE.md — SCAFFOLD

> Spec Version: 3.0 (Frozen)
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

## Local Tool Features

- **F1.1 Strict Validation**: Schema check + logic check (SubGroup UsageShare sums, circular BOM via `nx.simple_cycles`, orphan detection via set ops). Output: `validated.xlsx` with red-highlighted errors + `_SCAFFOLD_Error` column. Smart Ignore: auto-skip `_SCAFFOLD_Error` columns on re-read.
- **F1.2 Static Risk Engine**: Max LT (multi-source → max), Auto-Activity (BUY/MAKE/TRANSFER), Single Source Detection, Path Fingerprinting (DFS per FG), Impact Analysis (supplier outage → affected product lines), Site Dependency Map.
- **F1.3 Dual-Ledger Export**: SHA-256 hashing + Jitter ±15% + Stage masking → `upload.json` (plaintext) + `key.scaf` (AES-256).
- **F1.4 Local Reports**: `validated.xlsx`, `report.pdf` (Network Summary), PartSource Proposal (Excel + checkbox).
- **F1.5 Export Plugin Architecture**: Kinaxis V7 (Phase 1), Generic CSV (Phase 1), SAP IBP (Phase 2). Core engine is system-agnostic.

## SaaS Platform Features

- **F2.1 Renderer Adapter Architecture**: JSON Parser → Adapter (`toSigma()`, `toCosmo()`, `toCyto()`) → Renderer. Swap engine by changing ~50-line adapter only.
- **F2.2 Graph View**: Sigma.js + graphology. Lazy Loading (max 1000 nodes rendered, default 3-level expand). Semantic zoom. Sidebar filter by Site/Stage/Depth. Subgraph extraction per FG. Color by Stage.
- **F2.3 Product-Centric Sankey**: D3.js. Select end product → multi-stage path visualization. Reads `paths` field from upload.json.
- **F2.4 Diff Overlay**: Blue (baseline) vs orange (target). Delta for Depth and Risk. Green = new nodes, red semi-transparent = deleted nodes.
- **F2.5 Client-side Restore**: Drag key.scaf → enter password → frontend JS decrypts in-memory → replaces hashes with real names, S1-S6 with real stages, jitter values with real values. Key never uploaded.
- **F2.6 PPT Export**: Free = browse only; Light = rasterized PDF (anti-OCR); Heavy = editable PPT (RSA signed).

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
5. **Minimal changes** — Only change what is requested
6. **Update this file** — When adding tooling or conventions, update CLAUDE.md
7. **Security first** — Never commit secrets or real customer data
8. **Test changes** — Run available tests/linters before committing
