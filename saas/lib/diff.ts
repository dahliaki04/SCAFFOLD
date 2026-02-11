/**
 * L2-19: BOM Diff Computation.
 * L2-21: Delta Metrics (ΔDepth, ΔRisk).
 * L2-22: New/Deleted Node classification.
 *
 * Compares two SCAFFOLD upload.json objects and produces a structured diff
 * with per-node status, per-edge status, and aggregate delta metrics.
 */

import type {
  ScaffoldJSON,
  DiffResult,
  NodeDiff,
  EdgeDiff,
  DeltaMetrics,
  DiffStatus,
} from "../types";
import { getMaxDepth } from "./parser";

/** Canonical edge key used for diff comparison. */
function edgeKey(parent: string, child: string): string {
  return `${parent}->${child}`;
}

/**
 * Compute a full structural diff between baseline and target BOM snapshots.
 *
 * Node matching is by hash ID (SHA-256 of PartName+SiteID), so nodes that
 * exist in both snapshots with the same hash are compared attribute-by-attribute.
 */
export function computeDiff(
  baseline: ScaffoldJSON,
  target: ScaffoldJSON
): DiffResult {
  const nodeDiffs: Record<string, NodeDiff> = {};
  const edgeDiffs: Record<string, EdgeDiff> = {};

  const baselineNodeIds = new Set(Object.keys(baseline.nodes));
  const targetNodeIds = new Set(Object.keys(target.nodes));

  // All node IDs across both snapshots
  const allNodeIds = new Set([...baselineNodeIds, ...targetNodeIds]);

  let addedNodes = 0;
  let removedNodes = 0;
  let modifiedNodes = 0;
  let unchangedNodes = 0;
  let riskDeltaSum = 0;
  let riskDeltaCount = 0;

  for (const nodeId of allNodeIds) {
    const inBaseline = baselineNodeIds.has(nodeId);
    const inTarget = targetNodeIds.has(nodeId);

    if (inBaseline && !inTarget) {
      // L2-22: Removed node (red)
      nodeDiffs[nodeId] = { status: "removed" };
      removedNodes++;
    } else if (!inBaseline && inTarget) {
      // L2-22: Added node (green)
      nodeDiffs[nodeId] = { status: "added" };
      addedNodes++;
    } else {
      // Present in both — check for modifications
      const bNode = baseline.nodes[nodeId];
      const tNode = target.nodes[nodeId];

      const deltaLt = tNode.lt - bNode.lt;
      const deltaDepth = tNode.depth - bNode.depth;
      const stageChanged = tNode.stage !== bNode.stage;

      if (deltaLt !== 0 || deltaDepth !== 0 || stageChanged) {
        const diff: NodeDiff = {
          status: "modified",
          deltaLt,
          deltaDepth,
        };
        if (stageChanged) {
          diff.oldStage = bNode.stage;
          diff.newStage = tNode.stage;
        }
        nodeDiffs[nodeId] = diff;
        modifiedNodes++;
      } else {
        nodeDiffs[nodeId] = { status: "unchanged" };
        unchangedNodes++;
      }

      // L2-21: Risk delta for nodes present in both
      const bRisk = baseline.risk[nodeId]?.max_lt ?? bNode.lt;
      const tRisk = target.risk[nodeId]?.max_lt ?? tNode.lt;
      riskDeltaSum += tRisk - bRisk;
      riskDeltaCount++;
    }
  }

  // Edge diff
  const baselineEdgeMap = new Map<string, number>();
  for (const e of baseline.edges) {
    baselineEdgeMap.set(edgeKey(e.parent, e.child), e.qty);
  }

  const targetEdgeMap = new Map<string, number>();
  for (const e of target.edges) {
    targetEdgeMap.set(edgeKey(e.parent, e.child), e.qty);
  }

  const allEdgeKeys = new Set([
    ...baselineEdgeMap.keys(),
    ...targetEdgeMap.keys(),
  ]);

  let addedEdges = 0;
  let removedEdges = 0;

  for (const key of allEdgeKeys) {
    const inBase = baselineEdgeMap.has(key);
    const inTgt = targetEdgeMap.has(key);

    if (inBase && !inTgt) {
      edgeDiffs[key] = { status: "removed" };
      removedEdges++;
    } else if (!inBase && inTgt) {
      edgeDiffs[key] = { status: "added" };
      addedEdges++;
    } else {
      const bQty = baselineEdgeMap.get(key)!;
      const tQty = targetEdgeMap.get(key)!;
      if (bQty !== tQty) {
        edgeDiffs[key] = { status: "modified", deltaQty: tQty - bQty };
      } else {
        edgeDiffs[key] = { status: "unchanged" };
      }
    }
  }

  // Product diff
  const baselineProducts = new Set(Object.keys(baseline.paths));
  const targetProducts = new Set(Object.keys(target.paths));

  const addedProducts: string[] = [];
  const removedProducts: string[] = [];

  for (const p of targetProducts) {
    if (!baselineProducts.has(p)) addedProducts.push(p);
  }
  for (const p of baselineProducts) {
    if (!targetProducts.has(p)) removedProducts.push(p);
  }

  // L2-21: Aggregate delta metrics
  const metrics: DeltaMetrics = {
    baselineNodeCount: baselineNodeIds.size,
    targetNodeCount: targetNodeIds.size,
    addedNodes,
    removedNodes,
    modifiedNodes,
    unchangedNodes,
    baselineEdgeCount: baseline.edges.length,
    targetEdgeCount: target.edges.length,
    addedEdges,
    removedEdges,
    deltaMaxDepth: getMaxDepth(target) - getMaxDepth(baseline),
    deltaAvgRisk: riskDeltaCount > 0 ? riskDeltaSum / riskDeltaCount : 0,
    addedProducts,
    removedProducts,
  };

  return { nodeDiffs, edgeDiffs, metrics };
}
