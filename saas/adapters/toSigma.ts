/**
 * L2-02: Sigma.js Adapter (toSigma).
 *
 * Transforms SCAFFOLD JSON → graphology Graph for Sigma.js rendering.
 *
 * L2-05: Node Color by Stage — S1=blue, S2=green, S3=orange...
 * L2-06: Node Size by Risk (Max LT) — larger = higher Max LT.
 * L2-07: Lazy Loading — default expand 3 levels, track expansion state.
 */

import Graph from "graphology";
import type { ScaffoldJSON, KeyScafData } from "../types";
import { getStageColor } from "../types";

/** Min/max node sizes for risk-based scaling. */
const MIN_NODE_SIZE = 4;
const MAX_NODE_SIZE = 24;

/** Uniform node size when risk-based sizing is disabled. */
const UNIFORM_NODE_SIZE = 8;

/** Default visible depth for lazy loading (L2-07). */
export const DEFAULT_VISIBLE_DEPTH = 3;

export interface ToSigmaOptions {
  /** Max depth to show initially (L2-07 lazy loading). Null = show all. */
  maxVisibleDepth?: number | null;
  /** Filter to only these stages. Null = show all. */
  stageFilter?: Set<string> | null;
  /** Filter to only these sites. Null = show all. */
  siteFilter?: Set<string> | null;
  /** Max depth filter. Null = show all. */
  depthFilter?: number | null;
  /** Subgraph: only show nodes reachable from this end product. */
  subgraphRoot?: string | null;
  /** Key restore data for real labels. */
  keyData?: KeyScafData | null;
  /** Enable risk-based node sizing (L2-06). When false, all nodes use uniform size. */
  nodeSizing?: boolean;
}

/**
 * Build a graphology Graph from SCAFFOLD JSON.
 *
 * This is the core adapter — all rendering decisions flow through here.
 */
export function toSigmaGraph(
  data: ScaffoldJSON,
  options: ToSigmaOptions = {}
): Graph {
  const {
    maxVisibleDepth = null,
    stageFilter = null,
    siteFilter = null,
    depthFilter = null,
    subgraphRoot = null,
    keyData = null,
    nodeSizing = true,
  } = options;

  const graph = new Graph({ type: "directed", multi: false });

  // Compute max lead time for risk-based sizing
  let globalMaxLt = 0;
  for (const r of Object.values(data.risk)) {
    if (r.max_lt > globalMaxLt) globalMaxLt = r.max_lt;
  }

  // If subgraph mode, compute reachable nodes from the selected product
  let reachableNodes: Set<string> | null = null;
  if (subgraphRoot && data.paths[subgraphRoot]) {
    reachableNodes = new Set<string>();
    // Include all nodes on any path from this end product
    for (const pathNodes of Object.values(data.paths)) {
      // paths value is an array of node hashes per path
      // For subgraph, we only want paths from the selected product
    }
    // Walk edges from subgraphRoot via BFS
    reachableNodes = computeReachable(subgraphRoot, data);
  }

  // Add nodes
  for (const [nodeId, nodeData] of Object.entries(data.nodes)) {
    // Apply filters
    if (reachableNodes && !reachableNodes.has(nodeId)) continue;
    if (stageFilter && !stageFilter.has(nodeData.stage)) continue;
    if (siteFilter && !siteFilter.has(nodeData.site)) continue;
    if (depthFilter !== null && nodeData.depth > depthFilter) continue;
    if (maxVisibleDepth !== null && nodeData.depth > maxVisibleDepth) continue;

    // L2-05: Color by stage
    const color = getStageColor(
      keyData?.stages?.[nodeData.stage] ? nodeData.stage : nodeData.stage
    );

    // L2-06: Size by max lead time risk (toggleable)
    const risk = data.risk[nodeId];
    const riskLt = risk?.max_lt ?? nodeData.lt;
    let size: number;
    if (nodeSizing) {
      const sizeRatio = globalMaxLt > 0 ? riskLt / globalMaxLt : 0.5;
      size = MIN_NODE_SIZE + sizeRatio * (MAX_NODE_SIZE - MIN_NODE_SIZE);
    } else {
      size = UNIFORM_NODE_SIZE;
    }

    // Label: use restored name if available, otherwise hash prefix
    let label = nodeId.slice(0, 8) + "...";
    if (keyData?.nodes?.[nodeId]) {
      const restored = keyData.nodes[nodeId];
      label = `${restored.part}@${restored.site}`;
    }

    graph.addNode(nodeId, {
      label,
      x: Math.random() * 1000,
      y: Math.random() * 1000,
      size,
      color,
      stage: nodeData.stage,
      site: nodeData.site,
      depth: nodeData.depth,
      lt: nodeData.lt,
      riskLt: riskLt,
      singleSource: risk?.single_source ?? false,
    });
  }

  // Add edges
  for (const edge of data.edges) {
    if (graph.hasNode(edge.parent) && graph.hasNode(edge.child)) {
      const edgeKey = `${edge.parent}->${edge.child}`;
      if (!graph.hasEdge(edgeKey)) {
        graph.addEdgeWithKey(edgeKey, edge.parent, edge.child, {
          qty: edge.qty,
          size: 1,
          color: "#555",
        });
      }
    }
  }

  return graph;
}

/**
 * Compute set of reachable nodes from a start node via BFS (L2-14).
 */
function computeReachable(
  startId: string,
  data: ScaffoldJSON
): Set<string> {
  const reachable = new Set<string>();

  // Build adjacency list from edges
  const children = new Map<string, string[]>();
  for (const edge of data.edges) {
    if (!children.has(edge.parent)) children.set(edge.parent, []);
    children.get(edge.parent)!.push(edge.child);
  }

  // BFS (index-based to avoid O(n) shift)
  const queue = [startId];
  let head = 0;
  while (head < queue.length) {
    const current = queue[head++];
    if (reachable.has(current)) continue;
    reachable.add(current);
    for (const child of children.get(current) ?? []) {
      if (!reachable.has(child)) queue.push(child);
    }
  }

  return reachable;
}

/**
 * Get count of nodes that would be visible with given options.
 */
export function countVisibleNodes(
  data: ScaffoldJSON,
  options: ToSigmaOptions = {}
): number {
  const {
    maxVisibleDepth = null,
    stageFilter = null,
    siteFilter = null,
    depthFilter = null,
    subgraphRoot = null,
  } = options;

  let reachableNodes: Set<string> | null = null;
  if (subgraphRoot) {
    reachableNodes = computeReachable(subgraphRoot, data);
  }

  let count = 0;
  for (const [nodeId, nodeData] of Object.entries(data.nodes)) {
    if (reachableNodes && !reachableNodes.has(nodeId)) continue;
    if (stageFilter && !stageFilter.has(nodeData.stage)) continue;
    if (siteFilter && !siteFilter.has(nodeData.site)) continue;
    if (depthFilter !== null && nodeData.depth > depthFilter) continue;
    if (maxVisibleDepth !== null && nodeData.depth > maxVisibleDepth) continue;
    count++;
  }
  return count;
}
