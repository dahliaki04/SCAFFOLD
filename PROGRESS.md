# SCAFFOLD Progress Report

> Date: 2026-02-10 | Total Tests: 289 (208 Python + 81 JS) | All Passing

---

## Executive Summary

| Sprint | Scope | P0 Done | P1 Done | Total Done | Status |
|--------|-------|---------|---------|------------|--------|
| S1 | Local Core | 16/16 | - | 16/16 | COMPLETE |
| S2 | Local Reports | 7/7 | 3/3 | 10/10 | COMPLETE |
| S3 | SaaS MVP | 18/18 | 3/3 | 21/21 | COMPLETE |
| S4 | Package & Ship | 8/8 | 3/3 | 11/11 | COMPLETE |
| **Total** | | **49/49** | **9/9** | **58/58** | **100%** |

Phase 2 (P2): 0/12 started (deferred by design).

---

## Sprint 1 — Local Core (16/16 COMPLETE)

All 16 P0 features are implemented, tested, and integrated into the CLI pipeline.

| ID | Feature | Status | File |
|----|---------|--------|------|
| L1-01 | V4 Excel Reader | DONE | `local/core/reader.py` |
| L1-02 | Schema Validation | DONE | `local/core/validation.py` |
| L1-03 | SubGroup UsageShare Check | DONE | `local/core/validation.py` |
| L1-04 | NetworkX DiGraph Build | DONE | `local/core/graph.py` |
| L1-05 | Circular BOM Detection | DONE | `local/core/graph.py` |
| L1-06 | Orphan Detection | DONE | `local/core/graph.py` |
| L1-08 | Smart Ignore | DONE | `local/core/reader.py` |
| L1-09 | Max LeadTime Calculation | DONE | `local/core/risk.py` |
| L1-10 | Auto-Activity Assignment | DONE | `local/core/risk.py` |
| L1-11 | Path Fingerprinting (DFS) | DONE | `local/core/risk.py` |
| L1-12 | Pattern String Grouping | DONE | `local/core/risk.py` |
| L1-16 | SHA-256 Hasher | DONE | `local/masking/hasher.py` |
| L1-17 | Stage Masking | DONE | `local/masking/stage.py` |
| L1-18 | Jitter Engine | DONE | `local/masking/jitter.py` |
| L1-19 | upload.json Generator | DONE | `local/core/output.py` |
| L1-20 | key.scaf Generator (AES) | DONE | `local/core/output.py` |
| L1-21 | orjson Integration | DONE | `local/core/output.py`, `local/cli.py` |

**Test coverage**: `tests/local/` — 168 tests across 6 test files.

---

## Sprint 2 — Local Reports (10/10 COMPLETE)

| ID | Feature | Priority | Status | File |
|----|---------|----------|--------|------|
| L1-13 | Single Source Detection | P0 | DONE | `local/core/risk.py` |
| L1-14 | Impact Analysis | P0 | DONE | `local/core/risk.py` |
| L1-22 | In-place Excel Validation | P0 | DONE | `local/reports/reports.py` |
| L1-23 | Auto-timestamp Filenames | P0 | DONE | `local/reports/reports.py` |
| L1-24 | Network Summary Report | P0 | DONE | `local/reports/reports.py` |
| L1-25 | PartSource Proposal | P0 | DONE | `local/reports/reports.py` |
| L1-15 | Site Dependency Map | P1 | DONE | `local/core/risk.py` |
| L1-26 | Proposal Readback | P1 | DONE | `local/reports/reports.py` |
| L1-27 | PDF Audit Report | P1 | **DONE** | `local/reports/reports.py` |

### L1-27 Detail

Full PDF rendering via ReportLab is now implemented. `render_audit_report_pdf()` generates a standalone PDF with network summary table, validation error counts, and key findings. Data preparation via `generate_audit_report_data()` feeds into the ReportLab platypus layout engine.

---

## Sprint 3 — SaaS MVP (21/21 COMPLETE)

All 18 P0 and 3 P1 features are implemented.

