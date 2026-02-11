/**
 * L2-31: Editable PPT Export.
 *
 * Generates an Office Open XML (.pptx) slide deck with editable text,
 * tables, and charts. Unlike L2-29 (rasterized PDF), all content is
 * editable in PowerPoint — consultants can modify text, colors, etc.
 *
 * Available to Heavy tier users only.
 * No network calls — all generation happens client-side.
 */

import type { ScaffoldJSON, KeyScafData } from "../types";
import { getStageColor } from "../types";

/** Configuration for PPT export. */
export interface PptExportOptions {
  /** SCAFFOLD data to export. */
  data: ScaffoldJSON;
  /** Key data for label restoration (null = masked). */
  keyData: KeyScafData | null;
  /** Currently selected end product (null = overview). */
  selectedProduct: string | null;
  /** Canvas element from the graph view (for visualization screenshot). */
  graphCanvas: HTMLCanvasElement | null;
}

/** Resolve a node's display label. */
function nodeLabel(
  hash: string,
  keyData: KeyScafData | null,
): string {
  if (keyData?.nodes?.[hash]) {
    const n = keyData.nodes[hash];
    return `${n.part}@${n.site}`;
  }
  return hash.slice(0, 10) + "...";
}

/** Resolve a stage's display name. */
function stageName(stage: string, keyData: KeyScafData | null): string {
  if (keyData?.stages?.[stage]) {
    return `${stage} (${keyData.stages[stage]})`;
  }
  return stage;
}

/**
 * Generate an editable PowerPoint slide deck from SCAFFOLD data.
 *
 * Slide structure:
 *   1. Title slide (project overview)
 *   2. Network statistics table
 *   3. Graph visualization (as image — editable frame)
 *   4. Risk summary table (top risks, single source)
 *   5. Stage distribution breakdown
 *   6. End product summary (with selected product detail if applicable)
 *
 * Returns a Blob containing the .pptx file.
 */
