# SCAFFOLD (鷹架)

**Supply Chain Static Structure Audit & Visualization Platform**

> Supports, then removes itself.

SCAFFOLD automates supply chain structure auditing. Drop customer BOM data into the Local Tool — it validates structural integrity, computes risk metrics, anonymizes data, and produces secure files for optional upload to the SaaS platform for interactive visualization and editable report generation.

**Philosophy**: Murphy's Law — the weakest link in the structure is the inherent risk.
**Design**: Survivor-first — zero trust, offline-first, tools travel with you.

---

## How It Works

```
┌────────────────────────────────────────────┐
│ LOCAL TOOL (Python Desktop)                │
│                                            │
│ Excel → Validate → Risk Engine → Export    │
│                                            │
│ Outputs:                                   │
│   upload.json    → SaaS (masked, public)   │
│   key.scaf       → Local (AES-256, private)│
│   validated.xlsx → Errors highlighted      │
│   report.pdf     → Structure audit report  │
└──────────────────┬─────────────────────────┘
                   │ upload.json only
┌──────────────────▼─────────────────────────┐
│ SAAS PLATFORM (React Web)                  │
│                                            │
│ Graph View │ Sankey │ Diff Overlay          │
│                                            │
│ Drag key.scaf → Password → Restore in      │
│ browser (key never uploaded)               │
└────────────────────────────────────────────┘
```

### Privacy by Design

- **upload.json** is plaintext JSON — open it in Notepad. All names are SHA-256 hashed, stages replaced with S1/S2/S3..., numeric values jittered ±15%. No real business data leaves the local machine.
- **key.scaf** is AES-256 encrypted and password-protected. It stays on your laptop.
- **Client-side restore**: key.scaf is decrypted in the browser. The server never sees real data.

## For Whom

| User | Value |
|------|-------|
| Supply Chain Consultant | Cut 2-3 days of manual modeling per engagement |
| Planner / NPI Engineer | "New part number affects who? Supplier switch changes risk how much?" |
| Procurement / M&A Team | Supplier consolidation, factory relocation impact analysis |
| Senior Auditor | Structural risk inventory |

## Features

### Local Tool
- **Strict Validation** — Schema + logic checks (circular BOM, orphan detection, SubGroup share sums)
- **Static Risk Engine** — Max LeadTime, single source detection, path fingerprinting, impact analysis
- **Dual-Ledger Export** — SHA-256 + jitter + stage masking → `upload.json` + `key.scaf`
- **Local Reports** — `validated.xlsx` (red-highlighted) + `report.pdf` (network summary)
- **Export Plugins** — Kinaxis V7, Generic CSV, SAP IBP (plugin architecture)

### SaaS Platform
- **Graph View** — Sigma.js (WebGL), lazy loading, semantic zoom, filter by Site/Stage/Depth
- **Product-Centric Sankey** — D3.js, multi-stage path visualization per end product
- **Diff Overlay** — Blue (baseline) vs orange (target) structural comparison
- **Client-side Restore** — Drag key.scaf + password → real data restored in browser only
- **PPT Export** — Editable PowerPoint for consultant delivery

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Local Tool | Python (xlwings, pandas, networkx, orjson, customtkinter, cryptography) |
| SaaS Platform | React (sigma.js, graphology, D3.js, d3-sankey) |
| Packaging | PyInstaller + UPX (portable folder) |
| Encryption | AES-256 (key.scaf), RSA (PPT license) |

## Data Format

Users prepare an Excel workbook with three tabs:

1. **Part Master** — PartNumber, Site (defines nodes)
2. **BOM Structure** — Parent, Component, Qty (defines edges); optional SubGroup + UsageShare
3. **Supplier Map** — Part, Supplier, LeadTime (defines sources; max LT rule for multi-supplier)

## Getting Started

> Development is in early stages. See [CLAUDE.md](CLAUDE.md) for full technical specification, engineering constraints, and contributor guidelines.

## License

[GNU Affero General Public License v3.0](LICENSE)
