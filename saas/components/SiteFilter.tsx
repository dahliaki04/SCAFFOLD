/**
 * L2-12: Filter by Site (P1).
 *
 * Hash checkboxes; after restore shows real site names.
 */

import { useMemo } from "react";
import { useScaffold, useDispatch } from "../context/ScaffoldContext";

export function SiteFilter() {
  const { data, sites, siteFilters, keyData } = useScaffold();
  const dispatch = useDispatch();

  const allChecked = siteFilters.size === sites.length;

  // Build site hash → real site name map by cross-referencing
  // data.nodes (site hash) with keyData.nodes (real site name)
  const siteLabels = useMemo(() => {
    const map = new Map<string, string>();
    if (!data?.nodes || !keyData?.nodes) return map;
    for (const [nodeId, nodeData] of Object.entries(data.nodes)) {
      const restored = keyData.nodes[nodeId];
      if (restored?.site && !map.has(nodeData.site)) {
        map.set(nodeData.site, restored.site);
      }
    }
    return map;
  }, [data, keyData]);

  return (
    <div className="sidebar-section">
      <h3>Sites</h3>
      <div className="filter-list">
        <label className="filter-item">
          <input
            type="checkbox"
            checked={allChecked}
            onChange={() =>
              dispatch({ type: "SET_ALL_SITES", payload: !allChecked })
            }
          />
          All
        </label>
        {sites.map((site) => {
          const label = siteLabels.get(site) ?? site.slice(0, 10) + "...";

          return (
            <label key={site} className="filter-item">
              <input
                type="checkbox"
                checked={siteFilters.has(site)}
                onChange={() =>
                  dispatch({ type: "TOGGLE_SITE", payload: site })
                }
              />
              {label}
            </label>
          );
        })}
      </div>
    </div>
  );
}
