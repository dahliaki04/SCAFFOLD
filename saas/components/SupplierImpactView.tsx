/**
 * Supplier Impact View — L1-14 visualization in SaaS.
 *
 * Lists all suppliers from upload.json sorted by impact count (desc).
 * Selecting a supplier highlights:
 *   1. supplied_nodes — the exact (part, site) graph nodes this supplier feeds
 *   2. affected_products — end products reachable via backward trace
 *   3. the full upstream chain between them (computed in GraphView)
 *
 * After key.scaf restore: shows real supplier names instead of hashes.
 */

import { useMemo } from "react";
import { useScaffold, useDispatch } from "../context/ScaffoldContext";

interface SupplierInfo {
  hash: string;
  label: string;
  suppliedCount: number;
  impactCount: number;
  suppliedNodes: string[];
  affectedProducts: string[];
}

export function SupplierImpactView() {
  const { data, selectedSupplier, keyData } = useScaffold();
  const dispatch = useDispatch();

  const suppliers = useMemo(() => {
    if (!data?.suppliers) return [];

    const list: SupplierInfo[] = [];
    for (const [hash, info] of Object.entries(data.suppliers)) {
      const restoredName = keyData?.suppliers?.[hash];
      list.push({
        hash,
        label: restoredName ?? hash.slice(0, 12) + "...",
        suppliedCount: info.supplied_nodes.length,
        impactCount: info.impact_count,
        suppliedNodes: info.supplied_nodes,
        affectedProducts: info.affected_products,
      });
    }

    // Sort by impact count descending (most critical first)
    list.sort((a, b) => b.impactCount - a.impactCount);
    return list;
  }, [data, keyData]);

  // Build node label lookup for displaying supplied part@site
  const nodeLabel = useMemo(() => {
    const map = new Map<string, string>();
    if (!data?.nodes) return map;
    for (const nodeId of Object.keys(data.nodes)) {
      const restored = keyData?.nodes?.[nodeId];
      map.set(
        nodeId,
        restored ? `${restored.part}@${restored.site}` : nodeId.slice(0, 8),
      );
    }
    return map;
  }, [data, keyData]);

  if (suppliers.length === 0) return null;

  // Detail panel for the selected supplier
  const selectedInfo = selectedSupplier
    ? suppliers.find((s) => s.hash === selectedSupplier)
    : null;

  return (
    <div className="sidebar-section">
      <h3>Supplier Impact ({suppliers.length})</h3>
      <div className="product-list">
        {/* Clear selection */}
        <div
          className={`product-item ${selectedSupplier === null ? "selected" : ""}`}
          onClick={() => dispatch({ type: "SELECT_SUPPLIER", payload: null })}
        >
          All Suppliers
        </div>

        {suppliers.map((sup) => (
          <div
            key={sup.hash}
            className={`product-item ${selectedSupplier === sup.hash ? "selected" : ""}`}
            onClick={() =>
              dispatch({
                type: "SELECT_SUPPLIER",
                payload: selectedSupplier === sup.hash ? null : sup.hash,
              })
            }
          >
            <span>{sup.label}</span>
            <span className="badge">
              {sup.impactCount} products · {sup.suppliedCount} nodes
            </span>
          </div>
        ))}
      </div>

      {/* Detail panel when a supplier is selected */}
      {selectedInfo && (
        <div className="supplier-detail">
          <h4>Supplied Nodes</h4>
          <div className="supplier-detail-list">
            {selectedInfo.suppliedNodes.map((nodeId) => (
              <div key={nodeId} className="supplier-detail-item supplied">
                {nodeLabel.get(nodeId) ?? nodeId.slice(0, 8)}
              </div>
            ))}
          </div>
          <h4>Affected End Products</h4>
          <div className="supplier-detail-list">
            {selectedInfo.affectedProducts.map((nodeId) => (
              <div key={nodeId} className="supplier-detail-item affected">
                {nodeLabel.get(nodeId) ?? nodeId.slice(0, 8)}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
