/**
 * L2-13: Filter by Depth (P1).
 *
 * Slider to show BOM levels 1-N.
 */

import { useScaffold, useDispatch } from "../context/ScaffoldContext";

export function DepthFilter() {
  const { maxDepth, depthFilter } = useScaffold();
  const dispatch = useDispatch();

  if (maxDepth === 0) return null;

  return (
    <div className="sidebar-section">
      <h3>Depth</h3>
      <div className="depth-slider">
        <input
          type="range"
          min={0}
          max={maxDepth}
          value={depthFilter === Infinity ? maxDepth : depthFilter}
          onChange={(e) =>
            dispatch({ type: "SET_DEPTH", payload: Number(e.target.value) })
          }
        />
        <div className="slider-label">
          <span>0</span>
          <span>
            Level {depthFilter === Infinity ? maxDepth : depthFilter} /{" "}
            {maxDepth}
          </span>
        </div>
      </div>
    </div>
  );
}
