/**
 * L2-15: Product List Panel.
 *
 * Right sidebar: list all FG (end product) nodes.
 * Clicking a product enters subgraph view (L2-14).
 */

import { useMemo } from "react";
import { useScaffold, useDispatch } from "../context/ScaffoldContext";
import { getEndProducts } from "../lib/parser";

export function ProductList() {
  const { data, selectedProduct, keyData } = useScaffold();
  const dispatch = useDispatch();

  const products = useMemo(() => {
    if (!data) return [];
    return getEndProducts(data).map((id) => {
      const restored = keyData?.nodes?.[id];
      const label = restored
        ? `${restored.part}@${restored.site}`
        : id.slice(0, 12) + "...";
      const pathCount = data.paths[id]?.length ?? 0;
      return { id, label, pathCount };
    });
  }, [data, keyData]);

  if (products.length === 0) return null;

  return (
    <div className="sidebar-section">
      <h3>End Products ({products.length})</h3>
      <div className="product-list">
        {/* Show All option */}
        <div
          className={`product-item ${selectedProduct === null ? "selected" : ""}`}
          onClick={() => dispatch({ type: "SELECT_PRODUCT", payload: null })}
        >
          All Products
        </div>
        {products.map((p) => (
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
        ))}
      </div>
    </div>
  );
}
