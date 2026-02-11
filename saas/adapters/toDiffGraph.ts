/**
 * L2-20: Diff Overlay Adapter (toDiffGraph).
 * L2-22: New/Deleted Node Highlight.
 *
 * Transforms two SCAFFOLD JSONs + DiffResult into a single graphology Graph
 * with diff-colored nodes and edges for superimposed overlay visualization.
 *
 * Color scheme:
 *   Added   = green (#34A853)  — new in target
 *   Removed = red (#EA4335)    — gone from baseline
 *   Modified = orange (#F59E0B) — attributes changed
 *   Unchanged = gray (#6B7280) — identical in both
 */

import Graph from "graphology";
import type { ScaffoldJSON, DiffResult, KeyScafData } from "../types";
import { DIFF_COLORS } from "../types";

const MIN_NODE_SIZE = 4;
const MAX_NODE_SIZE = 24;

export interface ToDiffGraphOptions {
  /** Key restore data for real labels. */
  keyData?: KeyScafData | null;
  /** Filter: only show nodes with these diff statuses. */
  statusFilter?: Set<string> | null;
}

/**
 * Build a graphology Graph that overlays baseline + target with diff colors.
 *
 * Nodes from both snapshots are merged into one graph. Each node gets a
 * `diffStatus` attribute and is colored accordingly.
 */
export function toDiffGraph(
  baseline: ScaffoldJSON,
  target: ScaffoldJSON,
  diff: DiffResult,
  options: ToDiffGraphOptions = {}
): Graph {
  const { keyData = null, statusFilter = null } = options;

  const graph = new Graph({ type: "directed", multi: false });

  // Compute global max LT across both snapshots for sizing
  let globalMaxLt = 0;
  for (const r of Object.values(baseline.risk)) {
    if (r.max_lt > globalMaxLt) globalMaxLt = r.max_lt;
  }
  for (const r of Object.values(target.risk)) {
    if (r.max_lt > globalMaxLt) globalMaxLt = r.max_lt;
  }

  // Merge all node IDs
  const allNodeIds = new Set([
    ...Object.keys(baseline.nodes),
    ...Object.keys(target.nodes),
  ]);

  for (const nodeId of allNodeIds) {
    const nodeDiff = diff.nodeDiffs[nodeId];
    if (!nodeDiff) continue;

    // Apply status filter
    if (statusFilter && !statusFilter.has(nodeDiff.status)) continue;

    const color = DIFF_COLORS[nodeDiff.status];

    // Use target node data if available, else baseline
    const nodeData = target.nodes[nodeId] ?? baseline.nodes[nodeId];
    const riskData = target.risk[nodeId] ?? baseline.risk[nodeId];
    const riskLt = riskData?.max_lt ?? nodeData.lt;

    const sizeRatio = globalMaxLt > 0 ? riskLt / globalMaxLt : 0.5;
    const size = MIN_NODE_SIZE + sizeRatio * (MAX_NODE_SIZE - MIN_NODE_SIZE);

    // Label
    let label = nodeId.slice(0, 8) + "...";
    if (keyData?.nodes?.[nodeId]) {
      const restored = keyData.nodes[nodeId];
      label = `${restored.part}@${restored.site}`;
    }

    // Status suffix for label
    const statusSuffix =
      nodeDiff.status === "unchanged" ? "" : ` [${nodeDiff.status}]`;

    graph.addNode(nodeId, {
      label: label + statusSuffix,
      x: Math.random() * 1000,
      y: Math.random() * 1000,
      size,
      color,
      stage: nodeData.stage,
      site: nodeData.site,
      depth: nodeData.depth,
      lt: nodeData.lt,
      diffStatus: nodeDiff.status,
      deltaLt: nodeDiff.deltaLt ?? 0,
      deltaDepth: nodeDiff.deltaDepth ?? 0,
    });
  }

  // Merge edges from both snapshots
  const addedEdgeKeys = new Set<string>();

  // Add target edges (these represent the "current" state)
  for (const edge of target.edges) {
    if (!graph.hasNode(edge.parent) || !graph.hasNode(edge.child)) continue;
    const key = `${edge.parent}->${edge.child}`;
    if (addedEdgeKeys.has(key)) continue;
    addedEdgeKeys.add(key);

    const eDiff = diff.edgeDiffs[key];
    const status = eDiff?.status ?? "unchanged";
    const edgeColor = DIFF_COLORS[status as keyof typeof DIFF_COLORS] ?? "#555";

    graph.addEdgeWithKey(key, edge.parent, edge.child, {
      qty: edge.qty,
      size: status === "unchanged" ? 1 : 2,
      color: edgeColor,
      diffStatus: status,
    });
  }

  // Add baseline-only edges (removed edges)
  for (const edge of baseline.edges) {
    const key = `${edge.parent}->${edge.child}`;
    if (addedEdgeKeys.has(key)) continue;
    if (!graph.hasNode(edge.parent) || !graph.hasNode(edge.child)) continue;
    addedEdgeKeys.add(key);

    graph.addEdgeWithKey(key, edge.parent, edge.child, {
      qty: edge.qty,
      size: 2,
      color: DIFF_COLORS.removed,
      diffStatus: "removed",
    });
  }

  return graph;
}
