/**
 * L2-11: Filter by Stage.
 *
 * S1-S6+ checkbox, graphology filter with undo.
 * L2-27: Stage Color Update — after restore, shows real stage names.
 */

import { useScaffold, useDispatch } from "../context/ScaffoldContext";
import { getStageColor } from "../types";

export function StageFilter() {
  const { stages, stageFilters, keyData } = useScaffold();
  const dispatch = useDispatch();

  const allChecked = stageFilters.size === stages.length;

  return (
    <div className="sidebar-section">
      <h3>Stages</h3>
      <div className="filter-list">
        <label className="filter-item">
          <input
            type="checkbox"
            checked={allChecked}
            onChange={() =>
              dispatch({ type: "SET_ALL_STAGES", payload: !allChecked })
            }
          />
          All
        </label>
        {stages.map((stage) => {
          // L2-27: Show real stage name if key restored
          const realName = keyData?.stages?.[stage];
          const label = realName ? `${stage} (${realName})` : stage;

          return (
            <label key={stage} className="filter-item">
              <input
                type="checkbox"
                checked={stageFilters.has(stage)}
                onChange={() =>
                  dispatch({ type: "TOGGLE_STAGE", payload: stage })
                }
              />
              <span
                className="color-dot"
                style={{ background: getStageColor(stage) }}
              />
              {label}
            </label>
          );
        })}
      </div>
    </div>
  );
}
