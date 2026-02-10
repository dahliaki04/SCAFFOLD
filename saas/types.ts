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
}

/** Decrypted key.scaf mapping data. */
export interface KeyScafData {
  nodes: Record<string, { part: string; site: string; stage: string }>;
  stages: Record<string, string>; // S1 → real stage name
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
