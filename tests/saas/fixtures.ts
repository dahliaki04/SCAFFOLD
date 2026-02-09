/**
 * Test fixtures for SaaS tests.
 *
 * Mirrors the Python test data structure.
 */

import type { ScaffoldJSON } from "../../saas/types";

/** Minimal valid SCAFFOLD JSON for testing. */
export const MINIMAL_JSON: ScaffoldJSON = {
  meta: { version: "3.0", generated: "2026-02-09T14:30:00" },
  nodes: {
    aaa111: { stage: "S1", lt: 10, depth: 0, site: "site_hash_1" },
    bbb222: { stage: "S2", lt: 20, depth: 1, site: "site_hash_1" },
    ccc333: { stage: "S3", lt: 30, depth: 2, site: "site_hash_2" },
  },
  edges: [
    { parent: "aaa111", child: "bbb222", qty: 2 },
    { parent: "bbb222", child: "ccc333", qty: 1 },
  ],
  paths: {
    aaa111: ["aaa111", "bbb222", "ccc333"],
  },
  risk: {
    aaa111: { max_lt: 30, single_source: false, depth: 0 },
    bbb222: { max_lt: 20, single_source: true, depth: 1 },
    ccc333: { max_lt: 30, single_source: false, depth: 2 },
  },
};

/** Larger fixture with multiple end products and sites. */
export const MULTI_PRODUCT_JSON: ScaffoldJSON = {
  meta: { version: "3.0", generated: "2026-02-09T15:00:00" },
  nodes: {
    fg001: { stage: "S1", lt: 5, depth: 0, site: "site_a" },
    wip001: { stage: "S2", lt: 10, depth: 1, site: "site_a" },
    wip002: { stage: "S3", lt: 15, depth: 2, site: "site_b" },
    rm001: { stage: "S4", lt: 25, depth: 3, site: "site_b" },
    rm002: { stage: "S4", lt: 30, depth: 3, site: "site_c" },
    fg002: { stage: "S1", lt: 8, depth: 0, site: "site_c" },
    wip003: { stage: "S2", lt: 12, depth: 1, site: "site_c" },
    rm003: { stage: "S5", lt: 40, depth: 2, site: "site_a" },
  },
  edges: [
    { parent: "fg001", child: "wip001", qty: 2 },
    { parent: "wip001", child: "wip002", qty: 1 },
    { parent: "wip002", child: "rm001", qty: 3 },
    { parent: "wip002", child: "rm002", qty: 1 },
    { parent: "fg002", child: "wip003", qty: 4 },
    { parent: "wip003", child: "rm003", qty: 2 },
  ],
  paths: {
    fg001: [
      ["fg001", "wip001", "wip002", "rm001"],
      ["fg001", "wip001", "wip002", "rm002"],
    ] as unknown as string[],
    fg002: [["fg002", "wip003", "rm003"]] as unknown as string[],
  },
  risk: {
    fg001: { max_lt: 30, single_source: false, depth: 0 },
    wip001: { max_lt: 10, single_source: false, depth: 1 },
    wip002: { max_lt: 25, single_source: false, depth: 2 },
    rm001: { max_lt: 25, single_source: true, depth: 3 },
    rm002: { max_lt: 30, single_source: false, depth: 3 },
    fg002: { max_lt: 40, single_source: false, depth: 0 },
    wip003: { max_lt: 12, single_source: false, depth: 1 },
    rm003: { max_lt: 40, single_source: true, depth: 2 },
  },
};
