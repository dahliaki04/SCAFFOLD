/**
 * Tests for L2-02: Sigma.js Adapter (toSigma).
 * Also covers L2-05, L2-06, L2-07, L2-14 filtering.
 */

import { describe, it, expect } from "vitest";
import { toSigmaGraph, countVisibleNodes, DEFAULT_VISIBLE_DEPTH } from "../../saas/adapters/toSigma";
import { MINIMAL_JSON, MULTI_PRODUCT_JSON } from "./fixtures";
import { getStageColor, STAGE_COLORS, DEFAULT_STAGE_COLOR } from "../../saas/types";

describe("L2-02: toSigmaGraph", () => {
  it("creates graph with correct node count", () => {
    const graph = toSigmaGraph(MINIMAL_JSON);
    expect(graph.order).toBe(3);
  });

  it("creates graph with correct edge count", () => {
    const graph = toSigmaGraph(MINIMAL_JSON);
    expect(graph.size).toBe(2);
  });

  it("directed graph type", () => {
    const graph = toSigmaGraph(MINIMAL_JSON);
    expect(graph.type).toBe("directed");
  });

  it("nodes have position attributes", () => {
    const graph = toSigmaGraph(MINIMAL_JSON);
    graph.forEachNode((_id, attrs) => {
      expect(typeof attrs.x).toBe("number");
      expect(typeof attrs.y).toBe("number");
    });
  });

  it("nodes have label attribute", () => {
    const graph = toSigmaGraph(MINIMAL_JSON);
    graph.forEachNode((_id, attrs) => {
      expect(typeof attrs.label).toBe("string");
      expect(attrs.label.length).toBeGreaterThan(0);
    });
  });
});

describe("L2-05: Node Color by Stage", () => {
  it("each stage has a unique color", () => {
    const colors = new Set(Object.values(STAGE_COLORS));
    expect(colors.size).toBe(Object.keys(STAGE_COLORS).length);
  });

  it("S1 is blue", () => {
    expect(getStageColor("S1")).toBe("#4285F4");
  });

  it("S2 is green", () => {
    expect(getStageColor("S2")).toBe("#34A853");
  });

  it("S3 is orange", () => {
    expect(getStageColor("S3")).toBe("#F59E0B");
  });

  it("unknown stage gets default color", () => {
    expect(getStageColor("S99")).toBe(DEFAULT_STAGE_COLOR);
  });

  it("graph nodes have color from stage", () => {
    const graph = toSigmaGraph(MINIMAL_JSON);
    const s1Color = getStageColor("S1");
    expect(graph.getNodeAttribute("aaa111", "color")).toBe(s1Color);
  });
});

describe("L2-06: Node Size by Risk", () => {
  it("highest-risk node is largest", () => {
    const graph = toSigmaGraph(MINIMAL_JSON);
    const sizeA = graph.getNodeAttribute("aaa111", "size") as number;
    const sizeC = graph.getNodeAttribute("ccc333", "size") as number;
    // ccc333 has max_lt=30 (highest risk)
    expect(sizeC).toBeGreaterThanOrEqual(sizeA);
  });

  it("all nodes have positive size", () => {
    const graph = toSigmaGraph(MULTI_PRODUCT_JSON);
    graph.forEachNode((_id, attrs) => {
      expect(attrs.size).toBeGreaterThan(0);
    });
  });
});

describe("L2-06: Node Size Toggle", () => {
  it("uniform size when nodeSizing disabled", () => {
    const graph = toSigmaGraph(MINIMAL_JSON, { nodeSizing: false });
    const sizes = new Set<number>();
    graph.forEachNode((_id, attrs) => {
      sizes.add(attrs.size);
    });
    expect(sizes.size).toBe(1); // all nodes same size
  });

  it("varied sizes when nodeSizing enabled", () => {
    const graph = toSigmaGraph(MINIMAL_JSON, { nodeSizing: true });
    const sizeA = graph.getNodeAttribute("aaa111", "size") as number;
    const sizeB = graph.getNodeAttribute("bbb222", "size") as number;
    // bbb222 has lower max_lt (20) than aaa111 (30), so smaller
    expect(sizeA).not.toBe(sizeB);
  });

  it("defaults to risk-based sizing", () => {
    const graph = toSigmaGraph(MINIMAL_JSON);
    const sizes = new Set<number>();
    graph.forEachNode((_id, attrs) => {
      sizes.add(attrs.size);
    });
    expect(sizes.size).toBeGreaterThan(1);
  });
});

