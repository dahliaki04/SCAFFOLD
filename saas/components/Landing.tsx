/**
 * SCAFFOLD Landing Page — promotional intro + upload entry point.
 *
 * Sections: Hero → Features → How It Works → Pricing → CTA/Upload.
 * Dark professional theme matching the SaaS viewer.
 */

import { useState, useCallback, useRef } from "react";
import { useDispatch } from "../context/ScaffoldContext";
import { parseScaffoldJSON, ParseError } from "../lib/parser";

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

function ArrowDownIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="12" y1="5" x2="12" y2="19" />
      <polyline points="19 12 12 19 5 12" />
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
  const dispatch = useDispatch();
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const [demoLoading, setDemoLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadRef = useRef<HTMLDivElement>(null);

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

  const scrollToDemo = () => {
    document.getElementById("demo")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="landing">
      {/* ── Navigation ─────────────────────────────────── */}
      <nav className="landing-nav">
        <div className="landing-nav-inner">
          <span className="landing-logo">SCAFFOLD</span>
          <div className="landing-nav-links">
            <a href="#demo">Demo</a>
            <a href="#features">Features</a>
            <a href="#how-it-works">How It Works</a>
            <a href="#pricing">Pricing</a>
            <button className="btn btn-accent btn-sm" onClick={scrollToDemo}>
              Try Demo
            </button>
            <button className="btn btn-primary btn-sm" onClick={scrollToUpload}>
              Open Viewer
            </button>
          </div>
        </div>
      </nav>

      {/* ── Hero ───────────────────────────────────────── */}
      <section className="landing-hero">
        <div className="landing-hero-content">
          <div className="landing-hero-badge">Your BOM Analysis Buddy</div>
          <h1>
            See the risk your
            <br />
            <span className="hero-accent">BOM hides</span>
          </h1>
          <p className="landing-hero-sub">
            Map your product structure and visualize where lead time
            accumulates across every part and stage — see which components
            carry the most weight in your chain. Built for planners who
            need visibility into what slows things down, and consultants
            who need to present it. The local tool works fully offline.
            This viewer runs entirely in your browser — your data never
            leaves your machine.
          </p>
          <div className="landing-hero-actions">
            <button className="btn btn-accent btn-lg" onClick={scrollToDemo}>
              Try Semiconductor Demo
              <ArrowDownIcon />
            </button>
            <button className="btn btn-primary btn-lg" onClick={scrollToUpload}>
              Upload Your Data
              <ArrowRightIcon />
            </button>
          </div>
          <div className="landing-hero-stats">
            <div className="hero-stat">
              <span className="hero-stat-value">100%</span>
              <span className="hero-stat-label">free offline tool</span>
            </div>
            <div className="hero-stat-divider" />
            <div className="hero-stat">
              <span className="hero-stat-value">0</span>
              <span className="hero-stat-label">data sent to server</span>
            </div>
            <div className="hero-stat-divider" />
            <div className="hero-stat">
              <span className="hero-stat-value">Browser only</span>
              <span className="hero-stat-label">all processing local</span>
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

      {/* ── Demo Section ────────────────────────────────── */}
      <section className="landing-section section-alt" id="demo">
        <div className="landing-section-inner">
          <div className="demo-showcase">
            <div className="demo-showcase-content">
              <div className="demo-showcase-badge">Live Demo</div>
              <h2>See SCAFFOLD in action</h2>
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

      {/* ── Features ───────────────────────────────────── */}
      <section className="landing-section" id="features">
        <div className="landing-section-inner">
          <div className="section-header">
            <h2>Built for the people behind the BOM</h2>
            <p>
              Analyze your customer's BOM structure, identify patterns and
              present findings — without ever exposing their proprietary data.
            </p>
          </div>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon" style={{ color: "#4285F4" }}>
                <GraphIcon />
              </div>
              <h3>Interactive BOM Graph</h3>
              <p>
                Sigma.js WebGL rendering with stage-colored nodes, risk-based
                sizing, hover highlighting, and per-product subgraph views.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ color: "#F59E0B" }}>
                <FlowIcon />
              </div>
              <h3>Sankey Flow Diagrams</h3>
              <p>
                D3.js-powered multi-hop flow visualization. Select a finished
                good and trace every path through your supply chain.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ color: "#EA4335" }}>
                <AlertIcon />
              </div>
              <h3>Risk Detection</h3>
              <p>
                Single-source alerts, max lead-time bottlenecks, supplier impact
                analysis, and site dependency mapping — all automated.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ color: "#34A853" }}>
                <ShieldIcon />
              </div>
              <h3>Privacy by Design</h3>
              <p>
                SHA-256 hashed names, jittered values, masked stages. Your
                customer's real data never leaves the local machine.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ color: "#9333EA" }}>
                <LockIcon />
              </div>
              <h3>Client-side Decrypt</h3>
              <p>
                Restore real labels in the browser with key.scaf. AES
                decryption happens entirely client-side — zero network calls.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ color: "#06B6D4" }}>
                <LayersIcon />
              </div>
              <h3>Offline-first Local Tool</h3>
              <p>
                Validate Excel BOMs, generate audit reports, and produce
                standalone deliverables — no internet required.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── How It Works ───────────────────────────────── */}
      <section className="landing-section section-alt" id="how-it-works">
        <div className="landing-section-inner">
          <div className="section-header">
            <h2>How SCAFFOLD works</h2>
            <p>Two-segment disconnected architecture. Privacy by design.</p>
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
              <h3>Analyze & Mask</h3>
              <p>
                Risk engine computes lead times, detects single-source parts,
                runs impact analysis. All names are hashed, values jittered.
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
              <div className="arch-label">Local Tool (Python)</div>
              <div className="arch-items">
                <span>Excel Input</span>
                <span>Validation</span>
                <span>Risk Engine</span>
                <span>Dual Ledger</span>
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
              <div className="arch-label">SaaS Viewer (React)</div>
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
              <div className="pricing-tier">Hardhat</div>
              <div className="pricing-price">
                $0<span>/forever</span>
              </div>
              <div className="pricing-desc">
                Grab a hardhat and poke around.
              </div>
              <ul className="pricing-features">
                <li><span className="check"><CheckIcon /></span> Up to 5 end products</li>
                <li><span className="check"><CheckIcon /></span> Up to 2,000 BOM rows</li>
                <li><span className="check"><CheckIcon /></span> validated.xlsx output</li>
                <li><span className="check"><CheckIcon /></span> PDF audit report</li>
                <li><span className="cross"><CrossIcon /></span> upload.json generation</li>
                <li><span className="cross"><CrossIcon /></span> key.scaf generation</li>
                <li><span className="cross"><CrossIcon /></span> SaaS label restore</li>
              </ul>
              <button className="btn btn-outline btn-block" onClick={scrollToUpload}>
                Get Started
              </button>
            </div>

            {/* Scaffold — Coming Soon */}
            <div className="pricing-card pricing-coming-soon">
              <div className="pricing-badge">Coming Soon</div>
              <div className="pricing-tier">Scaffold</div>
              <div className="pricing-price">
                $49<span>/month</span>
              </div>
              <div className="pricing-desc">
                The full rig — no limits, no excuses.
              </div>
              <ul className="pricing-features">
                <li><span className="check"><CheckIcon /></span> Unlimited products & rows</li>
                <li><span className="check"><CheckIcon /></span> validated.xlsx output</li>
                <li><span className="check"><CheckIcon /></span> PDF audit report</li>
                <li><span className="check"><CheckIcon /></span> upload.json generation</li>
                <li><span className="check"><CheckIcon /></span> SaaS masked browse</li>
                <li><span className="check"><CheckIcon /></span> Rasterized PDF export</li>
                <li><span className="cross"><CrossIcon /></span> key.scaf / label restore</li>
              </ul>
              <button className="btn btn-outline btn-block" disabled>
                Coming Soon
              </button>
            </div>

            {/* Skyline — Coming Soon */}
            <div className="pricing-card pricing-coming-soon">
              <div className="pricing-badge">Coming Soon</div>
              <div className="pricing-tier">Skyline</div>
              <div className="pricing-price">
                $129<span>/month</span>
              </div>
              <div className="pricing-desc">
                See the whole picture. Own the presentation.
              </div>
              <ul className="pricing-features">
                <li><span className="check"><CheckIcon /></span> Everything in Scaffold</li>
                <li><span className="check"><CheckIcon /></span> key.scaf generation</li>
                <li><span className="check"><CheckIcon /></span> Client-side label restore</li>
                <li><span className="check"><CheckIcon /></span> Editable PPT export</li>
                <li><span className="check"><CheckIcon /></span> Export plugins (Kinaxis, CSV)</li>
                <li><span className="check"><CheckIcon /></span> Priority support</li>
                <li><span className="check"><CheckIcon /></span> RSA-signed license</li>
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
            <h2>Ready to explore?</h2>
            <p>
              Drop your upload.json below to launch the interactive viewer.
              No account needed. No server upload. Everything runs in your
              browser's memory and is gone when you close the tab.
            </p>
          </div>

          {/* Quick demo link */}
          <div className="demo-quick">
            <span>No data yet?</span>
            <button className="btn btn-sm btn-accent" onClick={loadDemo} disabled={demoLoading}>
              {demoLoading ? "Loading..." : "Load Semiconductor Demo"}
            </button>
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

      {/* ── Footer ─────────────────────────────────────── */}
      <footer className="landing-footer">
        <div className="landing-footer-inner">
          <div className="footer-brand">
            <span className="landing-logo">SCAFFOLD</span>
            <span className="footer-copy">
              Your BOM analysis buddy.
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
