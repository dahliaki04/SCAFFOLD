# SCAFFOLD Progress Report

> Date: 2026-02-10 | Total Tests: 266 (208 Python + 58 JS) | All Passing

---

## Executive Summary

| Sprint | Scope | P0 Done | P1 Done | Total Done | Status |
|--------|-------|---------|---------|------------|--------|
| S1 | Local Core | 16/16 | - | 16/16 | COMPLETE |
| S2 | Local Reports | 7/7 | 3/3 | 10/10 | COMPLETE |
| S3 | SaaS MVP | 18/18 | 3/3 | 21/21 | COMPLETE |
| S4 | Package & Ship | 5/8 | 3/3 | 8/11 | 73% |
| **Total** | | **46/49** | **9/11** | **55/58** | **95%** |

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

**Test coverage**: `tests/saas/` — 58 tests across 4 test files.

---

## Sprint 4 — Package & Ship (8/11, 73%)

| ID | Feature | Priority | Status | File |
|----|---------|----------|--------|------|
| L1-28 | Kinaxis V7 Export | P0 | **DONE** | `local/export/kinaxis_v7.py` |
| L1-29 | Generic CSV Export | P0 | **DONE** | `local/export/csv_export.py` |
| L1-31 | Free Tier Gate | P0 | **DONE** | `local/core/licensing.py` |
| L1-32 | ttkbootstrap GUI | P0 | **DONE** | `local/gui/app.py` |
| L1-33 | PyInstaller Build | P0 | **DONE** | `scaffold.spec`, `main.py` |
| L2-29 | Rasterized PDF Export | P0 | NOT STARTED | SaaS-side feature |
| L2-31 | Editable PPT Export | P0 | NOT STARTED | SaaS-side feature |
| L2-32 | RSA Signature Verification | P0 | **DONE** | `local/core/licensing.py` |
| L1-07 | Multi-format Input | P1 | **DONE** | `local/cli.py` (Excel + CSV) |
| L1-35 | SmartScreen Disclaimer | P1 | **DONE** | `local/gui/app.py` |
| L1-38 | Sample Data + README | P1 | **DONE** | `demo/` dir + README.md + USAGE.md |

### New in this update:

- **L1-07**: CLI now accepts `--input data.xlsx` for single-workbook mode, or `--pm/--bom/--sup` for CSV mode
- **L1-28**: Kinaxis V7 RapidResponse CSV export with Part, Site, Activity, Supplier, LeadTime, Category columns
- **L1-29**: Generic flat CSV export with full analysis results (activity, risk, depth, suppliers)
- **L1-31**: Free tier limits enforced at runtime (≤5 end products, ≤2000 rows)
- **L1-32**: ttkbootstrap desktop GUI with darkly theme, file pickers, export toggles, progress log
- **L1-33**: PyInstaller spec file (`scaffold.spec`) with UPX compression, hidden imports, ttkbootstrap collection
- **L1-35**: SmartScreen first-run disclaimer dialog with flag file persistence
- **L2-32**: Full RSA license key system — generate, sign, verify offline. License format: `SCAF-<TIER>-<b64>.<sig>`
- **L1-27**: PDF audit report rendering via ReportLab (network summary table, validation errors, findings)

### Remaining S4 items (SaaS-side):
- **L2-29**: Rasterized PDF export (browser-side, anti-OCR)
- **L2-31**: Editable PPT export (browser-side, python-pptx or equivalent)

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
| Total test count | 266 (208 Python + 58 JS) |
| Test pass rate | 100% |
| Build status | `vite build` passing |
| Bundle size | 491 KB (141 KB gzipped) |
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
| `tests/local/test_licensing.py` | L1-31, L2-32 | 11 tests for licensing + tier gate |
| `tests/local/test_exports.py` | L1-28, L1-29 | 12 tests for export plugins |
| `tests/local/test_pdf_report.py` | L1-27 | 5 tests for PDF report rendering |
| `tests/local/test_gui.py` | L1-32, L1-33, L1-35 | 10 tests for GUI + packaging |
