/**
 * Pattern List Panel.
 *
 * Lists consolidated supply chain patterns (L1-12).
 * Each pattern groups end products with identical site-sequence structures.
 * Hover shows product count + names. Click selects pattern for full-path view.
 */

import { useMemo, useState } from "react";
import { useScaffold, useDispatch } from "../context/ScaffoldContext";

export function PatternList() {
  const { data, selectedPattern, keyData } = useScaffold();
  const dispatch = useDispatch();
  const [hoveredPattern, setHoveredPattern] = useState<string | null>(null);

  const patterns = useMemo(() => {
    if (!data || !data.patterns) return [];
    return Object.entries(data.patterns)
      .sort(([, a], [, b]) => b.depth - a.depth)
      .map(([pid, pat]) => {
        const productLabels = pat.products.map((hash) => {
          const restored = keyData?.nodes?.[hash];
          return restored
            ? `${restored.part}@${restored.site}`
            : hash.slice(0, 10) + "...";
        });
        return {
          pid,
          depth: pat.depth,
          productCount: pat.products.length,
          pathCount: pat.site_sequences.length,
          productLabels,
        };
      });
  }, [data, keyData]);

  if (patterns.length === 0) return null;

  return (
    <div className="sidebar-section">
      <h3>BOM Patterns ({patterns.length})</h3>
      <div className="product-list">
        {/* Show All option */}
        <div
          className={`product-item ${selectedPattern === null ? "selected" : ""}`}
          onClick={() => dispatch({ type: "SELECT_PATTERN", payload: null })}
        >
          All Patterns
        </div>
        {patterns.map((p) => (
          <div
            key={p.pid}
            className={`product-item ${selectedPattern === p.pid ? "selected" : ""}`}
            style={{ position: "relative" }}
            onClick={() =>
              dispatch({
                type: "SELECT_PATTERN",
                payload: selectedPattern === p.pid ? null : p.pid,
              })
            }
            onMouseEnter={() => setHoveredPattern(p.pid)}
            onMouseLeave={() => setHoveredPattern(null)}
          >
            <span>
              {p.pid} &middot; depth {p.depth}
            </span>
            <span className="badge">
              {p.productCount} products
            </span>
            {/* Hover tooltip */}
            {hoveredPattern === p.pid && (
              <div className="pattern-tooltip">
                <div style={{ fontWeight: 600, marginBottom: 4 }}>
                  {p.productCount} end product{p.productCount !== 1 ? "s" : ""}
                </div>
                {p.productLabels.map((label, i) => (
                  <div key={i} style={{ fontSize: "0.85em", opacity: 0.9 }}>
                    {label}
                  </div>
                ))}
                <div
                  style={{
                    marginTop: 4,
                    fontSize: "0.8em",
                    opacity: 0.7,
                  }}
                >
                  {p.pathCount} unique paths
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
