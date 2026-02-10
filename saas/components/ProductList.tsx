/**
 * L2-15: Product List Panel.
 *
 * Right sidebar: list all FG (end product) nodes.
 * Clicking a product enters subgraph view (L2-14).
 * Products are dynamically grouped by L1-12 pattern data when available.
 * Pattern summaries (unique sites, paths, route) are derived from site_sequences.
 */

import { useMemo } from "react";
import { useScaffold, useDispatch } from "../context/ScaffoldContext";
import { getEndProducts } from "../lib/parser";

interface ProductInfo {
  id: string;
  label: string;
  pathCount: number;
}

interface PatternGroup {
  patternId: string;
  depth: number;
  pathCount: number;
  uniqueSites: string[]; // display labels: restored names or hash prefix
  route: string; // e.g. "WAF → HUB → PLT" or "08d4… → 133a… → 3654…"
  products: ProductInfo[];
}

/**
 * Derive unique ordered sites from site_sequences.
 * Preserves first-seen order (the structural route).
 */
function deriveUniqueSites(sequences: string[][]): string[] {
  const seen = new Set<string>();
  const ordered: string[] = [];
  for (const seq of sequences) {
    for (const siteHash of seq) {
      if (!seen.has(siteHash)) {
        seen.add(siteHash);
        ordered.push(siteHash);
      }
    }
  }
  return ordered;
}

export function ProductList() {
  const { data, selectedProduct, keyData } = useScaffold();
  const dispatch = useDispatch();

  // Build product info lookup
  const productMap = useMemo(() => {
    if (!data) return new Map<string, ProductInfo>();
    const map = new Map<string, ProductInfo>();
    for (const id of getEndProducts(data)) {
      const restored = keyData?.nodes?.[id];
      const label = restored
        ? `${restored.part}@${restored.site}`
        : id.slice(0, 12) + "...";
      const pathCount = data.paths[id]?.length ?? 0;
      map.set(id, { id, label, pathCount });
    }
    return map;
  }, [data, keyData]);

  // Build site hash → real name lookup (for key restore)
  const siteHashToName = useMemo(() => {
    const map = new Map<string, string>();
    if (!data?.nodes || !keyData?.nodes) return map;
    for (const [nodeId, nodeData] of Object.entries(data.nodes)) {
      const restored = keyData.nodes[nodeId];
      if (restored && !map.has(nodeData.site)) {
        map.set(nodeData.site, restored.site);
      }
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

      // Derive structural info from site_sequences
      const siteHashes = deriveUniqueSites(pattern.site_sequences);
      const uniqueSites = siteHashes.map((hash) =>
        siteHashToName.get(hash) ?? hash.slice(0, 6) + "…"
      );

      const route = uniqueSites.join(" → ");

      groups.push({
        patternId,
        depth: pattern.depth,
        pathCount: pattern.site_sequences.length,
        uniqueSites,
        route,
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
  }, [data, productMap, siteHashToName]);

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
            {groups.map((group) => (
              <div key={group.patternId} className="pattern-group">
                <div className="pattern-group-header">
                  <span className="pattern-group-id">{group.patternId}</span>
                  <span className="badge">
                    {group.uniqueSites.length} sites · {group.pathCount} paths · depth {group.depth}
                  </span>
                </div>
                <div className="pattern-route" title={group.route}>
                  {group.route}
                </div>
                {group.products.map(renderProduct)}
              </div>
            ))}
            {ungrouped.length > 0 && (
              <div className="pattern-group">
                <div className="pattern-group-header">
                  <span className="pattern-group-id">Ungrouped</span>
                </div>
                {ungrouped.map(renderProduct)}
              </div>
            )}
          </>
        ) : (
          Array.from(productMap.values()).map(renderProduct)
        )}
      </div>
    </div>
  );
}
