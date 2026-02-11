/**
 * SCAFFOLD SaaS Platform — TypeScript type definitions.
 *
 * These types mirror the upload.json format defined in CLAUDE.md v3.0.
 */

/** Node data in upload.json (all values masked). */
export interface ScaffoldNode {
  stage: string; // S1, S2, S3...
  lt: number; // jittered lead time
  depth: number;
  site: string; // SHA-256 hash of site name
}

/** Edge in upload.json. */
export interface ScaffoldEdge {
  parent: string; // SHA-256 hash
  child: string; // SHA-256 hash
  qty: number; // jittered quantity
}

/** Risk data per node. */
export interface ScaffoldRisk {
  max_lt: number;
  single_source: boolean;
  depth: number;
}

/** Pattern group in upload.json (L1-12). */
export interface ScaffoldPattern {
  site_sequences: string[][]; // masked site hash sequences per path
  products: string[]; // end product hashes sharing this pattern
  depth: number; // max path length
}

/** Supplier impact data in upload.json (L1-14). */
export interface ScaffoldSupplier {
  /** Hashed (part:site) node IDs this supplier feeds into. */
  supplied_nodes: string[];
  /** End product node hashes reachable via backward trace. */
  affected_products: string[];
  /** Count of affected end products. */
  impact_count: number;
}

/** Meta section of upload.json. */
export interface ScaffoldMeta {
  version: string;
  generated: string;
  tier?: string;
  tier_sig?: string;
}

/** Full upload.json structure. */
export interface ScaffoldJSON {
  meta: ScaffoldMeta;
  nodes: Record<string, ScaffoldNode>;
  edges: ScaffoldEdge[];
  paths: Record<string, string[]>;
  patterns: Record<string, ScaffoldPattern>;
  risk: Record<string, ScaffoldRisk>;
  suppliers?: Record<string, ScaffoldSupplier>;
}

/** Decrypted key.scaf mapping data. */
export interface KeyScafData {
  nodes: Record<string, { part: string; site: string; stage: string }>;
  stages: Record<string, string>; // S1 → real stage name
  suppliers?: Record<string, string>; // supplier hash → real supplier name
  [key: string]: unknown;
}

/** Restored node with real labels. */
export interface RestoredNode extends ScaffoldNode {
  realPart?: string;
  realSite?: string;
  realStage?: string;
  realLt?: number;
}

/** Application state for the SCAFFOLD viewer. */
export interface AppState {
  /** Raw parsed upload.json */
  data: ScaffoldJSON | null;
  /** Whether data is loaded */
  loaded: boolean;
  /** Key restore data from key.scaf */
  keyData: KeyScafData | null;
  /** Whether key is restored */
  restored: boolean;
  /** Currently selected end product hash for subgraph/sankey */
  selectedProduct: string | null;
  /** Currently selected supplier hashes for impact view (multi-select) */
  selectedSuppliers: Set<string>;
  /** Active stage filters (checked stages shown) */
  stageFilters: Set<string>;
  /** Active site filters */
  siteFilters: Set<string>;
  /** Depth filter max level */
  depthFilter: number;
  /** Search query */
  searchQuery: string;
  /** View mode */
  viewMode: "graph" | "sankey";
}

/** Stage color palette — S1=blue, S2=green, S3=orange, S4=red, S5=purple, S6=teal */
export const STAGE_COLORS: Record<string, string> = {
  S1: "#4285F4", // blue
  S2: "#34A853", // green
  S3: "#F59E0B", // orange
  S4: "#EA4335", // red
  S5: "#9333EA", // purple
  S6: "#06B6D4", // teal
  S7: "#EC4899", // pink
  S8: "#84CC16", // lime
};

/** Default color for unknown stages. */
export const DEFAULT_STAGE_COLOR = "#6B7280";

/** Get color for a stage. */
export function getStageColor(stage: string): string {
  return STAGE_COLORS[stage] ?? DEFAULT_STAGE_COLOR;
}

/* ── L2-19 to L2-22: BOM Diff / Comparison Types ─────────────── */

/** Status of a node or edge in a diff comparison. */
export type DiffStatus = "added" | "removed" | "unchanged" | "modified";

/** Colors for diff overlay (L2-20). */
export const DIFF_COLORS: Record<DiffStatus, string> = {
  added: "#34A853",    // green — new nodes (L2-22)
  removed: "#EA4335",  // red — deleted nodes (L2-22)
  modified: "#F59E0B", // orange — changed attributes
  unchanged: "#6B7280", // gray — no change
};

/** Per-node diff detail. */
export interface NodeDiff {
  status: DiffStatus;
  /** Delta values — only present when status is "modified". */
  deltaLt?: number;
  deltaDepth?: number;
  oldStage?: string;
  newStage?: string;
}

/** Per-edge diff detail. */
export interface EdgeDiff {
  status: DiffStatus;
  deltaQty?: number;
}

/** Aggregate delta metrics (L2-21). */
export interface DeltaMetrics {
  baselineNodeCount: number;
  targetNodeCount: number;
  addedNodes: number;
  removedNodes: number;
  modifiedNodes: number;
  unchangedNodes: number;
  baselineEdgeCount: number;
  targetEdgeCount: number;
  addedEdges: number;
  removedEdges: number;
  /** Max depth change (target - baseline). */
  deltaMaxDepth: number;
  /** Average risk change across all nodes present in both. */
  deltaAvgRisk: number;
  /** New end products in target. */
  addedProducts: string[];
  /** Removed end products from baseline. */
  removedProducts: string[];
}

/** Full diff result between baseline and target (L2-19). */
export interface DiffResult {
  nodeDiffs: Record<string, NodeDiff>;
  edgeDiffs: Record<string, EdgeDiff>;
  metrics: DeltaMetrics;
}
