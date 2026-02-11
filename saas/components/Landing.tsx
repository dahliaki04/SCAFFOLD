/**
 * SCAFFOLD Landing Page — promotional intro + upload entry point.
 *
 * Sections: Hero → Features → How It Works → Pricing → CTA/Upload.
 * Dark professional theme matching the SaaS viewer.
 */

import { useState, useCallback, useRef } from "react";
import { useScaffold, useDispatch } from "../context/ScaffoldContext";
import { parseScaffoldJSON, ParseError } from "../lib/parser";
import type { ScaffoldJSON } from "../types";

/* ── SVG Icon Components ────────────────────────────────────────── */

function ShieldIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
    </svg>
  );
}

function GraphIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="6" r="2" />
      <circle cx="18" cy="6" r="2" />
      <circle cx="6" cy="18" r="2" />
      <circle cx="18" cy="18" r="2" />
      <circle cx="12" cy="12" r="2" />
      <line x1="7.8" y1="7.2" x2="10.5" y2="10.5" />
      <line x1="13.5" y1="10.5" x2="16.2" y2="7.2" />
      <line x1="7.8" y1="16.8" x2="10.5" y2="13.5" />
      <line x1="13.5" y1="13.5" x2="16.2" y2="16.8" />
    </svg>
  );
}

function FlowIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="3" width="6" height="5" rx="1" />
      <rect x="16" y="3" width="6" height="5" rx="1" />
      <rect x="9" y="16" width="6" height="5" rx="1" />
      <path d="M5 8v3a2 2 0 002 2h10a2 2 0 002-2V8" />
      <line x1="12" y1="13" x2="12" y2="16" />
    </svg>
  );
}

function AlertIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
      <line x1="12" y1="9" x2="12" y2="13" />
      <line x1="12" y1="17" x2="12.01" y2="17" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
      <path d="M7 11V7a5 5 0 0110 0v4" />
    </svg>
  );
}

function LayersIcon() {
  return (
    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 2 7 12 12 22 7 12 2" />
      <polyline points="2 17 12 22 22 17" />
      <polyline points="2 12 12 17 22 12" />
    </svg>
  );
}

function UploadIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="16 16 12 12 8 16" />
      <line x1="12" y1="12" x2="12" y2="21" />
      <path d="M20.39 18.39A5 5 0 0018 9h-1.26A8 8 0 103 16.3" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

function CrossIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}

function ArrowRightIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="5" y1="12" x2="19" y2="12" />
      <polyline points="12 5 19 12 12 19" />
    </svg>
  );
}

/* ── Landing Page Component ─────────────────────────────────────── */

