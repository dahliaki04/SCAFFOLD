/**
 * Toggle for node risk-based sizing (L2-06).
 *
 * When enabled, node size scales with Max LT (larger = higher risk).
 * When disabled, all nodes render at uniform size.
 */

import { useScaffold, useDispatch } from "../context/ScaffoldContext";

export function NodeSizeToggle() {
  const { nodeSizing } = useScaffold();
  const dispatch = useDispatch();

  return (
    <div className="sidebar-section">
      <h3>Node Size</h3>
      <label className="toggle-item">
        <input
          type="checkbox"
          checked={nodeSizing}
          onChange={() => dispatch({ type: "TOGGLE_NODE_SIZING" })}
        />
        <span>Scale by risk (Max LT)</span>
      </label>
    </div>
  );
}
