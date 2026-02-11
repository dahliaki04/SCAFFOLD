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

/** Highlight color for the path-to-end-product chain. */
const PATH_HIGHLIGHT_COLOR = "#38BDF8"; // sky-blue accent

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
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

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
    sigma.on("clickNode", ({ node }) => {
      setSelectedNode((prev) => (prev === node ? null : node));
    });
    sigma.on("clickStage", () => setSelectedNode(null));

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

  // Highlight: hover shows immediate neighbors, click shows full path chain
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

      sigma.setSetting("nodeReducer", (node, data) => {
        if (node === activeNode) {
          return {
            ...data,
            zIndex: 2,
            highlighted: true,
            color: selectedNode ? PATH_HIGHLIGHT_COLOR : data.color,
          };
        }
        if (highlighted.has(node)) {
          return { ...data, zIndex: 1 };
        }
        return { ...data, color: "#2a2d35", label: "", zIndex: 0 };
      });
      sigma.setSetting("edgeReducer", (edge, data) => {
        const source = graph.source(edge);
        const target = graph.target(edge);
        if (highlighted.has(source) && highlighted.has(target)) {
          return { ...data, size: 2 };
        }
        return { ...data, color: "#1a1d22", size: 0.5 };
      });
    } else {
      sigma.setSetting("nodeReducer", null);
      sigma.setSetting("edgeReducer", null);
    }

    sigma.refresh();
  }, [hoveredNode, selectedNode, graph, getFullChain]);

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
