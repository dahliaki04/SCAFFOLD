/**
 * L2-15: Product List Panel.
 *
 * Right sidebar: list all FG (end product) nodes.
 * Clicking a product enters subgraph view (L2-14).
 * Products are grouped by L1-12 pattern when pattern data is available.
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
  products: ProductInfo[];
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

  // Group products by pattern (L1-12)
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
      if (products.length > 0) {
        groups.push({ patternId, depth: pattern.depth, products });
      }
    }

    // Products not in any pattern
    const ungrouped: ProductInfo[] = [];
    for (const info of productMap.values()) {
      if (!grouped.has(info.id)) {
        ungrouped.push(info);
      }
    }

    return { groups, ungrouped };
  }, [data, productMap]);

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
            {groups.map((group, idx) => (
              <div key={group.patternId} className="pattern-group">
                <div className="pattern-group-header">
                  Pattern {idx + 1}
                  <span className="badge">
                    {group.products.length} products · depth {group.depth}
                  </span>
                </div>
                {group.products.map(renderProduct)}
              </div>
            ))}
            {ungrouped.length > 0 && (
              <div className="pattern-group">
                <div className="pattern-group-header">Ungrouped</div>
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