export async function generateEditablePpt(
  options: PptExportOptions,
): Promise<Blob> {
  const PptxGenJS = (await import("pptxgenjs")).default;

  const pptx = new PptxGenJS();
  pptx.author = "SCAFFOLD v3.0";
  pptx.title = "SCAFFOLD Structure Audit Report";
  pptx.subject = "Supply Chain BOM Analysis";

  const { data, keyData, selectedProduct, graphCanvas } = options;

  // Shared style constants
  const BG = "0F1117";
  const TEXT = "E4E6EB";
  const MUTED = "9CA3AF";
  const ACCENT = "4285F4";
  const DARK_BG = "1A1D27";

  // ── Slide 1: Title ─────────────────────────────────────
  const slide1 = pptx.addSlide();
  slide1.background = { color: BG };
  slide1.addText("SCAFFOLD", {
    x: 0.8,
    y: 1.5,
    w: 8,
    fontSize: 44,
    bold: true,
    color: ACCENT,
    fontFace: "Helvetica",
  });
  slide1.addText("Supply Chain Structure Audit Report", {
    x: 0.8,
    y: 2.3,
    w: 8,
    fontSize: 20,
    color: TEXT,
    fontFace: "Helvetica",
  });
  slide1.addText(
    [
      { text: `Generated: ${data.meta.generated}`, options: { fontSize: 12, color: MUTED } },
      { text: "\n" },
      { text: `Version: ${data.meta.version}`, options: { fontSize: 12, color: MUTED } },
      { text: "\n" },
      {
        text: keyData ? "Labels: Restored (real names)" : "Labels: Masked (anonymized)",
        options: { fontSize: 12, color: keyData ? "34A853" : "F59E0B" },
      },
    ],
    { x: 0.8, y: 3.2, w: 8, fontFace: "Helvetica" },
  );

  // ── Slide 2: Network Statistics ────────────────────────
  const slide2 = pptx.addSlide();
  slide2.background = { color: BG };
  slide2.addText("Network Statistics", {
    x: 0.5,
    y: 0.3,
    w: 9,
    fontSize: 24,
    bold: true,
    color: TEXT,
    fontFace: "Helvetica",
  });

  const nodeCount = Object.keys(data.nodes).length;
  const edgeCount = data.edges.length;
  const endProducts = Object.keys(data.paths).length;
  const stages = [...new Set(Object.values(data.nodes).map((n) => n.stage))].sort();
  const sites = [...new Set(Object.values(data.nodes).map((n) => n.site))].sort();
  const maxDepth = Math.max(0, ...Object.values(data.nodes).map((n) => n.depth));
  const singleSourceCount = Object.values(data.risk).filter((r) => r.single_source).length;

  const statsRows: Array<Array<{ text: string; options: Record<string, unknown> }>> = [
    [
      { text: "Metric", options: { bold: true, color: TEXT, fill: { color: "252830" } } },
      { text: "Value", options: { bold: true, color: TEXT, fill: { color: "252830" } } },
    ],
    [
      { text: "Total Nodes", options: { color: MUTED } },
      { text: String(nodeCount), options: { color: TEXT } },
    ],
    [
      { text: "Total Edges", options: { color: MUTED } },
      { text: String(edgeCount), options: { color: TEXT } },
    ],
    [
      { text: "End Products", options: { color: MUTED } },
      { text: String(endProducts), options: { color: TEXT } },
    ],
    [
      { text: "Stages", options: { color: MUTED } },
      { text: String(stages.length), options: { color: TEXT } },
    ],
    [
      { text: "Sites", options: { color: MUTED } },
      { text: String(sites.length), options: { color: TEXT } },
    ],
    [
      { text: "Max BOM Depth", options: { color: MUTED } },
      { text: String(maxDepth), options: { color: TEXT } },
    ],
    [
      { text: "Single Source Parts", options: { color: MUTED } },
      { text: String(singleSourceCount), options: { color: singleSourceCount > 0 ? "EA4335" : TEXT } },
    ],
  ];

  slide2.addTable(statsRows, {
    x: 0.5,
    y: 1.0,
    w: 6,
    fontSize: 13,
    fontFace: "Helvetica",
    border: { type: "solid", color: "333640", pt: 0.5 },
    colW: [3, 3],
  });

  // Stage legend
  const stageTexts = stages.map((s) => ({
    text: `  ${stageName(s, keyData)}  `,
    options: { fontSize: 11, color: getStageColor(s).replace("#", "") },
  }));
  slide2.addText(stageTexts, {
    x: 0.5,
    y: 4.2,
    w: 9,
    fontFace: "Helvetica",
  });

  // ── Slide 3: Visualization ─────────────────────────────
  const slide3 = pptx.addSlide();
  slide3.background = { color: BG };
  slide3.addText("BOM Graph Visualization", {
    x: 0.5,
    y: 0.3,
    w: 9,
    fontSize: 24,
    bold: true,
    color: TEXT,
    fontFace: "Helvetica",
  });

  if (graphCanvas) {
    const imgData = graphCanvas.toDataURL("image/png");
    slide3.addImage({
      data: imgData,
      x: 0.5,
      y: 1.0,
      w: 9,
      h: 5.5,
    });
  } else {
    slide3.addText("Graph visualization not captured.\nSwitch to Graph view and export again.", {
      x: 1,
      y: 2.5,
      w: 8,
      fontSize: 16,
      color: MUTED,
      fontFace: "Helvetica",
      align: "center",
    });
  }

  // ── Slide 4: Risk Summary ──────────────────────────────
  const slide4 = pptx.addSlide();
  slide4.background = { color: BG };
  slide4.addText("Risk Analysis", {
    x: 0.5,
    y: 0.3,
    w: 9,
    fontSize: 24,
    bold: true,
    color: TEXT,
    fontFace: "Helvetica",
  });

  // Top 10 risks by max lead time
  const topRisks = Object.entries(data.risk)
    .sort((a, b) => b[1].max_lt - a[1].max_lt)
    .slice(0, 10);

  const riskRows: Array<Array<{ text: string; options: Record<string, unknown> }>> = [
    [
      { text: "Node", options: { bold: true, color: TEXT, fill: { color: "252830" } } },
      { text: "Max Lead Time", options: { bold: true, color: TEXT, fill: { color: "252830" } } },
      { text: "Depth", options: { bold: true, color: TEXT, fill: { color: "252830" } } },
      { text: "Single Source", options: { bold: true, color: TEXT, fill: { color: "252830" } } },
    ],
  ];

  for (const [hash, risk] of topRisks) {
    riskRows.push([
      { text: nodeLabel(hash, keyData), options: { color: MUTED, fontSize: 11 } },
      { text: String(risk.max_lt), options: { color: TEXT } },
      { text: String(risk.depth), options: { color: TEXT } },
      {
        text: risk.single_source ? "YES" : "No",
        options: { color: risk.single_source ? "EA4335" : "34A853" },
      },
    ]);
  }

  slide4.addTable(riskRows, {
    x: 0.5,
    y: 1.0,
    w: 9,
    fontSize: 12,
    fontFace: "Helvetica",
    border: { type: "solid", color: "333640", pt: 0.5 },
    colW: [3.5, 2, 1.5, 2],
  });

  // ── Slide 5: End Product Summary ───────────────────────
  const slide5 = pptx.addSlide();
  slide5.background = { color: BG };
  slide5.addText("End Products", {
    x: 0.5,
    y: 0.3,
    w: 9,
    fontSize: 24,
    bold: true,
    color: TEXT,
    fontFace: "Helvetica",
  });

  const epRows: Array<Array<{ text: string; options: Record<string, unknown> }>> = [
    [
      { text: "Product", options: { bold: true, color: TEXT, fill: { color: "252830" } } },
      { text: "Stage", options: { bold: true, color: TEXT, fill: { color: "252830" } } },
      { text: "Max LT", options: { bold: true, color: TEXT, fill: { color: "252830" } } },
      { text: "Paths", options: { bold: true, color: TEXT, fill: { color: "252830" } } },
    ],
  ];

  for (const epHash of Object.keys(data.paths)) {
    const node = data.nodes[epHash];
    const risk = data.risk[epHash];
    const pathData = data.paths[epHash];
    const pathCount = Array.isArray(pathData?.[0]) ? pathData.length : 1;

    epRows.push([
      { text: nodeLabel(epHash, keyData), options: { color: ACCENT, fontSize: 11 } },
      { text: stageName(node?.stage ?? "S1", keyData), options: { color: MUTED } },
      { text: String(risk?.max_lt ?? 0), options: { color: TEXT } },
      { text: String(pathCount), options: { color: TEXT } },
    ]);
  }

  slide5.addTable(epRows, {
    x: 0.5,
    y: 1.0,
    w: 9,
    fontSize: 12,
    fontFace: "Helvetica",
    border: { type: "solid", color: "333640", pt: 0.5 },
    colW: [3.5, 2, 1.5, 2],
  });

  // Selected product detail
  if (selectedProduct) {
    slide5.addText(
      `Selected: ${nodeLabel(selectedProduct, keyData)}`,
      {
        x: 0.5,
        y: 4.5,
        w: 9,
        fontSize: 14,
        color: ACCENT,
        fontFace: "Helvetica",
      },
    );
  }

  // ── Slide 6: Footer ────────────────────────────────────
  const slide6 = pptx.addSlide();
  slide6.background = { color: BG };
  slide6.addText("SCAFFOLD v3.0", {
    x: 0.8,
    y: 2.0,
    w: 8,
    fontSize: 36,
    bold: true,
    color: ACCENT,
    fontFace: "Helvetica",
    align: "center",
  });
  slide6.addText("Supply Chain Structure Audit", {
    x: 0.8,
    y: 3.0,
    w: 8,
    fontSize: 18,
    color: MUTED,
    fontFace: "Helvetica",
    align: "center",
  });
  slide6.addText(
    "This report was generated offline. No data was transmitted.",
    {
      x: 0.8,
      y: 4.5,
      w: 8,
      fontSize: 11,
      color: "6B7280",
      fontFace: "Helvetica",
      align: "center",
    },
  );

  // Generate .pptx blob
  const arrayBuffer = await pptx.write({ outputType: "arraybuffer" }) as ArrayBuffer;
  return new Blob([arrayBuffer], {
    type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  });
}
