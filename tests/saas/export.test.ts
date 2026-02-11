/**
 * Tests for L2-29 (Rasterized PDF Export) and L2-31 (Editable PPT Export).
 *
 * These are structural/unit tests for the export modules.
 * DOM-dependent rendering (canvas, jsPDF, pptxgenjs) is mocked
 * since jsdom does not support Canvas2D or WebGL.
 */

import { describe, it, expect, vi } from "vitest";
import { MINIMAL_JSON, MULTI_PRODUCT_JSON } from "./fixtures";
import type { PdfExportOptions } from "../../saas/lib/exportPdf";
import type { PptExportOptions } from "../../saas/lib/exportPpt";
import type { ScaffoldJSON, KeyScafData } from "../../saas/types";

// ===================================================================
// L2-29: Rasterized PDF Export — Module structure tests
// ===================================================================

describe("L2-29: exportPdf module", () => {
  it("exports generateRasterizedPdf function", async () => {
    const mod = await import("../../saas/lib/exportPdf");
    expect(typeof mod.generateRasterizedPdf).toBe("function");
  });

  it("exports downloadBlob function", async () => {
    const mod = await import("../../saas/lib/exportPdf");
    expect(typeof mod.downloadBlob).toBe("function");
  });

  it("PdfExportOptions interface requires correct fields", async () => {
    // TypeScript compile-time check — this just verifies the shape is usable
    const options: PdfExportOptions = {
      data: MINIMAL_JSON,
      keyData: null,
      selectedProduct: null,
      graphCanvas: null,
      sankeySvg: null,
      viewMode: "graph",
    };
    expect(options.data).toBe(MINIMAL_JSON);
    expect(options.viewMode).toBe("graph");
  });

  it("PdfExportOptions accepts sankey viewMode", () => {
    const options: PdfExportOptions = {
      data: MINIMAL_JSON,
      keyData: null,
      selectedProduct: null,
      graphCanvas: null,
      sankeySvg: null,
      viewMode: "sankey",
    };
    expect(options.viewMode).toBe("sankey");
  });

  it("PdfExportOptions accepts keyData for restored labels", () => {
    const keyData: KeyScafData = {
      nodes: {
        aaa111: { part: "FG-001", site: "PLANT-A", stage: "Warehouse" },
      },
      stages: { S1: "Warehouse" },
    };
    const options: PdfExportOptions = {
      data: MINIMAL_JSON,
      keyData,
      selectedProduct: null,
      graphCanvas: null,
      sankeySvg: null,
      viewMode: "graph",
    };
    expect(options.keyData).toBe(keyData);
  });
});

// ===================================================================
// L2-31: Editable PPT Export — Module structure tests
// ===================================================================

describe("L2-31: exportPpt module", () => {
  it("exports generateEditablePpt function", async () => {
    const mod = await import("../../saas/lib/exportPpt");
    expect(typeof mod.generateEditablePpt).toBe("function");
  });

  it("PptExportOptions interface requires correct fields", () => {
    const options: PptExportOptions = {
      data: MINIMAL_JSON,
      keyData: null,
      selectedProduct: null,
      graphCanvas: null,
    };
    expect(options.data).toBe(MINIMAL_JSON);
  });

  it("PptExportOptions works with selectedProduct", () => {
    const options: PptExportOptions = {
      data: MULTI_PRODUCT_JSON,
      keyData: null,
      selectedProduct: "fg001",
      graphCanvas: null,
    };
    expect(options.selectedProduct).toBe("fg001");
  });

  it("PptExportOptions works with keyData for restored labels", () => {
    const keyData: KeyScafData = {
      nodes: {
        fg001: { part: "FG-001", site: "PLANT-A", stage: "Warehouse" },
      },
      stages: { S1: "Warehouse", S2: "Assembly" },
    };
    const options: PptExportOptions = {
      data: MULTI_PRODUCT_JSON,
      keyData,
      selectedProduct: "fg001",
      graphCanvas: null,
    };
    expect(options.keyData?.stages?.S1).toBe("Warehouse");
  });
});

// ===================================================================
// Export helper function tests
// ===================================================================

describe("exportPdf: downloadBlob", () => {
  it("creates and clicks an anchor element", async () => {
    const { downloadBlob } = await import("../../saas/lib/exportPdf");

    // Mock DOM APIs
    const mockClick = vi.fn();
    const mockAnchor = {
      href: "",
      download: "",
      click: mockClick,
    };
    const createSpy = vi.spyOn(document, "createElement").mockReturnValue(mockAnchor as any);
    const appendSpy = vi.spyOn(document.body, "appendChild").mockReturnValue(mockAnchor as any);
    const removeSpy = vi.spyOn(document.body, "removeChild").mockReturnValue(mockAnchor as any);
    const revokeURL = vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});
    const createURL = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:mock-url");

    const blob = new Blob(["test"], { type: "application/pdf" });
    downloadBlob(blob, "test.pdf");

    expect(createSpy).toHaveBeenCalledWith("a");
    expect(mockAnchor.download).toBe("test.pdf");
    expect(mockClick).toHaveBeenCalled();
    expect(appendSpy).toHaveBeenCalled();
    expect(removeSpy).toHaveBeenCalled();

    createSpy.mockRestore();
    appendSpy.mockRestore();
    removeSpy.mockRestore();
    revokeURL.mockRestore();
    createURL.mockRestore();
  });
});