describe("L2-07: Lazy Loading", () => {
  it("DEFAULT_VISIBLE_DEPTH is 3", () => {
    expect(DEFAULT_VISIBLE_DEPTH).toBe(3);
  });

  it("countVisibleNodes respects maxVisibleDepth", () => {
    const total = countVisibleNodes(MULTI_PRODUCT_JSON);
    expect(total).toBe(8);

    const depth1 = countVisibleNodes(MULTI_PRODUCT_JSON, {
      maxVisibleDepth: 1,
    });
    expect(depth1).toBeLessThan(total);
    expect(depth1).toBeGreaterThan(0);
  });
});

describe("L2-11: Stage Filter", () => {
  it("filters nodes by stage", () => {
    const all = countVisibleNodes(MULTI_PRODUCT_JSON);
    const s1Only = countVisibleNodes(MULTI_PRODUCT_JSON, {
      stageFilter: new Set(["S1"]),
    });
    expect(s1Only).toBeLessThan(all);
    expect(s1Only).toBe(2); // fg001 + fg002
  });

  it("empty stage filter shows nothing", () => {
    const count = countVisibleNodes(MULTI_PRODUCT_JSON, {
      stageFilter: new Set(),
    });
    expect(count).toBe(0);
  });
});

describe("L2-12: Site Filter", () => {
  it("filters nodes by site", () => {
    const siteA = countVisibleNodes(MULTI_PRODUCT_JSON, {
      siteFilter: new Set(["site_a"]),
    });
    expect(siteA).toBe(3); // fg001, wip001, rm003
  });
});

describe("L2-13: Depth Filter", () => {
  it("filters by max depth", () => {
    const depth2 = countVisibleNodes(MULTI_PRODUCT_JSON, {
      depthFilter: 2,
    });
    const depth3 = countVisibleNodes(MULTI_PRODUCT_JSON, {
      depthFilter: 3,
    });
    expect(depth2).toBeLessThan(depth3);
  });
});

describe("L2-14: Subgraph View", () => {
  it("subgraph contains only reachable nodes", () => {
    const graph = toSigmaGraph(MULTI_PRODUCT_JSON, {
      subgraphRoot: "fg002",
    });
    // fg002 -> wip003 -> rm003 = 3 nodes
    expect(graph.order).toBe(3);
    expect(graph.hasNode("fg002")).toBe(true);
    expect(graph.hasNode("wip003")).toBe(true);
    expect(graph.hasNode("rm003")).toBe(true);
    expect(graph.hasNode("fg001")).toBe(false);
  });

  it("subgraph preserves edges", () => {
    const graph = toSigmaGraph(MULTI_PRODUCT_JSON, {
      subgraphRoot: "fg002",
    });
    expect(graph.size).toBe(2);
  });
});

describe("L2-26: Live Label Restore", () => {
  it("restored labels use real names", () => {
    const keyData = {
      nodes: {
        aaa111: { part: "FG-001", site: "DC-EAST", stage: "WAF" },
        bbb222: { part: "WIP-01", site: "DC-EAST", stage: "ASSY" },
        ccc333: { part: "RM-01", site: "PLANT-A", stage: "RAW" },
      },
      stages: { S1: "WAF", S2: "ASSY", S3: "RAW" },
    };

    const graph = toSigmaGraph(MINIMAL_JSON, { keyData });
    expect(graph.getNodeAttribute("aaa111", "label")).toBe("FG-001@DC-EAST");
    expect(graph.getNodeAttribute("bbb222", "label")).toBe("WIP-01@DC-EAST");
  });

  it("without key data shows hash prefix", () => {
    const graph = toSigmaGraph(MINIMAL_JSON);
    const label = graph.getNodeAttribute("aaa111", "label") as string;
    expect(label).toContain("...");
  });
});
