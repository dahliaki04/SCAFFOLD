/**
 * L2-21: Delta Metrics (ΔDepth, ΔRisk).
 * L2-22: New/Deleted Node counts.
 *
 * Sidebar panel showing computed diff metrics between baseline and target.
 */

import { useScaffold, useDispatch } from "../context/ScaffoldContext";
import { DIFF_COLORS, type DiffStatus } from "../types";

/** Format a signed delta value with + prefix for positive. */
function formatDelta(val: number): string {
  if (val > 0) return `+${val}`;
  return String(val);
}

export function DeltaMetrics() {
  const { diffResult, diffStatusFilter, keyData } = useScaffold();
  const dispatch = useDispatch();

  if (!diffResult) return null;

  const { metrics } = diffResult;

  const statusItems: { status: DiffStatus; label: string; count: number }[] = [
    { status: "added", label: "Added", count: metrics.addedNodes },
    { status: "removed", label: "Removed", count: metrics.removedNodes },
    { status: "modified", label: "Modified", count: metrics.modifiedNodes },
    { status: "unchanged", label: "Unchanged", count: metrics.unchangedNodes },
  ];

  return (
    <>
      {/* Diff status filter */}
      <div className="sidebar-section">
        <h3>Diff Filter</h3>
        <div className="filter-list">
          {statusItems.map(({ status, label, count }) => (
            <label key={status} className="filter-item">
              <input
                type="checkbox"
                checked={diffStatusFilter.has(status)}
                onChange={() =>
                  dispatch({ type: "TOGGLE_DIFF_STATUS", payload: status })
                }
              />
              <span
                className="color-dot"
                style={{ background: DIFF_COLORS[status] }}
              />
              <span>
                {label} ({count})
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Delta metrics */}
      <div className="sidebar-section">
        <h3>Delta Metrics</h3>
        <div className="delta-metrics">
          <div className="delta-row">
            <span className="delta-label">Nodes</span>
            <span className="delta-value">
              {metrics.baselineNodeCount} → {metrics.targetNodeCount}
              <span
                className={`delta-badge ${
                  metrics.targetNodeCount - metrics.baselineNodeCount >= 0
                    ? "delta-positive"
                    : "delta-negative"
                }`}
              >
                {formatDelta(
                  metrics.targetNodeCount - metrics.baselineNodeCount
                )}
              </span>
            </span>
          </div>
          <div className="delta-row">
            <span className="delta-label">Edges</span>
            <span className="delta-value">
              {metrics.baselineEdgeCount} → {metrics.targetEdgeCount}
              <span
                className={`delta-badge ${
                  metrics.targetEdgeCount - metrics.baselineEdgeCount >= 0
                    ? "delta-positive"
                    : "delta-negative"
                }`}
              >
                {formatDelta(
                  metrics.targetEdgeCount - metrics.baselineEdgeCount
                )}
              </span>
            </span>
          </div>
          <div className="delta-row">
            <span className="delta-label">Max Depth</span>
            <span className="delta-value">
              <span
                className={`delta-badge ${
                  metrics.deltaMaxDepth >= 0
                    ? "delta-positive"
                    : "delta-negative"
                }`}
              >
                {formatDelta(metrics.deltaMaxDepth)}
              </span>
            </span>
          </div>
          <div className="delta-row">
            <span className="delta-label">Avg Risk</span>
            <span className="delta-value">
              <span
                className={`delta-badge ${
                  metrics.deltaAvgRisk >= 0
                    ? "delta-negative"
                    : "delta-positive"
                }`}
              >
                {metrics.deltaAvgRisk >= 0 ? "+" : ""}
                {metrics.deltaAvgRisk.toFixed(1)}
              </span>
            </span>
          </div>
        </div>

        {/* Product changes */}
        {(metrics.addedProducts.length > 0 ||
          metrics.removedProducts.length > 0) && (
          <div className="delta-products">
            {metrics.addedProducts.length > 0 && (
              <div className="delta-product-group">
                <h4>New Products</h4>
                {metrics.addedProducts.map((p) => (
                  <div
                    key={p}
                    className="delta-product-item delta-product-added"
                  >
                    {keyData?.nodes?.[p]?.part ?? p.slice(0, 12) + "..."}
                  </div>
                ))}
              </div>
            )}
            {metrics.removedProducts.length > 0 && (
              <div className="delta-product-group">
                <h4>Removed Products</h4>
                {metrics.removedProducts.map((p) => (
                  <div
                    key={p}
                    className="delta-product-item delta-product-removed"
                  >
                    {keyData?.nodes?.[p]?.part ?? p.slice(0, 12) + "..."}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Exit diff mode */}
      <div className="sidebar-section">
        <button
          className="btn btn-sm"
          style={{ width: "100%" }}
          onClick={() => dispatch({ type: "CLEAR_DIFF" })}
        >
          Exit Diff Mode
        </button>
      </div>
    </>
  );
}