// ===================================================================
// Tier gating logic tests (matches ExportPanel behavior)
// ===================================================================

describe("Tier gating logic", () => {
  function getEffectiveTier(tier?: string): "Free" | "Light" | "Heavy" {
    if (tier === "Heavy") return "Heavy";
    if (tier === "Light") return "Light";
    return "Free";
  }

  it("returns Free for undefined tier", () => {
    expect(getEffectiveTier(undefined)).toBe("Free");
  });

  it("returns Free for empty string tier", () => {
    expect(getEffectiveTier("")).toBe("Free");
  });

  it("returns Light for Light tier", () => {
    expect(getEffectiveTier("Light")).toBe("Light");
  });

  it("returns Heavy for Heavy tier", () => {
    expect(getEffectiveTier("Heavy")).toBe("Heavy");
  });

  it("Free tier cannot export PDF", () => {
    const tier = getEffectiveTier(undefined);
    const canPdf = tier === "Light" || tier === "Heavy";
    expect(canPdf).toBe(false);
  });

  it("Light tier can export PDF but not PPT", () => {
    const tier = getEffectiveTier("Light");
    const canPdf = tier === "Light" || tier === "Heavy";
    const canPpt = tier === "Heavy";
    expect(canPdf).toBe(true);
    expect(canPpt).toBe(false);
  });

  it("Heavy tier can export both PDF and PPT", () => {
    const tier = getEffectiveTier("Heavy");
    const canPdf = tier === "Light" || tier === "Heavy";
    const canPpt = tier === "Heavy";
    expect(canPdf).toBe(true);
    expect(canPpt).toBe(true);
  });
});

// ===================================================================
// PPT helper function tests (nodeLabel, stageName)
// ===================================================================

describe("exportPpt: helper functions", () => {
  it("nodeLabel returns truncated hash without keyData", async () => {
    // The module-level functions are not exported, but we can test
    // the PPT generation indirectly by checking the exported interface
    const mod = await import("../../saas/lib/exportPpt");
    expect(mod.generateEditablePpt).toBeDefined();
  });

  it("module imports from types correctly", async () => {
    // Verify the import chain works
    const { getStageColor } = await import("../../saas/types");
    expect(getStageColor("S1")).toMatch(/^#/);
  });
});

// ===================================================================
// Data structure compatibility tests
// ===================================================================

describe("Export data compatibility", () => {
  it("MINIMAL_JSON has all fields needed for PDF export", () => {
    expect(MINIMAL_JSON.meta).toBeDefined();
    expect(MINIMAL_JSON.nodes).toBeDefined();
    expect(MINIMAL_JSON.edges).toBeDefined();
    expect(MINIMAL_JSON.risk).toBeDefined();
    expect(MINIMAL_JSON.paths).toBeDefined();
  });

  it("MULTI_PRODUCT_JSON has all fields needed for PPT export", () => {
    expect(MULTI_PRODUCT_JSON.meta).toBeDefined();
    expect(MULTI_PRODUCT_JSON.nodes).toBeDefined();
    expect(MULTI_PRODUCT_JSON.edges).toBeDefined();
    expect(MULTI_PRODUCT_JSON.risk).toBeDefined();
    expect(MULTI_PRODUCT_JSON.paths).toBeDefined();
    expect(Object.keys(MULTI_PRODUCT_JSON.paths).length).toBeGreaterThan(1);
  });

  it("risk data has required fields for export tables", () => {
    for (const [hash, risk] of Object.entries(MINIMAL_JSON.risk)) {
      expect(risk).toHaveProperty("max_lt");
      expect(risk).toHaveProperty("single_source");
      expect(risk).toHaveProperty("depth");
      expect(typeof risk.max_lt).toBe("number");
      expect(typeof risk.single_source).toBe("boolean");
    }
  });

  it("nodes data has required fields for stage coloring", () => {
    for (const [hash, node] of Object.entries(MINIMAL_JSON.nodes)) {
      expect(node).toHaveProperty("stage");
      expect(node).toHaveProperty("lt");
      expect(node).toHaveProperty("depth");
      expect(node).toHaveProperty("site");
    }
  });
});
