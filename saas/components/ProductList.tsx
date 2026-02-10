/**
 * L2-15: Product List Panel.
 *
 * Right sidebar: list all FG (end product) nodes.
 * Clicking a product enters subgraph view (L2-14).
 * Products are dynamically grouped by L1-12 pattern data when available.
 * Path counts and routes are derived from data.paths (full FG-to-leaf paths).
 */

import { useMemo, useState, useCallback } from "react";
import { useScaffold, useDispatch } from "../context/ScaffoldContext";
import { getEndProducts } from "../lib/parser";

interface ProductInfo {
  id: string;
  label: string;
  pathCount: number; // full end-to-end paths from data.paths
}

interface PatternGroup {
  patternId: string;
  depth: number;
  totalPaths: number; // sum of full paths across all products in group
  uniqueSites: number; // count of distinct sites in site_sequences
  longestRoute: string; // representative longest path (node labels)
  products: ProductInfo[];
}

export function ProductList() {
  const { data, selectedProduct, keyData } = useScaffold();
  const dispatch = useDispatch();

  // Build node hash → display label lookup
  const nodeLabel = useMemo(() => {
    const map = new Map<string, string>();
    if (!data?.nodes) return map;
    for (const nodeId of Object.keys(data.nodes)) {
      const restored = keyData?.nodes?.[nodeId];
      map.set(
        nodeId,
        restored ? `${restored.part}@${restored.site}` : nodeId.slice(0, 8)
      );
    }
    return map;
  }, [data, keyData]);

  // Build product info lookup
  const productMap = useMemo(() => {
    if (!data) return new Map<string, ProductInfo>();
    const map = new Map<string, ProductInfo>();
    for (const id of getEndProducts(data)) {
      const restored = keyData?.nodes?.[id];
      const label = restored
        ? `${restored.part}@${restored.site}`
        : id.slice(0, 12) + "...";
      // Count full end-to-end paths from data.paths
      const paths = data.paths[id];
      const pathCount = Array.isArray(paths) ? paths.length : 0;
      map.set(id, { id, label, pathCount });
    }
    return map;
  }, [data, keyData]);

  // Dynamically group products by pattern (L1-12)
  const { groups, ungrouped } = useMemo(() => {
    if (!data) return { groups: [] as PatternGroup[], ungrouped: [] as ProductInfo[] };

    const patterns = data.patterns ?? {};
    const patternKeys = Object.keys(patterns);
    const grouped = new Set<string>();
    const groups: PatternGroup[] = [];

    for (const patternId of patternKeys) {
      const pattern = patterns[patternId];
      const products: ProductInfo[] = [];
      for (const prodId of pattern.products) {
        const info = productMap.get(prodId);
        if (info) {
          products.push(info);
          grouped.add(prodId);
        }
      }
      if (products.length === 0) continue;

      // Total full paths across all products in this group
      let totalPaths = 0;
      for (const p of products) {
        totalPaths += p.pathCount;
      }

      // Count unique sites from site_sequences
      const allSites = new Set<string>();
      for (const seq of pattern.site_sequences) {
        for (const site of seq) allSites.add(site);
      }

      // Build representative route: longest full path from data.paths
      // Pick the first product and find its longest path
      let longestPath: string[] = [];
      for (const prodId of pattern.products) {
        const paths = data.paths[prodId];
        if (!Array.isArray(paths)) continue;
        for (const path of paths) {
          if (Array.isArray(path) && path.length > longestPath.length) {
            longestPath = path;
          }
        }
      }
      const longestRoute = longestPath
        .map((hash) => nodeLabel.get(hash) ?? hash.slice(0, 8))
        .join(" → ");

      groups.push({
        patternId,
        depth: pattern.depth,
        totalPaths,
        uniqueSites: allSites.size,
        longestRoute,
        products,
      });
    }

    // Products not in any pattern
    const ungrouped: ProductInfo[] = [];
    for (const info of productMap.values()) {
      if (!grouped.has(info.id)) {
        ungrouped.push(info);
      }
    }

    return { groups, ungrouped };
  }, [data, productMap, nodeLabel]);

  // Collapsible pattern groups — track which are collapsed
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set());
  const toggleCollapse = useCallback((patternId: string) => {
    setCollapsed((prev) => {
      const next = new Set(prev);
      if (next.has(patternId)) next.delete(patternId);
      else next.add(patternId);
      return next;
    });
  }, []);

  const hasPatterns = groups.length > 0;
  const totalProducts = productMap.size;

  if (totalProducts === 0) return null;

  const renderProduct = (p: ProductInfo) => (
    <div
      key={p.id}
      className={`product-item ${selectedProduct === p.id ? "selected" : ""}`}
      onClick={() =>
        dispatch({
          type: "SELECT_PRODUCT",
          payload: selectedProduct === p.id ? null : p.id,
        })
      }
    >
      <span>{p.label}</span>
      <span className="badge">{p.pathCount} paths</span>
    </div>
  );

  return (
    <div className="sidebar-section">
      <h3>End Products ({totalProducts})</h3>
      <div className="product-list">
        {/* Show All option */}
        <div
          className={`product-item ${selectedProduct === null ? "selected" : ""}`}
          onClick={() => dispatch({ type: "SELECT_PRODUCT", payload: null })}
        >
          All Products
        </div>

        {hasPatterns ? (
          <>
            {groups.map((group) => {
              const isCollapsed = collapsed.has(group.patternId);
              return (
                <div key={group.patternId} className="pattern-group">
                  <div
                    className="pattern-group-header"
                    onClick={() => toggleCollapse(group.patternId)}
                  >
                    <span className="pattern-group-id">
                      <span className="fold-arrow">{isCollapsed ? "\u25b6" : "\u25bc"}</span>
                      {group.patternId}
                    </span>
                    <span className="badge">
                      {group.totalPaths} paths · {group.uniqueSites} sites · depth {group.depth}
                    </span>
                  </div>
                  {!isCollapsed && (
                    <>
                      {group.longestRoute && (
                        <div className="pattern-route" title={group.longestRoute}>
                          {group.longestRoute}
                        </div>
                      )}
                      {group.products.map(renderProduct)}
                    </>
                  )}
                </div>
              );
            })}
            {ungrouped.length > 0 && (() => {
              const isCollapsed = collapsed.has("__ungrouped");
              return (
                <div className="pattern-group">
                  <div
                    className="pattern-group-header"
                    onClick={() => toggleCollapse("__ungrouped")}
                  >
                    <span className="pattern-group-id">
                      <span className="fold-arrow">{isCollapsed ? "\u25b6" : "\u25bc"}</span>
                      Ungrouped
                    </span>
                  </div>
                  {!isCollapsed && ungrouped.map(renderProduct)}
                </div>
              );
            })()}
          </>
        ) : (
          Array.from(productMap.values()).map(renderProduct)
        )}
      </div>
    </div>
  );
}
