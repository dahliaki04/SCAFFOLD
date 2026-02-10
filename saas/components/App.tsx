/**
 * SCAFFOLD SaaS Platform — Main Application.
 *
 * Layout: Header + Sidebar (left) + Main View (center/right).
 */

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
import { Landing } from "./Landing";

function AppContent() {
  const { loaded, data, viewMode, restored } = useScaffold();
  const dispatch = useDispatch();

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
      </header>

      <div className="app-body">
        {/* Left sidebar */}
        <div className="sidebar">
          <div className="sidebar-section">
            <h3>Search</h3>
            <SearchBar />
          </div>
          <ProductList />
          <StageFilter />
          <SiteFilter />
          <DepthFilter />
          <NodeSizeToggle />
          <KeyRestore />
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