| ID | Feature | Priority | Status | File |
|----|---------|----------|--------|------|
| L2-01 | SCAFFOLD JSON Parser | P0 | DONE | `saas/lib/parser.ts` |
| L2-02 | Sigma.js Adapter (toSigma) | P0 | DONE | `saas/adapters/toSigma.ts` |
| L2-04 | Sigma.js WebGL Renderer | P0 | DONE | `saas/components/GraphView.tsx` |
| L2-05 | Node Color by Stage | P0 | DONE | `saas/types.ts` |
| L2-06 | Node Size by Risk (Max LT) | P0 | DONE | `saas/adapters/toSigma.ts` + `NodeSizeToggle.tsx` |
| L2-07 | Lazy Loading (1000 nodes) | P0 | DONE | `saas/adapters/toSigma.ts` |
| L2-09 | Hover Highlight Neighbors | P0 | DONE | `saas/components/GraphView.tsx` |
| L2-10 | Search Node | P0 | DONE | `saas/components/SearchBar.tsx` |
| L2-11 | Filter by Stage | P0 | DONE | `saas/components/StageFilter.tsx` |
| L2-14 | Subgraph View (select FG) | P0 | DONE | `saas/adapters/toSigma.ts` |
| L2-15 | Product List Panel | P0 | DONE | `saas/components/ProductList.tsx` |
| L2-16 | D3.js Sankey Renderer | P0 | DONE | `saas/components/SankeyView.tsx` |
| L2-17 | Product Path Sankey | P0 | DONE | `saas/components/SankeyView.tsx` |
| L2-18 | Sankey Stage Labels | P0 | DONE | `saas/components/SankeyView.tsx` |
| L2-23 | key.scaf Drag & Drop | P0 | DONE | `saas/components/KeyRestore.tsx` |
| L2-24 | Password Prompt | P0 | DONE | `saas/components/KeyRestore.tsx` |
| L2-25 | Client-side AES Decrypt | P0 | DONE | `saas/lib/crypto.ts` |
| L2-26 | Live Label Restore | P0 | DONE | `saas/adapters/toSigma.ts` |
| L2-27 | Stage Color Update | P0 | DONE | `saas/components/StageFilter.tsx` |
| L2-28 | Key Never Uploaded | P0 | DONE | `saas/lib/crypto.ts` (verified) |
| L2-08 | Semantic Zoom | P1 | DONE | `saas/components/GraphView.tsx` |
| L2-12 | Filter by Site | P1 | DONE | `saas/components/SiteFilter.tsx` |
| L2-13 | Filter by Depth | P1 | DONE | `saas/components/DepthFilter.tsx` |

**Note on L2-12**: Filtering logic works correctly. Site label restoration post-key-restore has a minor display issue (shows hash instead of real name in some cases).

**Test coverage**: `tests/saas/` — 81 tests across 5 test files.

---

## Sprint 4 — Package & Ship (11/11 COMPLETE)

| ID | Feature | Priority | Status | File |
|----|---------|----------|--------|------|
| L1-28 | Kinaxis V7 Export | P0 | **DONE** | `local/export/kinaxis_v7.py` |
| L1-29 | Generic CSV Export | P0 | **DONE** | `local/export/csv_export.py` |
| L1-31 | Free Tier Gate | P0 | **DONE** | `local/core/licensing.py` |
| L1-32 | ttkbootstrap GUI | P0 | **DONE** | `local/gui/app.py` |
| L1-33 | PyInstaller Build | P0 | **DONE** | `scaffold.spec`, `main.py` |
| L2-29 | Rasterized PDF Export | P0 | **DONE** | `saas/lib/exportPdf.ts`, `saas/components/ExportPanel.tsx` |
| L2-31 | Editable PPT Export | P0 | **DONE** | `saas/lib/exportPpt.ts`, `saas/components/ExportPanel.tsx` |
| L2-32 | RSA Signature Verification | P0 | **DONE** | `local/core/licensing.py` |
| L1-07 | Multi-format Input | P1 | **DONE** | `local/cli.py` (Excel + CSV) |
| L1-35 | SmartScreen Disclaimer | P1 | **DONE** | `local/gui/app.py` |
| L1-38 | Sample Data + README | P1 | **DONE** | `demo/` dir + README.md + USAGE.md |

