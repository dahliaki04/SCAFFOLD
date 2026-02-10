/**
 * L2-01: SCAFFOLD JSON Parser.
 *
 * Reads upload.json into a validated standard in-memory object.
 * Performs structural validation before returning typed data.
 */

import type { ScaffoldJSON } from "../types";

const REQUIRED_TOP_KEYS = ["meta", "nodes", "edges", "paths", "risk"] as const;
const SUPPORTED_VERSIONS = ["3.0"];

export class ParseError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ParseError";
  }
}

/**
 * Parse and validate a SCAFFOLD upload.json string or object.
 */
export function parseScaffoldJSON(input: string | object): ScaffoldJSON {
  let data: unknown;

  if (typeof input === "string") {
    try {
      data = JSON.parse(input);
    } catch {
      throw new ParseError("Invalid JSON: failed to parse input string");
    }
  } else {
    data = input;
  }

  if (typeof data !== "object" || data === null || Array.isArray(data)) {
    throw new ParseError("Invalid SCAFFOLD JSON: top-level must be an object");
  }

  const obj = data as Record<string, unknown>;

  // Check required top-level keys
  for (const key of REQUIRED_TOP_KEYS) {
    if (!(key in obj)) {
      throw new ParseError(`Missing required key: "${key}"`);
    }
  }

  // Validate meta
  const meta = obj.meta as Record<string, unknown>;
  if (typeof meta !== "object" || meta === null) {
    throw new ParseError('Invalid "meta" section');
  }
  if (typeof meta.version !== "string") {
    throw new ParseError("meta.version must be a string");
  }
  if (!SUPPORTED_VERSIONS.includes(meta.version)) {
    throw new ParseError(
      `Unsupported version "${meta.version}". Supported: ${SUPPORTED_VERSIONS.join(", ")}`
    );
  }

  // Validate nodes
  const nodes = obj.nodes;
  if (typeof nodes !== "object" || nodes === null || Array.isArray(nodes)) {
    throw new ParseError('"nodes" must be an object');
  }

  // Validate edges
  const edges = obj.edges;
  if (!Array.isArray(edges)) {
    throw new ParseError('"edges" must be an array');
  }

  // Validate paths
  const paths = obj.paths;
  if (typeof paths !== "object" || paths === null || Array.isArray(paths)) {
    throw new ParseError('"paths" must be an object');
  }

  // Validate risk
  const risk = obj.risk;
  if (typeof risk !== "object" || risk === null || Array.isArray(risk)) {
    throw new ParseError('"risk" must be an object');
  }

  return data as ScaffoldJSON;
}

/**
 * Extract unique stages from parsed SCAFFOLD data.
 */
export function extractStages(data: ScaffoldJSON): string[] {
  const stages = new Set<string>();
  for (const node of Object.values(data.nodes)) {
    stages.add(node.stage);
  }
  return Array.from(stages).sort();
}

/**
 * Extract unique sites from parsed SCAFFOLD data.
 */
export function extractSites(data: ScaffoldJSON): string[] {
  const sites = new Set<string>();
  for (const node of Object.values(data.nodes)) {
    sites.add(node.site);
  }
  return Array.from(sites).sort();
}

/**
 * Get the maximum depth across all nodes.
 */
export function getMaxDepth(data: ScaffoldJSON): number {
  let max = 0;
  for (const node of Object.values(data.nodes)) {
    if (node.depth > max) max = node.depth;
  }
  return max;
}

/**
 * Get end product node IDs (keys of the paths object).
 */
export function getEndProducts(data: ScaffoldJSON): string[] {
  return Object.keys(data.paths);
}
