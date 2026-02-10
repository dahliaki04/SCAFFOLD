/**
 * L2-04: Sigma.js WebGL Renderer.
 * L2-05: Node Color by Stage.
 * L2-06: Node Size by Risk (Max LT).
 * L2-07: Lazy Loading (1000 nodes max).
 * L2-08: Semantic Zoom (P1).
 * L2-09: Hover Highlight Neighbors.
 *
 * Main graph visualization component using Sigma.js + graphology.
 */

import { useEffect, useRef, useMemo, useCallback, useState } from "react";
import Graph from "graphology";
import Sigma from "sigma";
import { useScaffold } from "../context/ScaffoldContext";
import { toSigmaGraph, DEFAULT_VISIBLE_DEPTH } from "../adapters/toSigma";

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
    nodeSizing,
  } = useScaffold();

  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // L1-12: Build product-to-pattern lookup for pattern-aware highlighting
  const patternPeers = useMemo(() => {
    if (!data?.patterns) return new Map<string, Set<string>>();
    const map = new Map<string, Set<string>>();
    for (const pattern of Object.values(data.patterns)) {
      const peerSet = new Set(pattern.products);
      for (const prodId of pattern.products) {
        map.set(prodId, peerSet);
      }
    }
    return map;
  }, [data]);

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
      keyData,
      nodeSizing,
    });
  }, [data, stageFilters, siteFilters, depthFilter, selectedProduct, keyData, nodeSizing]);

  // Apply force-directed layout
  useEffect(() => {
    if (graph.order === 0) return;

    // Simple force-directed layout using circular initial positions
    const nodes = graph.nodes();
    const n = nodes.length;

    // Arrange by depth layers for better visualization
    const depthGroups = new Map<number, string[]>();
    nodes.forEach((nodeId) => {
      const depth = graph.getNodeAttribute(nodeId, "depth") ?? 0;
      if (!depthGroups.has(depth)) depthGroups.set(depth, []);
      depthGroups.get(depth)!.push(nodeId);
    });

    const sortedDepths = Array.from(depthGroups.keys()).sort((a, b) => a - b);
    const layerWidth = 200;

    sortedDepths.forEach((depth, layerIdx) => {
      const nodesInLayer = depthGroups.get(depth)!;
      const layerHeight = nodesInLayer.length * 60;
      nodesInLayer.forEach((nodeId, i) => {
        graph.setNodeAttribute(
          nodeId,
          "x",
          layerIdx * layerWidth + (Math.random() - 0.5) * 40
        );
        graph.setNodeAttribute(
          nodeId,
          "y",
          (i - nodesInLayer.length / 2) * 60 + (Math.random() - 0.5) * 20
        );
      });
    });
  }, [graph]);

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

  // L2-09: Highlight effect — hover shows immediate neighbors, click shows full chain
  useEffect(() => {
    const sigma = sigmaRef.current;
    if (!sigma) return;

    // Click selection takes priority over hover
    const activeNode = selectedNode ?? hoveredNode;

    if (activeNode) {
      const highlighted = selectedNode
        ? getFullChain(activeNode)
        : (() => {
            const neighbors = new Set<string>();
            neighbors.add(activeNode);
            graph.forEachNeighbor(activeNode, (neighbor) => {
              neighbors.add(neighbor);
            });
            return neighbors;
          })();

      // L1-12: Pattern peers — other end products sharing the same structural pattern
      const peers = selectedNode ? (patternPeers.get(activeNode) ?? new Set()) : new Set();

      sigma.setSetting("nodeReducer", (node, data) => {
        if (node === activeNode) {
          return { ...data, zIndex: 2, highlighted: true };
        }
        if (highlighted.has(node)) {
          return { ...data, zIndex: 1 };
        }
        // Pattern peers get a distinct accent to show structural similarity
        if (peers.has(node) && graph.hasNode(node)) {
          return { ...data, zIndex: 1, color: "#F59E0B", borderColor: "#F59E0B" };
        }
        return { ...data, color: "#2a2d35", label: "", zIndex: 0 };
      });
      sigma.setSetting("edgeReducer", (edge, data) => {
        const source = graph.source(edge);
        const target = graph.target(edge);
        if (highlighted.has(source) && highlighted.has(target)) {
          return { ...data, color: "#888", size: 2 };
        }
        return { ...data, color: "#1a1d22", size: 0.5 };
      });
    } else {
      sigma.setSetting("nodeReducer", null);
      sigma.setSetting("edgeReducer", null);
    }

    sigma.refresh();
  }, [hoveredNode, selectedNode, graph, getFullChain, patternPeers]);

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

  return <div ref={containerRef} className="graph-container" />;
}