export function Landing() {
  const { loaded } = useScaffold();
  const dispatch = useDispatch();
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const [demoLoading, setDemoLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadRef = useRef<HTMLDivElement>(null);

  // L2-19: Diff upload state
  const [baselineDragOver, setBaselineDragOver] = useState(false);
  const [targetDragOver, setTargetDragOver] = useState(false);
  const [baselineFile, setBaselineFile] = useState<ScaffoldJSON | null>(null);
  const [targetFile, setTargetFile] = useState<ScaffoldJSON | null>(null);
  const [baselineName, setBaselineName] = useState("");
  const [targetName, setTargetName] = useState("");
  const [diffError, setDiffError] = useState("");
  const baselineInputRef = useRef<HTMLInputElement>(null);
  const targetInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    (file: File) => {
      setError("");
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const data = parseScaffoldJSON(reader.result as string);
          dispatch({ type: "LOAD_DATA", payload: data });
        } catch (err) {
          setError(
            err instanceof ParseError ? err.message : "Failed to parse file"
          );
        }
      };
      reader.readAsText(file);
    },
    [dispatch]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const loadDemo = useCallback(async () => {
    setDemoLoading(true);
    setError("");
    try {
      const res = await fetch("/demo-upload.json");
      if (!res.ok) throw new Error("Failed to fetch demo data");
      const text = await res.text();
      const data = parseScaffoldJSON(text);
      dispatch({ type: "LOAD_DATA", payload: data });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load demo");
      setDemoLoading(false);
    }
  }, [dispatch]);

  const scrollToUpload = () => {
    uploadRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // L2-19: Handle baseline/target file loading for diff
  const handleDiffFile = useCallback(
    (file: File, slot: "baseline" | "target") => {
      setDiffError("");
      const reader = new FileReader();
      reader.onload = () => {
        try {
          const data = parseScaffoldJSON(reader.result as string);
          if (slot === "baseline") {
            setBaselineFile(data);
            setBaselineName(file.name);
          } else {
            setTargetFile(data);
            setTargetName(file.name);
          }
        } catch (err) {
          setDiffError(
            err instanceof ParseError ? err.message : "Failed to parse file"
          );
        }
      };
      reader.readAsText(file);
    },
    []
  );

  const handleDiffDrop = useCallback(
    (e: React.DragEvent, slot: "baseline" | "target") => {
      e.preventDefault();
      if (slot === "baseline") setBaselineDragOver(false);
      else setTargetDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleDiffFile(file, slot);
    },
    [handleDiffFile]
  );

  const launchDiff = useCallback(() => {
    if (!baselineFile || !targetFile) return;
    dispatch({
      type: "LOAD_DIFF",
      payload: { baseline: baselineFile, target: targetFile },
    });
  }, [baselineFile, targetFile, dispatch]);

  return (
    <div className="landing">
      {/* ── Navigation ─────────────────────────────────── */}
      <nav className="landing-nav">
        <div className="landing-nav-inner">
          <span className="landing-logo">SCAFFOLD</span>
          <div className="landing-nav-links">
            <a href="#features">Features</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#pricing">Pricing</a>
            <a href="#compare">Compare</a>
            <a href="#" onClick={(e) => { e.preventDefault(); dispatch({ type: "SET_PAGE", payload: "guide" }); }}>
              Guide
            </a>
            {loaded && (
              <button className="btn btn-accent btn-sm" onClick={() => dispatch({ type: "SET_PAGE", payload: "viewer" })}>
                Open Viewer
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────── */}
      <section className="landing-hero">
        <div className="landing-hero-content">
          <div className="landing-hero-badge">Supply Chain Structure Audit</div>
          <h1>
            See the risk your
            <br />
            <span className="hero-accent">BOM hides</span>
          </h1>
          <p className="landing-hero-sub">
            Orphan parts, circular refs, broken links — small BOM errors
            that take hours to find and seconds to fix. SCAFFOLD catches
            them instantly, then visualizes your supply network so you see
            how products cluster, where suppliers overlap, and which
            disruption hits the most lines. Runs entirely on your machine.
          </p>
          <div className="landing-hero-actions">
            <button className="btn btn-accent btn-lg" onClick={loadDemo} disabled={demoLoading}>
              {demoLoading ? "Loading Demo..." : "Try Semiconductor Demo"}
              <ArrowRightIcon />
            </button>
            <button className="btn btn-primary btn-lg" onClick={scrollToUpload}>
              Upload Your Data
              <ArrowRightIcon />
            </button>
          </div>
          <div className="landing-hero-stats">
            <div className="hero-stat">
              <span className="hero-stat-value">250k+</span>
              <span className="hero-stat-label">rows in under 15s</span>
            </div>
            <div className="hero-stat-divider" />
            <div className="hero-stat">
              <span className="hero-stat-value">Zero upload</span>
              <span className="hero-stat-label">runs on your machine</span>
            </div>
            <div className="hero-stat-divider" />
            <div className="hero-stat">
              <span className="hero-stat-value">3 clicks</span>
              <span className="hero-stat-label">Excel to audit report</span>
            </div>
          </div>
        </div>
        <div className="landing-hero-visual">
          <div className="hero-graph-mock">
            <svg viewBox="0 0 400 300" className="hero-svg">
              {/* Edges */}
              <line x1="200" y1="40" x2="120" y2="120" stroke="#4285F4" strokeWidth="1.5" opacity="0.5" />
              <line x1="200" y1="40" x2="280" y2="120" stroke="#4285F4" strokeWidth="1.5" opacity="0.5" />
              <line x1="120" y1="120" x2="60" y2="200" stroke="#34A853" strokeWidth="1.5" opacity="0.5" />
              <line x1="120" y1="120" x2="160" y2="200" stroke="#34A853" strokeWidth="1.5" opacity="0.5" />
              <line x1="280" y1="120" x2="240" y2="200" stroke="#F59E0B" strokeWidth="1.5" opacity="0.5" />
              <line x1="280" y1="120" x2="340" y2="200" stroke="#F59E0B" strokeWidth="1.5" opacity="0.5" />
              <line x1="60" y1="200" x2="100" y2="270" stroke="#EA4335" strokeWidth="1.5" opacity="0.4" />
              <line x1="160" y1="200" x2="100" y2="270" stroke="#EA4335" strokeWidth="1.5" opacity="0.4" />
              <line x1="240" y1="200" x2="300" y2="270" stroke="#9333EA" strokeWidth="1.5" opacity="0.4" />
              <line x1="340" y1="200" x2="300" y2="270" stroke="#9333EA" strokeWidth="1.5" opacity="0.4" />
              {/* Nodes */}
              <circle cx="200" cy="40" r="14" fill="#4285F4" opacity="0.9" />
              <circle cx="120" cy="120" r="11" fill="#34A853" opacity="0.9" />
              <circle cx="280" cy="120" r="12" fill="#F59E0B" opacity="0.9" />
              <circle cx="60" cy="200" r="8" fill="#EA4335" opacity="0.9" />
              <circle cx="160" cy="200" r="9" fill="#EA4335" opacity="0.9" />
              <circle cx="240" cy="200" r="10" fill="#9333EA" opacity="0.9" />
              <circle cx="340" cy="200" r="7" fill="#9333EA" opacity="0.9" />
              <circle cx="100" cy="270" r="6" fill="#06B6D4" opacity="0.9" />
              <circle cx="300" cy="270" r="6" fill="#06B6D4" opacity="0.9" />
              {/* Labels */}
              <text x="200" y="44" textAnchor="middle" fill="#fff" fontSize="8" fontWeight="600">FG</text>
              <text x="120" y="124" textAnchor="middle" fill="#fff" fontSize="7">WIP</text>
              <text x="280" y="124" textAnchor="middle" fill="#fff" fontSize="7">WIP</text>
            </svg>
            <div className="hero-graph-label">Interactive BOM Graph</div>
          </div>
        </div>
      </section>

      {/* ── Trust Banner ─────────────────────────────────── */}
      <section className="landing-trust-banner">
        <div className="landing-trust-inner">
          <div className="trust-item">
            <ShieldIcon />
            <div>
              <strong>Free offline local tool</strong>
              <span>Structure-check your product BOMs, visualize lead time weight, and generate reports — fully offline, zero internet required.</span>
            </div>
          </div>
          <div className="trust-item">
            <LockIcon />
            <div>
              <strong>Browser-only online viewer</strong>
              <span>All processing happens in your browser's memory. Nothing is uploaded to any server — verifiable in DevTools Network tab.</span>
            </div>
          </div>
          <div className="trust-item">
            <LayersIcon />
            <div>
              <strong>Safe for sensitive data</strong>
              <span>Names are SHA-256 hashed, values are jittered, stages are masked. The upload file reveals zero business terms.</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ───────────────────────────────────── */}
      <section className="landing-section section-alt" id="features">
        <div className="landing-section-inner">
          <div className="section-header">
            <h2>Built for the people behind the BOM</h2>
            <p>
              Find structural errors, visualize supplier impact, and present
              findings — without exposing your customer's proprietary data.
            </p>
          </div>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon" style={{ color: "#EA4335" }}>
                <AlertIcon />
              </div>
              <h3>Catch errors before modeling</h3>
              <p>
                Orphan parts, circular references, missing links, bad sums —
                flagged instantly so you fix in minutes, not days.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ color: "#4285F4" }}>
                <GraphIcon />
              </div>
              <h3>See the full network</h3>
              <p>
                Interactive graph colored by stage, sized by lead time. Click
                any product to isolate its subgraph.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ color: "#F59E0B" }}>
                <FlowIcon />
              </div>
              <h3>Trace every path</h3>
              <p>
                Sankey flow from finished good to raw material. See where
                paths converge, where suppliers overlap, where risk stacks.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ color: "#9333EA" }}>
                <LayersIcon />
              </div>
              <h3>Measure supplier impact</h3>
              <p>
                Pick any supplier — see every product line affected. Single-source
                parts and site dependencies surfaced automatically.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ color: "#34A853" }}>
                <ShieldIcon />
              </div>
              <h3>Safe for customer data</h3>
              <p>
                Names hashed, values jittered, stages masked. Analyze your
                customer's BOM without exposing a single business term.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ color: "#06B6D4" }}>
                <LockIcon />
              </div>
              <h3>Works fully offline</h3>
              <p>
                Local tool validates, audits, and generates reports with zero
                internet. The online viewer processes everything in your browser.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Demo Section ────────────────────────────────── */}
      <section className="landing-section" id="demo">
        <div className="landing-section-inner">
          <div className="demo-showcase">
            <div className="demo-showcase-content">
              <div className="demo-showcase-badge">Live Demo</div>
              <h2>See it yourself</h2>
              <p>
                Explore a semiconductor BOM with 65 parts across 8 global sites
                and 6 process stages — from wafer fabrication through to distribution.
              </p>
              <div className="demo-showcase-actions">
                <button className="btn btn-accent btn-lg" onClick={loadDemo} disabled={demoLoading}>
                  {demoLoading ? "Loading..." : "Load Demo Instantly"}
                  <ArrowRightIcon />
                </button>
              </div>
              <div className="demo-showcase-info">
                <span>6 finished goods</span>
                <span className="demo-dot" />
                <span>6 process stages</span>
                <span className="demo-dot" />
                <span>8 fabs & sites</span>
              </div>
            </div>
            <div className="demo-showcase-details">
              <div className="demo-detail-card">
                <h4>Included in the demo</h4>
                <ul>
                  <li>2 products with 8-level deep supply chains</li>
                  <li>2 products with 6-level manufacturing flows</li>
                  <li>2 products with 4-level assembly paths</li>
                </ul>
              </div>
              <div className="demo-detail-card">
                <h4>Try the unmask flow</h4>
                <p>After loading the demo, download <a href="/demo-key.scaf" download="key.scaf">key.scaf</a> and drop it into the Key Restore panel. Password: <code>scaffold-demo</code></p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── How It Works ───────────────────────────────── */}
      <section className="landing-section section-alt" id="how-it-works">
        <div className="landing-section-inner">
          <div className="section-header">
            <h2>How it works</h2>
            <p>Local tool processes your data. Online viewer shows the result. Nothing crosses unless you choose.</p>
          </div>
          <div className="steps-flow">
            <div className="step-card">
              <div className="step-number">1</div>
              <h3>Load BOM Data</h3>
              <p>
                Drop your customer's Excel file into the Local Tool. Part Master,
                BOM Structure, and Supplier Map — validated instantly.
              </p>
            </div>
            <div className="step-arrow">
              <ArrowRightIcon />
            </div>
            <div className="step-card">
              <div className="step-number">2</div>
              <h3>Validate & Analyze</h3>
              <p>
                Structural errors flagged, lead times computed, supplier impact
                mapped. Names are hashed and values masked automatically.
              </p>
            </div>
            <div className="step-arrow">
              <ArrowRightIcon />
            </div>
            <div className="step-card">
              <div className="step-number">3</div>
              <h3>Visualize</h3>
              <p>
                Upload the masked JSON to the SaaS viewer. Interactive graph,
                Sankey flows, filterable by stage, site, and depth.
              </p>
            </div>
            <div className="step-arrow">
              <ArrowRightIcon />
            </div>
            <div className="step-card">
              <div className="step-number">4</div>
              <h3>Present & Export</h3>
              <p>
                Optionally restore labels with key.scaf. Export to PDF or
                editable PPT for client presentations.
              </p>
            </div>
          </div>
          <div className="architecture-diagram">
            <div className="arch-segment arch-local">
              <div className="arch-label">Local Tool</div>
              <div className="arch-items">
                <span>Excel Input</span>
                <span>Validation</span>
                <span>Risk Analysis</span>
                <span>Masking</span>
              </div>
              <div className="arch-outputs">
                <span className="arch-file">upload.json</span>
                <span className="arch-file arch-file-key">key.scaf</span>
              </div>
            </div>
            <div className="arch-gap">
              <div className="arch-gap-line" />
              <span>Air Gap</span>
              <div className="arch-gap-line" />
            </div>
            <div className="arch-segment arch-saas">
              <div className="arch-label">Online Viewer</div>
              <div className="arch-items">
                <span>Graph View</span>
                <span>Sankey Flow</span>
                <span>Key Restore</span>
                <span>Export</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Pricing ────────────────────────────────────── */}
      <section className="landing-section" id="pricing">
        <div className="landing-section-inner">
          <div className="section-header">
            <h2>Simple, transparent pricing</h2>
            <p>Start free. Upgrade when you need more.</p>
          </div>
          <div className="pricing-grid">
            {/* Free */}
            <div className="pricing-card">
              <div className="pricing-tier">Taste</div>
              <div className="pricing-price">
                $0<span>/forever</span>
              </div>
              <div className="pricing-desc">
                Validate, sort, and fix your BOM in place.
              </div>
              <ul className="pricing-features">
                <li><span className="check"><CheckIcon /></span> Up to 5 end products</li>
                <li><span className="check"><CheckIcon /></span> Up to 2,000 BOM rows</li>
                <li><span className="check"><CheckIcon /></span> validated.xlsx output</li>
                <li><span className="check"><CheckIcon /></span> PDF report</li>
                <li><span className="cross"><CrossIcon /></span> upload.json generation</li>
                <li><span className="cross"><CrossIcon /></span> key.scaf generation</li>
                <li><span className="cross"><CrossIcon /></span> SaaS label restore</li>
              </ul>
              <button className="btn btn-outline btn-block" onClick={scrollToUpload}>
                Get Started
              </button>
            </div>

            {/* Scope — Coming Soon */}
            <div className="pricing-card pricing-coming-soon">
              <div className="pricing-badge">Coming Soon</div>
              <div className="pricing-tier">Scope</div>
              <div className="pricing-price">
                $19.9<span>/month</span>
              </div>
              <div className="pricing-desc">
                See the full picture. No limits.
              </div>
              <ul className="pricing-features">
                <li><span className="check"><CheckIcon /></span> Unlimited products & rows</li>
                <li><span className="check"><CheckIcon /></span> validated.xlsx output</li>
                <li><span className="check"><CheckIcon /></span> PDF report</li>
                <li><span className="check"><CheckIcon /></span> upload.json generation</li>
                <li><span className="check"><CheckIcon /></span> SaaS masked browse</li>
                <li><span className="check"><CheckIcon /></span> Rasterized PDF export</li>
                <li><span className="cross"><CrossIcon /></span> key.scaf / label restore</li>
              </ul>
              <button className="btn btn-outline btn-block" disabled>
                Coming Soon
              </button>
            </div>

            {/* Deliver — Coming Soon */}
            <div className="pricing-card pricing-coming-soon">
              <div className="pricing-badge">Coming Soon</div>
              <div className="pricing-tier">Deliver</div>
              <div className="pricing-price">
                $39.9<span>/month</span>
              </div>
              <div className="pricing-desc">
                Present to clients. Own the deliverable.
              </div>
              <ul className="pricing-features">
                <li><span className="check"><CheckIcon /></span> Everything in Scope</li>
                <li><span className="check"><CheckIcon /></span> key.scaf generation</li>
                <li><span className="check"><CheckIcon /></span> Client-side label restore</li>
                <li><span className="check"><CheckIcon /></span> Editable PPT export</li>
                <li><span className="check"><CheckIcon /></span> Export plugins (Kinaxis, CSV)</li>
              </ul>
              <button className="btn btn-outline btn-block" disabled>
                Coming Soon
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── Upload CTA ─────────────────────────────────── */}
      <section className="landing-section section-alt" id="upload" ref={uploadRef}>
        <div className="landing-section-inner">
          <div className="section-header">
            <h2>Ready to try it?</h2>
            <p>
              Drop your upload.json to launch the viewer. No account, no
              server — everything runs in your browser and is gone when
              you close the tab.
            </p>
          </div>

          <div
            className={`landing-upload ${dragOver ? "drag-over" : ""}`}
            onDragOver={(e) => {
              e.preventDefault();
              setDragOver(true);
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <UploadIcon />
            <h3>Drop upload.json here</h3>
            <p>or click to browse</p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            style={{ display: "none" }}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleFile(file);
            }}
          />
          {error && (
            <div style={{ color: "var(--danger)", fontSize: 13, marginTop: 8, textAlign: "center" }}>
              {error}
            </div>
          )}
        </div>
      </section>

      {/* ── Compare BOMs (L2-19) ─────────────────────────── */}
      <section className="landing-section" id="compare">
        <div className="landing-section-inner">
          <div className="section-header">
            <h2>Compare two BOMs</h2>
            <p>
              Upload a baseline and target upload.json to see what changed —
              new parts, removed connections, shifted risk levels.
            </p>
            <p className="compare-sample-hint">
              No files yet? Try with our samples:{" "}
              <a href="/diff_baseline.json" download="diff_baseline.json">baseline.json</a>
              {" & "}
              <a href="/diff_target.json" download="diff_target.json">target.json</a>
            </p>
          </div>

          <div className="diff-upload-row">
            {/* Baseline drop zone */}
            <div className="diff-upload-slot">
              <h4>Baseline</h4>
              <div
                className={`diff-drop-zone ${baselineDragOver ? "drag-over" : ""} ${baselineFile ? "loaded" : ""}`}
                onDragOver={(e) => {
                  e.preventDefault();
                  setBaselineDragOver(true);
                }}
                onDragLeave={() => setBaselineDragOver(false)}
                onDrop={(e) => handleDiffDrop(e, "baseline")}
                onClick={() => baselineInputRef.current?.click()}
              >
                {baselineFile ? (
                  <>
                    <span className="diff-slot-check">&#10003;</span>
                    <span className="diff-slot-name">{baselineName}</span>
                  </>
                ) : (
                  <>
                    <UploadIcon />
                    <span>Drop baseline JSON</span>
                  </>
                )}
              </div>
              <input
                ref={baselineInputRef}
                type="file"
                accept=".json"
                style={{ display: "none" }}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleDiffFile(file, "baseline");
                }}
              />
            </div>

            <div className="diff-upload-arrow">
              <ArrowRightIcon />
            </div>

            {/* Target drop zone */}
            <div className="diff-upload-slot">
              <h4>Target</h4>
              <div
                className={`diff-drop-zone ${targetDragOver ? "drag-over" : ""} ${targetFile ? "loaded" : ""}`}
                onDragOver={(e) => {
                  e.preventDefault();
                  setTargetDragOver(true);
                }}
                onDragLeave={() => setTargetDragOver(false)}
                onDrop={(e) => handleDiffDrop(e, "target")}
                onClick={() => targetInputRef.current?.click()}
              >
                {targetFile ? (
                  <>
                    <span className="diff-slot-check">&#10003;</span>
                    <span className="diff-slot-name">{targetName}</span>
                  </>
                ) : (
                  <>
                    <UploadIcon />
                    <span>Drop target JSON</span>
                  </>
                )}
              </div>
              <input
                ref={targetInputRef}
                type="file"
                accept=".json"
                style={{ display: "none" }}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleDiffFile(file, "target");
                }}
              />
            </div>
          </div>

          {diffError && (
            <div style={{ color: "var(--danger)", fontSize: 13, marginTop: 8, textAlign: "center" }}>
              {diffError}
            </div>
          )}

          <div style={{ textAlign: "center", marginTop: 16 }}>
            <button
              className="btn btn-accent btn-lg"
              disabled={!baselineFile || !targetFile}
              onClick={launchDiff}
            >
              Compare
              <ArrowRightIcon />
            </button>
          </div>
        </div>
      </section>

      {/* ── Footer ─────────────────────────────────────── */}
      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <div className="footer-brand">
            <span className="landing-logo">SCAFFOLD</span>
            <span className="footer-copy">
              Supply chain structure audit.
            </span>
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
