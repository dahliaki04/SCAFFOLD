/**
 * L2-04: Sigma.js WebGL Renderer.
 * L2-05: Node Color by Stage.
 * L2-06: Node Size by Risk (Max LT).
 * L2-07: Lazy Loading (1000 nodes max).
 * L2-08: Semantic Zoom (P1).
 * L2-09: Hover Highlight Neighbors.
 *
 * Main graph visualization component using Sigma.js + graphology.
 *
 * Layout: spine-based — main path as straight horizontal line,
 * branch nodes (components added at a site) placed below.
 * Pattern-consolidated overview groups products by pattern.
 * Branches are foldable via toggle switch.
 */

import { useEffect, useRef, useMemo, useCallback, useState } from "react";
import Graph from "graphology";
import Sigma from "sigma";
import { useScaffold } from "../context/ScaffoldContext";
import { toSigmaGraph, DEFAULT_VISIBLE_DEPTH } from "../adapters/toSigma";

/**
 * Extract paths as string[][] from data.paths[productId],
 * handling both string[] (spec) and string[][] (actual demo) formats.
 */
function getProductPaths(rawPaths: unknown): string[][] {
  if (!Array.isArray(rawPaths) || rawPaths.length === 0) return [];
  if (Array.isArray(rawPaths[0])) return rawPaths as string[][];
  return [rawPaths as string[]];
}

