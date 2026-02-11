/**
 * SCAFFOLD SaaS Platform — Main Application.
 *
 * Layout:
 *   Desktop (>768px): Header + Sidebar (left) + Main View (right).
 *   Mobile (<=768px): Header + Collapsible controls (top) + Main View (below).
 */

import { useState } from "react";
import { ScaffoldProvider, useScaffold, useDispatch } from "../context/ScaffoldContext";
import { GraphView } from "./GraphView";
import { SankeyView } from "./SankeyView";
import { SearchBar } from "./SearchBar";
import { StageFilter } from "./StageFilter";
import { SiteFilter } from "./SiteFilter";
import { DepthFilter } from "./DepthFilter";
import { ProductList } from "./ProductList";
import { KeyRestore } from "./KeyRestore";
import { NodeSizeToggle } from "./NodeSizeToggle";
import { SupplierImpactView } from "./SupplierImpactView";
import { ExportPanel } from "./ExportPanel";
import { Landing } from "./Landing";

function AppContent() {
  const { loaded, data, viewMode, restored } = useScaffold();
  const dispatch = useDispatch();
  const [panelOpen, setPanelOpen] = useState(false);

  if (!loaded) {
    return <Landing />;
  }

  const nodeCount = data ? Object.keys(data.nodes).length : 0;
  const edgeCount = data ? data.edges.length : 0;

  return (
    <div className="app-container">
      <header className="app-header">
        <span className="logo">SCAFFOLD</span>
        <span className="version">v3.0</span>

        {/* View toggle */}
        <div className="view-toggle">
          <button
            className={viewMode === "graph" ? "active" : ""}
            onClick={() => dispatch({ type: "SET_VIEW", payload: "graph" })}
          >
            Graph
          </button>
          <button
            className={viewMode === "sankey" ? "active" : ""}
            onClick={() => dispatch({ type: "SET_VIEW", payload: "sankey" })}
          >
            Sankey
          </button>
        </div>

        {/* Stats */}
        <div className="stats-bar">
          <div className="stat">
            Nodes: <span className="stat-value">{nodeCount}</span>
          </div>
          <div className="stat">
            Edges: <span className="stat-value">{edgeCount}</span>
          </div>
          <div className="stat">
            {restored ? (
              <span style={{ color: "var(--success)" }}>Labels Restored</span>
            ) : (
              <span style={{ color: "var(--warning)" }}>Masked View</span>
            )}
          </div>
        </div>

        {/* Mobile panel toggle */}
        <button
          className="panel-toggle"
          onClick={() => setPanelOpen((prev) => !prev)}
          aria-label={panelOpen ? "Hide controls" : "Show controls"}
        >
          {panelOpen ? "\u2715" : "\u2630"}
        </button>
      </header>

      <div className="app-body">
        {/* Controls panel — sidebar on desktop, collapsible top panel on mobile */}
        <div className={`sidebar ${panelOpen ? "sidebar--open" : ""}`}>
          <div className="sidebar-section">
            <h3>Search</h3>
            <SearchBar />
          </div>
          <ProductList />
          <SupplierImpactView />
          <StageFilter />
          <SiteFilter />
          <DepthFilter />
          <NodeSizeToggle />
          <KeyRestore />
          <ExportPanel />
        </div>

        {/* Main view */}
        <div className="main-view">
          {viewMode === "graph" ? <GraphView /> : <SankeyView />}
        </div>
      </div>
    </div>
  );
}

export function App() {
  return (
    <ScaffoldProvider>
      <AppContent />
    </ScaffoldProvider>
  );
}