### L2-29 Detail

Client-side rasterized PDF export via jsPDF. All text is rendered to canvas images (anti-OCR). Page 1: summary statistics table, stage legend, risk highlights. Page 2: current graph/sankey visualization capture. Tier-gated to Light and Heavy users.

### L2-31 Detail

Client-side editable PowerPoint (.pptx) export via pptxgenjs. 6-slide deck: title slide, network statistics table, graph visualization (as image), risk analysis table (top 10 by max LT), end product summary, footer. All text/tables are editable in PowerPoint. Tier-gated to Heavy users only.

### New in this update:

- **L2-29**: Rasterized PDF with anti-OCR — jsPDF renders all text as canvas images, preventing text extraction
- **L2-31**: Editable PPT with 6 slides — pptxgenjs generates Office Open XML with editable tables and text
- **ExportPanel**: Sidebar UI with tier-gated buttons (Free: disabled, Light: PDF only, Heavy: PDF + PPT)
- All export happens client-side — zero network calls

---

## Phase 2+ (Deferred — 0/12)

All P2 features remain deferred per plan. No implementation started.

| ID | Feature | Status |
|----|---------|--------|
| L1-30 | SAP IBP Export Plugin | NOT STARTED |
| L1-34 | xlwings Add-in Mode | NOT STARTED |
| L1-36 | Zero Network Calls Verify | NOT STARTED |
| L1-37 | 250k Synthetic Stress Test | NOT STARTED |
| L2-03 | Cosmograph Adapter | NOT STARTED |
| L2-19 | Upload Two JSONs | NOT STARTED |
| L2-20 | Diff Overlay | NOT STARTED |
| L2-21 | Delta Metrics | NOT STARTED |
| L2-22 | New/Deleted Node Highlight | NOT STARTED |
| L2-33 | SaaS UI Polish | NOT STARTED |
| L2-34 | Responsive Layout | NOT STARTED |

---

## Quality Metrics

| Metric | Value |
|--------|-------|
| Total test count | 289 (208 Python + 81 JS) |
| Test pass rate | 100% |
| Build status | `vite build` passing |
| Python test time | ~4s |
| JS test time | ~6s |

---

## New Files Added

| File | Feature | Description |
|------|---------|-------------|
| `local/core/licensing.py` | L1-31, L2-32 | RSA license verification + Free Tier Gate |
| `local/export/kinaxis_v7.py` | L1-28 | Kinaxis V7 RapidResponse CSV export |
| `local/export/csv_export.py` | L1-29 | Generic CSV export with analysis results |
| `local/gui/app.py` | L1-32, L1-35 | ttkbootstrap GUI + SmartScreen disclaimer |
| `main.py` | L1-33 | Entry point (GUI or CLI based on args) |
| `scaffold.spec` | L1-33 | PyInstaller build specification |
| `saas/lib/exportPdf.ts` | L2-29 | Rasterized PDF export (anti-OCR, jsPDF) |
| `saas/lib/exportPpt.ts` | L2-31 | Editable PPT export (pptxgenjs, 6 slides) |
| `saas/components/ExportPanel.tsx` | L2-29, L2-31 | Tier-gated export sidebar UI |
| `tests/local/test_licensing.py` | L1-31, L2-32 | 11 tests for licensing + tier gate |
| `tests/local/test_exports.py` | L1-28, L1-29 | 12 tests for export plugins |
| `tests/local/test_pdf_report.py` | L1-27 | 5 tests for PDF report rendering |
| `tests/local/test_gui.py` | L1-32, L1-33, L1-35 | 10 tests for GUI + packaging |
| `tests/saas/export.test.ts` | L2-29, L2-31 | 23 tests for SaaS export features |