export function GraphView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const sigmaRef = useRef<Sigma | null>(null);
  const {
    data,
    stageFilters,
    siteFilters,
    depthFilter,
    selectedProduct,
    searchQuery,
    keyData,
  } = useScaffold();

  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [branchesFolded, setBranchesFolded] = useState(false);

  // Compute representative products for pattern-consolidated view.
  // When no product is selected and patterns exist, pick one product per pattern.
  const representativeRoots = useMemo(() => {
    if (selectedProduct || !data?.patterns || !data?.paths) return null;
    const patterns = Object.values(data.patterns);
    if (patterns.length === 0) return null;

    const reps: string[] = [];
    const coveredProducts = new Set<string>();

    for (const pat of patterns) {
      if (pat.products.length > 0) {
        reps.push(pat.products[0]);
        for (const p of pat.products) coveredProducts.add(p);
      }
    }

    // Include products not covered by any pattern
    for (const productId of Object.keys(data.paths)) {
      if (!coveredProducts.has(productId)) {
        reps.push(productId);
      }
    }

    return reps.length > 0 ? reps : null;
  }, [selectedProduct, data]);

  // Build graph with current filters
  const graph = useMemo(() => {
    if (!data) return new Graph({ type: "directed" });

    const totalNodes = Object.keys(data.nodes).length;
    // L2-07: Lazy loading — limit to DEFAULT_VISIBLE_DEPTH if > 1000 nodes
    const maxDepth =
      totalNodes > 1000 && !selectedProduct
        ? DEFAULT_VISIBLE_DEPTH
        : null;

    return toSigmaGraph(data, {
      maxVisibleDepth: maxDepth,
      stageFilter: stageFilters,
      siteFilter: siteFilters,
      depthFilter: depthFilter === Infinity ? null : depthFilter,
      subgraphRoot: selectedProduct,
      representativeRoots,
      keyData,
    });
  }, [
    data,
    stageFilters,
    siteFilters,
    depthFilter,
    selectedProduct,
    representativeRoots,
    keyData,
  ]);

  // Spine-based layout: main path as straight line, branches below.
  // Marks each node with isSpine attribute for fold toggle.
  // In pattern mode (no product selected), each pattern gets its own row.
  useEffect(() => {
    if (graph.order === 0 || !data) return;

    const layerWidth = 200;
    const positioned = new Set<string>();

    // Build spine (longest path) per product from paths data
    const productSpines = new Map<string, string[]>();
    const productAllNodes = new Map<string, Set<string>>();

    for (const [productId, rawPaths] of Object.entries(data.paths)) {
      const paths = getProductPaths(rawPaths);
      let longestPath: string[] = [];
      const nodeSet = new Set<string>();

      for (const path of paths) {
        if (Array.isArray(path)) {
          for (const nodeId of path) {
            if (graph.hasNode(nodeId)) nodeSet.add(nodeId);
          }
          if (path.length > longestPath.length) longestPath = path;
        }
      }

      productSpines.set(
        productId,
        longestPath.filter((n) => graph.hasNode(n))
      );
      productAllNodes.set(productId, nodeSet);
    }

    /**
     * Layout a single product's subgraph: spine on straight line at rowY,
     * branch nodes below. Marks nodes with isSpine attribute.
     */
    function layoutProductSubgraph(
      productId: string,
      rowY: number
    ): number {
      const spine = productSpines.get(productId) ?? [];
      const allNodes = productAllNodes.get(productId) ?? new Set<string>();

      // Build depth→spine x mapping for branch alignment
      const depthToSpineX = new Map<number, number>();

      // Position spine nodes on a straight horizontal line
      spine.forEach((nodeId, idx) => {
        if (positioned.has(nodeId)) return;
        const x = idx * layerWidth;
        graph.setNodeAttribute(nodeId, "x", x);
        graph.setNodeAttribute(nodeId, "y", rowY);
        graph.setNodeAttribute(nodeId, "isSpine", true);
        positioned.add(nodeId);

        const d = graph.getNodeAttribute(nodeId, "depth") ?? 0;
        if (!depthToSpineX.has(d)) depthToSpineX.set(d, x);
      });

      // Collect branch nodes (not on spine) grouped by depth
      const branchByDepth = new Map<number, string[]>();
      for (const nodeId of allNodes) {
        if (positioned.has(nodeId)) continue;
        const depth = graph.getNodeAttribute(nodeId, "depth") ?? 0;
        if (!branchByDepth.has(depth)) branchByDepth.set(depth, []);
        branchByDepth.get(depth)!.push(nodeId);
      }

      // Position branch nodes below the spine
      let maxBranchRows = 0;
      const sortedBranchDepths = Array.from(branchByDepth.keys()).sort(
        (a, b) => a - b
      );
      for (const depth of sortedBranchDepths) {
        const nodes = branchByDepth.get(depth)!;
        // Align x with spine node at same depth, or fall back to depth * layerWidth
        const x = depthToSpineX.get(depth) ?? depth * layerWidth;

        nodes.forEach((nodeId, i) => {
          graph.setNodeAttribute(nodeId, "x", x);
          graph.setNodeAttribute(nodeId, "y", rowY + 80 + i * 60);
          graph.setNodeAttribute(nodeId, "isSpine", false);
          positioned.add(nodeId);
        });
        maxBranchRows = Math.max(maxBranchRows, nodes.length);
      }

      // Return total height used by this row (spine + branches + gap)
      return 80 + maxBranchRows * 60 + 100;
    }

    const patterns = data.patterns ?? {};
    const patternIds = Object.keys(patterns).sort();

    if (patternIds.length > 0 && !selectedProduct) {
      // === Pattern-consolidated layout ===
      // Each pattern in its own row, spine as straight line, branches below
      let currentRowY = 0;

      for (const patId of patternIds) {
        const pat = patterns[patId];
        const rep = pat.products[0];
        if (!rep || !productSpines.has(rep)) continue;

        const rowHeight = layoutProductSubgraph(rep, currentRowY);
        currentRowY += rowHeight;
      }

      // Layout orphan products (not in any pattern)
      const coveredProducts = new Set<string>();
      for (const pat of Object.values(patterns)) {
        for (const p of pat.products) coveredProducts.add(p);
      }
      for (const productId of Object.keys(data.paths)) {
        if (coveredProducts.has(productId)) continue;
        if (!productSpines.has(productId)) continue;
        const rowHeight = layoutProductSubgraph(productId, currentRowY);
        currentRowY += rowHeight;
      }
    } else if (selectedProduct) {
      // === Single product selected — one spine ===
      layoutProductSubgraph(selectedProduct, 0);
    } else {
      // === Fallback: no patterns, no product selected ===
      // Use longest spine across all products
      let bestProduct = "";
      let bestLen = 0;
      for (const [pid, spine] of productSpines) {
        if (spine.length > bestLen) {
          bestLen = spine.length;
          bestProduct = pid;
        }
      }
      if (bestProduct) {
        layoutProductSubgraph(bestProduct, 0);
      }
    }

    // Position any remaining unpositioned nodes (safety net)
    const remaining = graph.nodes().filter((n) => !positioned.has(n));
    if (remaining.length > 0) {
      const startX =
        Math.max(
          ...graph
            .nodes()
            .filter((n) => positioned.has(n))
            .map((n) => graph.getNodeAttribute(n, "x") as number),
          0
        ) + layerWidth;
      remaining.forEach((nodeId, i) => {
        graph.setNodeAttribute(nodeId, "x", startX);
        graph.setNodeAttribute(nodeId, "y", i * 60);
        graph.setNodeAttribute(nodeId, "isSpine", false);
      });
    }
  }, [graph, data, selectedProduct]);

  // Initialize and update Sigma
  useEffect(() => {
    if (!containerRef.current) return;

    // Dispose previous instance
    if (sigmaRef.current) {
      sigmaRef.current.kill();
      sigmaRef.current = null;
    }

    if (graph.order === 0) return;

    const sigma = new Sigma(graph, containerRef.current, {
      allowInvalidContainer: true,
      renderEdgeLabels: false,
      defaultEdgeType: "arrow",
      labelRenderedSizeThreshold: 8,
      labelFont: "monospace",
      labelSize: 11,
      labelColor: { color: "#e4e6eb" },
      defaultNodeColor: "#6B7280",
      defaultEdgeColor: "#444",
      stagePadding: 30,
    });

    // L2-09: Hover Highlight Neighbors
    sigma.on("enterNode", ({ node }) => {
      setHoveredNode(node);
    });
    sigma.on("leaveNode", () => {
      setHoveredNode(null);
    });

    // Click node: select and highlight full upstream/downstream chain
    sigma.on("clickNode", ({ node }) => {
      setSelectedNode((prev) => (prev === node ? null : node));
    });
    sigma.on("clickStage", () => {
      setSelectedNode(null);
    });

    // L2-08: Semantic Zoom — show more details on zoom in
    // Sigma handles this natively via labelRenderedSizeThreshold

    sigmaRef.current = sigma;

    return () => {
      sigma.kill();
      sigmaRef.current = null;
    };
  }, [graph]);

  // Compute full upstream + downstream chain via iterative BFS
  const getFullChain = useCallback(
    (startNode: string): Set<string> => {
      const related = new Set<string>();
      related.add(startNode);

      // BFS upstream (predecessors via in-neighbors)
      const upQueue = [startNode];
      while (upQueue.length > 0) {
        const current = upQueue.shift()!;
        graph.forEachInNeighbor(current, (neighbor) => {
          if (!related.has(neighbor)) {
            related.add(neighbor);
            upQueue.push(neighbor);
          }
        });
      }

      // BFS downstream (successors via out-neighbors)
      const downQueue = [startNode];
      while (downQueue.length > 0) {
        const current = downQueue.shift()!;
        graph.forEachOutNeighbor(current, (neighbor) => {
          if (!related.has(neighbor)) {
            related.add(neighbor);
            downQueue.push(neighbor);
          }
        });
      }

      return related;
    },
    [graph]
  );

  // Combined reducer: fold branches + highlight (hover/click)
  useEffect(() => {
    const sigma = sigmaRef.current;
    if (!sigma) return;

    const activeNode = selectedNode ?? hoveredNode;
    const needsReducer = branchesFolded || activeNode;

    if (needsReducer) {
      // Pre-compute highlighted set if a node is active
      let highlighted: Set<string> | null = null;
      if (activeNode) {
        highlighted = selectedNode
          ? getFullChain(activeNode)
          : (() => {
              const neighbors = new Set<string>();
              neighbors.add(activeNode);
              graph.forEachNeighbor(activeNode, (neighbor) => {
                neighbors.add(neighbor);
              });
              return neighbors;
            })();
      }

      sigma.setSetting("nodeReducer", (node, attrs) => {
        const isSpine = graph.getNodeAttribute(node, "isSpine");

        // Fold: hide branch nodes
        if (branchesFolded && isSpine === false) {
          return { ...attrs, hidden: true };
        }

        // Highlight
        if (highlighted) {
          if (node === activeNode) {
            return { ...attrs, zIndex: 2, highlighted: true };
          }
          if (highlighted.has(node)) {
            return { ...attrs, zIndex: 1 };
          }
          return { ...attrs, color: "#2a2d35", label: "", zIndex: 0 };
        }

        return attrs;
      });

      sigma.setSetting("edgeReducer", (edge, attrs) => {
        const source = graph.source(edge);
        const target = graph.target(edge);

        // Fold: hide edges connected to branch nodes
        if (branchesFolded) {
          const sourceIsSpine = graph.getNodeAttribute(source, "isSpine");
          const targetIsSpine = graph.getNodeAttribute(target, "isSpine");
          if (sourceIsSpine === false || targetIsSpine === false) {
            return { ...attrs, hidden: true };
          }
        }

        // Highlight
        if (highlighted) {
          if (highlighted.has(source) && highlighted.has(target)) {
            return { ...attrs, color: "#888", size: 2 };
          }
          return { ...attrs, color: "#1a1d22", size: 0.5 };
        }

        return attrs;
      });
    } else {
      sigma.setSetting("nodeReducer", null);
      sigma.setSetting("edgeReducer", null);
    }

    sigma.refresh();
  }, [hoveredNode, selectedNode, branchesFolded, graph, getFullChain]);

  // Highlight searched node
  useEffect(() => {
    const sigma = sigmaRef.current;
    if (!sigma || !searchQuery) return;

    const q = searchQuery.toLowerCase();
    const matchId = graph.nodes().find((id) => {
      const label = graph.getNodeAttribute(id, "label") ?? "";
      return (
        id.toLowerCase().startsWith(q) || label.toLowerCase().includes(q)
      );
    });

    if (matchId) {
      const attrs = graph.getNodeAttributes(matchId);
      sigma.getCamera().animate(
        { x: attrs.x, y: attrs.y, ratio: 0.3 },
        { duration: 300 }
      );
    }
  }, [searchQuery, graph]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <div
        style={{
          position: "absolute",
          top: 8,
          right: 8,
          zIndex: 10,
          display: "flex",
          alignItems: "center",
          gap: 8,
          background: "var(--bg-secondary, #1a1d27)",
          border: "1px solid var(--border, #333640)",
          borderRadius: 6,
          padding: "6px 12px",
          fontSize: 13,
          color: "var(--text-secondary, #9ca3af)",
          userSelect: "none",
        }}
      >
        <span>Fold branches</span>
        <button
          onClick={() => setBranchesFolded((prev) => !prev)}
          style={{
            width: 36,
            height: 20,
            borderRadius: 10,
            border: "none",
            cursor: "pointer",
            position: "relative",
            background: branchesFolded
              ? "var(--accent, #4285f4)"
              : "var(--bg-tertiary, #252830)",
            transition: "background 0.2s",
          }}
        >
          <span
            style={{
              position: "absolute",
              top: 2,
              left: branchesFolded ? 18 : 2,
              width: 16,
              height: 16,
              borderRadius: "50%",
              background: "#fff",
              transition: "left 0.2s",
            }}
          />
        </button>
      </div>
      <div ref={containerRef} className="graph-container" />
    </div>
  );
}
