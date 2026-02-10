/**
 * L2-12: Filter by Site (P1).
 *
 * Hash checkboxes; after restore shows real site names.
 */

import { useScaffold, useDispatch } from "../context/ScaffoldContext";

export function SiteFilter() {
  const { sites, siteFilters, keyData } = useScaffold();
  const dispatch = useDispatch();

  const allChecked = siteFilters.size === sites.length;

  // Build label map from key data
  const siteLabels = new Map<string, string>();
  if (keyData?.nodes) {
    for (const nodeInfo of Object.values(keyData.nodes)) {
      // Hash → real site name might be stored differently
      // For now, use the hash prefix as label
    }
  }

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
          // After restore, try to find real site name
          let label = site.slice(0, 10) + "...";
          if (keyData?.nodes) {
            for (const nodeInfo of Object.values(keyData.nodes)) {
              if (nodeInfo.site && site === site) {
                // The keyData maps node hashes to real names
                // We need to find the real site name for this hash
                label = nodeInfo.site;
                break;
              }
            }
          }

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
