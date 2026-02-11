/**
 * SCAFFOLD Local Client Guide — operation manual for the desktop tool.
 *
 * Static content page explaining how to prepare data, run the local tool,
 * and understand the outputs it produces.
 */

import { useDispatch } from "../context/ScaffoldContext";

/* ── SVG Icon Components ────────────────────────────────────────── */

function DownloadIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  );
}

function FileIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
      <polyline points="14 2 14 8 20 8" />
    </svg>
  );
}

function TerminalIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="4 17 10 11 4 5" />
      <line x1="12" y1="19" x2="20" y2="19" />
    </svg>
  );
}

function TableIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
      <line x1="3" y1="9" x2="21" y2="9" />
      <line x1="3" y1="15" x2="21" y2="15" />
      <line x1="9" y1="3" x2="9" y2="21" />
    </svg>
  );
}

function OutputIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
      <polyline points="22 6 12 13 2 6" />
    </svg>
  );
}

function ArrowLeftIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="19" y1="12" x2="5" y2="12" />
      <polyline points="12 19 5 12 12 5" />
    </svg>
  );
}

/* ── LocalGuide Component ─────────────────────────────────────── */

export function LocalGuide() {
  const dispatch = useDispatch();

  const goToLanding = () => dispatch({ type: "SET_PAGE", payload: "landing" });

  return (
    <div className="guide">
      {/* ── Navigation ─────────────────────────────────── */}
      <nav className="landing-nav">
        <div className="landing-nav-inner">
          <span className="landing-logo guide-logo-link" onClick={goToLanding}>SCAFFOLD</span>
          <div className="landing-nav-links">
            <a href="#" onClick={(e) => { e.preventDefault(); goToLanding(); }}>Home</a>
            <span className="nav-active">Local Client Guide</span>
            <button
              className="btn btn-accent btn-sm"
              onClick={() => dispatch({ type: "SET_PAGE", payload: "viewer" })}
            >
              Open Viewer
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────── */}
      <section className="guide-hero">
        <button className="guide-back" onClick={goToLanding}>
          <ArrowLeftIcon />
          Back to Home
        </button>
        <h1>Local Client Guide</h1>
        <p className="guide-hero-sub">
          Step-by-step instructions for preparing your BOM data, running the
          SCAFFOLD local tool, and understanding the output files it produces.
        </p>
      </section>

      {/* ── Table of Contents ──────────────────────────── */}
      <div className="guide-content">
        <nav className="guide-toc">
          <h3>Contents</h3>
          <ol>
            <li><a href="#requirements">System Requirements</a></li>
            <li><a href="#installation">Installation</a></li>
            <li><a href="#data-prep">Preparing Your Data</a></li>
            <li><a href="#running">Running the Tool</a></li>
            <li><a href="#outputs">Understanding Outputs</a></li>
            <li><a href="#viewer-upload">Uploading to the Viewer</a></li>
            <li><a href="#key-restore">Key Restore (Unmask)</a></li>
            <li><a href="#troubleshooting">Troubleshooting</a></li>
          </ol>
        </nav>

        {/* ── 1. System Requirements ──────────────────── */}
        <section className="guide-section" id="requirements">
          <div className="guide-section-icon">
            <DownloadIcon />
          </div>
          <h2>1. System Requirements</h2>
          <div className="guide-card">
            <table className="guide-table">
              <thead>
                <tr>
                  <th>Component</th>
                  <th>Requirement</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Operating System</td>
                  <td>Windows 10/11 (Excel COM required for xlwings)</td>
                </tr>
                <tr>
                  <td>Microsoft Excel</td>
                  <td>Excel 2016 or later (required for reading/writing .xlsx)</td>
                </tr>
                <tr>
                  <td>Disk Space</td>
                  <td>~150 MB (portable folder)</td>
                </tr>
                <tr>
                  <td>Internet</td>
                  <td>Not required — fully offline</td>
                </tr>
              </tbody>
            </table>
            <div className="guide-note">
              The portable build bundles Python and all dependencies. No separate Python installation needed.
            </div>
          </div>
        </section>

        {/* ── 2. Installation ─────────────────────────── */}
        <section className="guide-section" id="installation">
          <div className="guide-section-icon">
            <TerminalIcon />
          </div>
          <h2>2. Installation</h2>
          <div className="guide-card">
            <ol className="guide-steps">
              <li>
                <strong>Download</strong> the latest SCAFFOLD release (.zip) from your delivery channel.
              </li>
              <li>
                <strong>Extract</strong> the zip to any folder (e.g. <code>C:\SCAFFOLD\</code>).
              </li>
              <li>
                <strong>Run</strong> <code>SCAFFOLD.exe</code> from the extracted folder.
              </li>
            </ol>
            <div className="guide-note">
              Windows SmartScreen may show a warning on first launch since the app is not code-signed. Click "More info" then "Run anyway" to proceed.
            </div>
          </div>
        </section>

        {/* ── 3. Preparing Your Data ──────────────────── */}
        <section className="guide-section" id="data-prep">
          <div className="guide-section-icon">
            <TableIcon />
          </div>
          <h2>3. Preparing Your Data</h2>
          <p>
            Your Excel workbook must contain three tabs (sheets) following the V4 Schema.
            Column names must match exactly.
          </p>

          <div className="guide-card">
            <h3>Tab 1: Part Master</h3>
            <p>Defines every unique part at every site.</p>
            <table className="guide-table">
              <thead>
                <tr>
                  <th>Column</th>
                  <th>Type</th>
                  <th>Required</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code>PartNumber</code></td>
                  <td>String</td>
                  <td>Yes</td>
                  <td>Unique part identifier</td>
                </tr>
                <tr>
                  <td><code>Site</code></td>
                  <td>String</td>
                  <td>Yes</td>
                  <td>Manufacturing/warehouse site ID</td>
                </tr>
                <tr>
                  <td><code>IsEndProduct</code></td>
                  <td>Boolean</td>
                  <td>Yes</td>
                  <td>True for finished goods (demand entry points)</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div className="guide-card">
            <h3>Tab 2: BOM Structure</h3>
            <p>Defines parent-child relationships (assembly and transfer edges).</p>
            <table className="guide-table">
              <thead>
                <tr>
                  <th>Column</th>
                  <th>Type</th>
                  <th>Required</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code>AssemblyName</code></td>
                  <td>String</td>
                  <td>Yes</td>
                  <td>Parent part number</td>
                </tr>
                <tr>
                  <td><code>AssemblySite</code></td>
                  <td>String</td>
                  <td>Yes</td>
                  <td>Parent site</td>
                </tr>
                <tr>
                  <td><code>ComponentName</code></td>
                  <td>String</td>
                  <td>Yes</td>
                  <td>Child part number</td>
                </tr>
                <tr>
                  <td><code>ComponentSite</code></td>
                  <td>String</td>
                  <td>Yes</td>
                  <td>Child site</td>
                </tr>
                <tr>
                  <td><code>Qty</code></td>
                  <td>Number</td>
                  <td>Yes</td>
                  <td>Quantity per assembly</td>
                </tr>
                <tr>
                  <td><code>SubGroup</code></td>
                  <td>String</td>
                  <td>No</td>
                  <td>Alternate part group ID</td>
                </tr>
                <tr>
                  <td><code>UsageShare</code></td>
                  <td>Float</td>
                  <td>No</td>
                  <td>Usage share within SubGroup (must sum to 1.0)</td>
                </tr>
              </tbody>
            </table>
            <div className="guide-note">
              <strong>Assembly edges:</strong> Parent part differs from child part (manufacturing).<br />
              <strong>Transfer edges:</strong> Same part, different sites (inter-site supply).
            </div>
          </div>

          <div className="guide-card">
            <h3>Tab 3: Supplier Map</h3>
            <p>Maps parts to their suppliers and lead times.</p>
            <table className="guide-table">
              <thead>
                <tr>
                  <th>Column</th>
                  <th>Type</th>
                  <th>Required</th>
                  <th>Description</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><code>Part</code></td>
                  <td>String</td>
                  <td>Yes</td>
                  <td>Part number</td>
                </tr>
                <tr>
                  <td><code>Supplier</code></td>
                  <td>String</td>
                  <td>Yes</td>
                  <td>Supplier name or ID</td>
                </tr>
                <tr>
                  <td><code>LeadTime</code></td>
                  <td>Number</td>
                  <td>Yes</td>
                  <td>Lead time in days</td>
                </tr>
              </tbody>
            </table>
            <div className="guide-note">
              When a part has multiple suppliers, SCAFFOLD takes the maximum lead time as the risk value.
            </div>
          </div>

          <div className="guide-card">
            <h3>Sample Files</h3>
            <p>
              Download sample CSV files to test the tool or use as a template for your own data.
            </p>
            <div className="guide-sample-links">
              <div className="guide-sample-group">
                <h4>Clean Demo Data (semiconductor BOM)</h4>
                <ul>
                  <li>
                    <a href="https://github.com/dahliaki04/SCAFFOLD/blob/main/demo/part_master.csv" target="_blank" rel="noopener noreferrer">
                      part_master.csv
                    </a> — 72 parts across 8 sites
                  </li>
                  <li>
                    <a href="https://github.com/dahliaki04/SCAFFOLD/blob/main/demo/bom_structure.csv" target="_blank" rel="noopener noreferrer">
                      bom_structure.csv
                    </a> — 81 BOM edges (assembly + transfer)
                  </li>
                  <li>
                    <a href="https://github.com/dahliaki04/SCAFFOLD/blob/main/demo/supplier_map.csv" target="_blank" rel="noopener noreferrer">
                      supplier_map.csv
                    </a> — 59 supplier relationships
                  </li>
                </ul>
              </div>
              <div className="guide-sample-group">
                <h4>Error Demo Data (intentional errors for testing)</h4>
                <p className="guide-sample-desc">
                  These files contain intentional errors to demonstrate every validation check SCAFFOLD performs:
                  blank fields, invalid quantities, circular BOM references, UsageShare mismatches,
                  orphan nodes, and invalid lead times.
                </p>
                <ul>
                  <li>
                    <a href="https://github.com/dahliaki04/SCAFFOLD/blob/main/demo/sample_errors/part_master.csv" target="_blank" rel="noopener noreferrer">
                      part_master.csv
                    </a> — includes blank PartNumber, blank Site, orphan part
                  </li>
                  <li>
                    <a href="https://github.com/dahliaki04/SCAFFOLD/blob/main/demo/sample_errors/bom_structure.csv" target="_blank" rel="noopener noreferrer">
                      bom_structure.csv
                    </a> — includes Qty &le; 0, blank references, circular BOM, SubGroup errors
                  </li>
                  <li>
                    <a href="https://github.com/dahliaki04/SCAFFOLD/blob/main/demo/sample_errors/supplier_map.csv" target="_blank" rel="noopener noreferrer">
                      supplier_map.csv
                    </a> — includes LeadTime &le; 0
                  </li>
                  <li>
                    <a href="https://github.com/dahliaki04/SCAFFOLD/blob/main/demo/sample_errors/sample_results.json" target="_blank" rel="noopener noreferrer">
                      sample_results.json
                    </a> — pre-generated validation results showing all 36 detected issues
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* ── 4. Running the Tool ─────────────────────── */}
        <section className="guide-section" id="running">
          <div className="guide-section-icon">
            <TerminalIcon />
          </div>
          <h2>4. Running the Tool</h2>
          <div className="guide-card">
            <ol className="guide-steps">
              <li>
                <strong>Open SCAFFOLD</strong> — launch the desktop application.
              </li>
              <li>
                <strong>Select your Excel file</strong> — click "Browse" or drag & drop your .xlsx workbook.
              </li>
              <li>
                <strong>Set a password</strong> (optional) — if you want to generate <code>key.scaf</code> for label restore, enter a password. This encrypts the mapping file.
              </li>
              <li>
                <strong>Click "Run"</strong> — the tool validates your data, builds the supply chain graph, computes risk metrics, and generates output files.
              </li>
            </ol>
          </div>

          <div className="guide-card">
            <h3>What happens during processing</h3>
            <ul className="guide-checklist">
              <li>Schema validation — checks required fields, data types, column names</li>
              <li>UsageShare check — verifies SubGroup shares sum to 1.0</li>
              <li>Graph construction — builds a directed graph from BOM edges</li>
              <li>Circular BOM detection — flags any cycles in the structure</li>
              <li>Orphan detection — finds parts not referenced in the BOM and vice versa</li>
              <li>Activity assignment — auto-classifies parts as Buy, Make, or Transfer</li>
              <li>Lead time calculation — computes max lead time per part from suppliers</li>
              <li>Path fingerprinting — traces every path from finished goods to raw materials</li>
              <li>Pattern grouping — groups products with identical supply chain structures</li>
              <li>Risk analysis — single-source detection, impact analysis</li>
              <li>Masking — hashes names, jitters values, masks stages for privacy</li>
            </ul>
          </div>
        </section>

        {/* ── 5. Understanding Outputs ────────────────── */}
        <section className="guide-section" id="outputs">
          <div className="guide-section-icon">
            <FileIcon />
          </div>
          <h2>5. Understanding Outputs</h2>
          <p>
            The tool produces up to four output files depending on your tier.
          </p>

          <div className="guide-output-grid">
            <div className="guide-card guide-output-card">
              <div className="guide-output-header">
                <span className="guide-output-file">validated.xlsx</span>
                <span className="guide-tier-badge guide-tier-free">All tiers</span>
              </div>
              <p>
                A copy of your input Excel with validation results. Invalid cells
                are highlighted in red, and a <code>_SCAFFOLD_Error</code> column
                is added describing each issue. Use this to fix your data.
              </p>
            </div>

            <div className="guide-card guide-output-card">
              <div className="guide-output-header">
                <span className="guide-output-file">report.pdf</span>
                <span className="guide-tier-badge guide-tier-free">All tiers</span>
              </div>
              <p>
                A standalone audit report with network summary statistics:
                node/edge counts, max depth, site count, pattern groups,
                single-source warnings, and supplier impact rankings.
              </p>
            </div>

            <div className="guide-card guide-output-card">
              <div className="guide-output-header">
                <span className="guide-output-file">upload.json</span>
                <span className="guide-tier-badge guide-tier-scope">Scope+</span>
              </div>
              <p>
                The masked data file for the online viewer. All part/site/supplier
                names are SHA-256 hashed, lead times and quantities are jittered,
                stage names are replaced with S1/S2/S3. This is the only file
                that should be uploaded.
              </p>
            </div>

            <div className="guide-card guide-output-card">
              <div className="guide-output-header">
                <span className="guide-output-file">key.scaf</span>
                <span className="guide-tier-badge guide-tier-deliver">Deliver</span>
              </div>
              <p>
                The encrypted mapping file for label restore. Contains the
                hash-to-name lookup, jitter reversal, and stage name mappings.
                AES encrypted with your chosen password. Never upload this file
                to any server — it stays local.
              </p>
            </div>
          </div>

          <div className="guide-note">
            All filenames include a timestamp (e.g. <code>validated_20260209_143000.xlsx</code>) so previous outputs are never overwritten.
          </div>
        </section>

        {/* ── 6. Uploading to the Viewer ──────────────── */}
        <section className="guide-section" id="viewer-upload">
          <div className="guide-section-icon">
            <OutputIcon />
          </div>
          <h2>6. Uploading to the Viewer</h2>
          <div className="guide-card">
            <ol className="guide-steps">
              <li>
                <strong>Open the viewer</strong> — navigate to the SCAFFOLD online viewer
                or click "Open Viewer" in the navigation above.
              </li>
              <li>
                <strong>Drop your <code>upload.json</code></strong> into the upload zone,
                or click to browse for the file.
              </li>
              <li>
                <strong>Explore</strong> — the graph view shows your supply chain network.
                Use the sidebar to filter by stage, site, or depth. Click any product
                to isolate its subgraph. Switch to Sankey view for flow visualization.
              </li>
            </ol>
            <div className="guide-note">
              Everything runs in your browser. The upload.json file is parsed client-side
              and is never sent to any server. You can verify this in your browser's
              DevTools Network tab.
            </div>
          </div>
        </section>

        {/* ── 7. Key Restore ─────────────────────────── */}
        <section className="guide-section" id="key-restore">
          <div className="guide-section-icon">
            <FileIcon />
          </div>
          <h2>7. Key Restore (Unmask Labels)</h2>
          <div className="guide-card">
            <ol className="guide-steps">
              <li>
                <strong>Load your data</strong> in the viewer first (upload.json).
              </li>
              <li>
                <strong>Open Key Restore</strong> panel in the sidebar.
              </li>
              <li>
                <strong>Drop <code>key.scaf</code></strong> into the key drop zone.
              </li>
              <li>
                <strong>Enter your password</strong> — the one you set when generating the key file.
              </li>
              <li>
                <strong>Labels restore</strong> — hashed names become real part/site/supplier names,
                jittered values revert to actuals, and stage labels show real names (e.g. "Wafer Fab"
                instead of "S1").
              </li>
            </ol>
            <div className="guide-note">
              The key.scaf file is decrypted entirely in your browser using the Web Crypto API.
              No network call is made during the restore process.
            </div>
          </div>
        </section>

        {/* ── 8. Troubleshooting ─────────────────────── */}
        <section className="guide-section" id="troubleshooting">
          <div className="guide-section-icon">
            <TerminalIcon />
          </div>
          <h2>8. Troubleshooting</h2>

          <div className="guide-card">
            <h3>Common Issues</h3>
            <div className="guide-faq">
              <div className="guide-faq-item">
                <h4>"Excel COM error" or "xlwings cannot find Excel"</h4>
                <p>
                  Microsoft Excel must be installed on the same machine. The tool uses
                  Excel's COM interface to read and write .xlsx files. LibreOffice and
                  Google Sheets are not supported.
                </p>
              </div>
              <div className="guide-faq-item">
                <h4>"Column X not found" validation error</h4>
                <p>
                  Column names are case-sensitive and must match exactly.
                  Check your sheet tabs are named "Part Master", "BOM Structure",
                  and "Supplier Map".
                </p>
              </div>
              <div className="guide-faq-item">
                <h4>Circular reference detected</h4>
                <p>
                  Your BOM contains a cycle (e.g. Part A uses Part B, which uses Part A).
                  Check the <code>_SCAFFOLD_Error</code> column in <code>validated.xlsx</code>
                  for the specific parts involved. Fix the cycle in your source data and re-run.
                </p>
              </div>
              <div className="guide-faq-item">
                <h4>UsageShare does not sum to 1.0</h4>
                <p>
                  Within each SubGroup, the UsageShare values of all alternate parts must
                  sum to exactly 1.0. Check your BOM Structure tab for the flagged SubGroup.
                </p>
              </div>
              <div className="guide-faq-item">
                <h4>Key restore fails with "wrong password"</h4>
                <p>
                  The password is case-sensitive and must match exactly what was entered
                  when generating the key file. There is no password recovery — if lost,
                  re-generate key.scaf from the local tool.
                </p>
              </div>
            </div>

            <div className="guide-note">
              Want to see what every type of error looks like? Download the{" "}
              <a href="https://github.com/dahliaki04/SCAFFOLD/tree/main/demo/sample_errors" target="_blank" rel="noopener noreferrer">
                error demo files
              </a>{" "}
              and run them through SCAFFOLD.
              The{" "}
              <a href="https://github.com/dahliaki04/SCAFFOLD/blob/main/demo/sample_errors/sample_results.json" target="_blank" rel="noopener noreferrer">
                sample_results.json
              </a>{" "}
              shows the full output with 36 detected issues across all error categories.
            </div>
          </div>
        </section>
      </div>

      {/* ── Footer ─────────────────────────────────────── */}
      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <div className="footer-brand">
            <span className="landing-logo">SCAFFOLD</span>
            <span className="footer-copy">Supply chain structure audit.</span>
          </div>
          <div className="footer-links">
            <a href="https://github.com/dahliaki04/SCAFFOLD" target="_blank" rel="noopener noreferrer">
              GitHub
            </a>
            <span className="footer-sep">|</span>
            <span>AGPL-3.0</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
