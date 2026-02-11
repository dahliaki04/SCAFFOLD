/**
 * L2-20: Diff Overlay — Superimposed graph comparison.
 * L2-22: New/Deleted Node Highlight.
 *
 * Sigma.js WebGL renderer showing baseline vs target BOM overlay.
 * Color scheme: green=added, red=removed, orange=modified, gray=unchanged.
 */

import { useEffect, useRef, useMemo, useCallback, useState } from "react";
import Graph from "graphology";
import Sigma from "sigma";
import { useScaffold } from "../context/ScaffoldContext";
import { toDiffGraph } from "../adapters/toDiffGraph";
import { DIFF_COLORS, type DiffStatus } from "../types";

export function DiffView() {
  const containerRef = useRef<HTMLDivElement>(null);
  const sigmaRef = useRef<Sigma | null>(null);
  const {
    baselineData,
    targetData,
    diffResult,
    keyData,
    diffStatusFilter,
    searchQuery,
  } = useScaffold();

  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  // Build the diff graph
  const graph = useMemo(() => {
    if (!baselineData || !targetData || !diffResult) {
      return new Graph({ type: "directed" });
    }

    return toDiffGraph(baselineData, targetData, diffResult, {
      keyData,
      statusFilter: diffStatusFilter,
    });
  }, [baselineData, targetData, diffResult, keyData, diffStatusFilter]);

  // Depth-based layout
  useEffect(() => {
    if (graph.order === 0) return;

    const nodes = graph.nodes();
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

    sigma.on("enterNode", ({ node }) => setHoveredNode(node));
    sigma.on("leaveNode", () => setHoveredNode(null));

    sigmaRef.current = sigma;

    return () => {
      sigma.kill();
      sigmaRef.current = null;
    };
  }, [graph]);

  // Hover highlight: show connected nodes for hovered node
  useEffect(() => {
    const sigma = sigmaRef.current;
    if (!sigma) return;

    if (hoveredNode) {
      const neighbors = new Set<string>();
      neighbors.add(hoveredNode);
      graph.forEachNeighbor(hoveredNode, (neighbor) => {
        neighbors.add(neighbor);
      });

      sigma.setSetting("nodeReducer", (node, data) => {
        if (node === hoveredNode) {
          return { ...data, zIndex: 2, highlighted: true };
        }
        if (neighbors.has(node)) {
          return { ...data, zIndex: 1 };
        }
        return { ...data, color: "#2a2d35", label: "", zIndex: 0 };
      });
      sigma.setSetting("edgeReducer", (edge, data) => {
        const source = graph.source(edge);
        const target = graph.target(edge);
        if (neighbors.has(source) && neighbors.has(target)) {
          return { ...data, size: 2 };
        }
        return { ...data, color: "#1a1d22", size: 0.5 };
      });
    } else {
      sigma.setSetting("nodeReducer", null);
      sigma.setSetting("edgeReducer", null);
    }

    sigma.refresh();
  }, [hoveredNode, graph]);

  // Search highlight
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

  if (!diffResult) {
    return (
      <div className="no-product-selected">
        Upload baseline and target JSON files to view diff overlay
      </div>
    );
  }

  return (
    <div className="diff-view-container">
      <div ref={containerRef} className="graph-container" />
      {/* Diff legend overlay */}
      <div className="diff-legend">
        {(Object.entries(DIFF_COLORS) as [DiffStatus, string][]).map(
          ([status, color]) => (
            <div key={status} className="diff-legend-item">
              <span
                className="diff-legend-dot"
                style={{ background: color }}
              />
              <span className="diff-legend-label">
                {status.charAt(0).toUpperCase() + status.slice(1)}
              </span>
            </div>
          )
        )}
      </div>
    </div>
  );
}
