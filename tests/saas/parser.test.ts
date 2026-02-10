/**
 * Tests for L2-01: SCAFFOLD JSON Parser.
 */

import { describe, it, expect } from "vitest";
import {
  parseScaffoldJSON,
  ParseError,
  extractStages,
  extractSites,
  getMaxDepth,
  getEndProducts,
} from "../../saas/lib/parser";
import { MINIMAL_JSON, MULTI_PRODUCT_JSON } from "./fixtures";

describe("L2-01: SCAFFOLD JSON Parser", () => {
  it("parses valid JSON string", () => {
    const result = parseScaffoldJSON(JSON.stringify(MINIMAL_JSON));
    expect(result.meta.version).toBe("3.0");
  });

  it("parses valid object directly", () => {
    const result = parseScaffoldJSON(MINIMAL_JSON);
    expect(result.meta.version).toBe("3.0");
  });

  it("rejects invalid JSON string", () => {
    expect(() => parseScaffoldJSON("{bad json")).toThrow(ParseError);
  });

  it("rejects non-object top level", () => {
    expect(() => parseScaffoldJSON("[]")).toThrow(ParseError);
    expect(() => parseScaffoldJSON('"string"')).toThrow(ParseError);
  });

  it("rejects missing required keys", () => {
    expect(() => parseScaffoldJSON({ meta: {} })).toThrow(/Missing required key/);
    expect(() =>
      parseScaffoldJSON({ meta: {}, nodes: {}, edges: [] })
    ).toThrow(/Missing required key/);
  });

  it("rejects unsupported version", () => {
    const bad = { ...MINIMAL_JSON, meta: { version: "2.0", generated: "" } };
    expect(() => parseScaffoldJSON(bad)).toThrow(/Unsupported version/);
  });

  it("rejects non-string version", () => {
    const bad = { ...MINIMAL_JSON, meta: { version: 3, generated: "" } };
    expect(() => parseScaffoldJSON(bad)).toThrow(/version must be a string/);
  });

  it("rejects nodes as array", () => {
    const bad = { ...MINIMAL_JSON, nodes: [] };
    expect(() => parseScaffoldJSON(bad)).toThrow(/"nodes" must be an object/);
  });

  it("rejects edges as object", () => {
    const bad = { ...MINIMAL_JSON, edges: {} };
    expect(() => parseScaffoldJSON(bad)).toThrow(/"edges" must be an array/);
  });

  it("preserves all node data", () => {
    const result = parseScaffoldJSON(MINIMAL_JSON);
    expect(result.nodes["aaa111"].stage).toBe("S1");
    expect(result.nodes["aaa111"].lt).toBe(10);
    expect(result.nodes["aaa111"].depth).toBe(0);
  });

  it("preserves all edge data", () => {
    const result = parseScaffoldJSON(MINIMAL_JSON);
    expect(result.edges).toHaveLength(2);
    expect(result.edges[0].parent).toBe("aaa111");
    expect(result.edges[0].child).toBe("bbb222");
    expect(result.edges[0].qty).toBe(2);
  });

  it("preserves path data", () => {
    const result = parseScaffoldJSON(MINIMAL_JSON);
    expect(Object.keys(result.paths)).toHaveLength(1);
    expect(result.paths["aaa111"]).toBeDefined();
  });

  it("preserves risk data", () => {
    const result = parseScaffoldJSON(MINIMAL_JSON);
    expect(result.risk["bbb222"].single_source).toBe(true);
    expect(result.risk["bbb222"].max_lt).toBe(20);
  });
});

describe("extractStages", () => {
  it("returns unique sorted stages", () => {
    const stages = extractStages(MINIMAL_JSON);
    expect(stages).toEqual(["S1", "S2", "S3"]);
  });

  it("handles multi-product data", () => {
    const stages = extractStages(MULTI_PRODUCT_JSON);
    expect(stages).toEqual(["S1", "S2", "S3", "S4", "S5"]);
  });
});

describe("extractSites", () => {
  it("returns unique sorted sites", () => {
    const sites = extractSites(MINIMAL_JSON);
    expect(sites).toEqual(["site_hash_1", "site_hash_2"]);
  });

  it("handles 3 sites", () => {
    const sites = extractSites(MULTI_PRODUCT_JSON);
    expect(sites).toEqual(["site_a", "site_b", "site_c"]);
  });
});

describe("getMaxDepth", () => {
  it("returns maximum depth", () => {
    expect(getMaxDepth(MINIMAL_JSON)).toBe(2);
  });

  it("handles deeper graph", () => {
    expect(getMaxDepth(MULTI_PRODUCT_JSON)).toBe(3);
  });
});

describe("getEndProducts", () => {
  it("returns path keys as end products", () => {
    expect(getEndProducts(MINIMAL_JSON)).toEqual(["aaa111"]);
  });

  it("returns multiple end products", () => {
    const eps = getEndProducts(MULTI_PRODUCT_JSON);
    expect(eps).toContain("fg001");
    expect(eps).toContain("fg002");
    expect(eps).toHaveLength(2);
  });
});
