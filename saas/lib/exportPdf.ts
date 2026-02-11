/**
 * L2-29: Rasterized PDF Export.
 *
 * Generates an image-based PDF from the current visualization state.
 * Anti-OCR: All text is rasterized into images — no selectable text layer.
 * This protects masked data from automated text extraction.
 *
 * Available to Light and Heavy tier users.
 * No network calls — all generation happens client-side.
 */

import type { ScaffoldJSON, KeyScafData, ScaffoldRisk } from "../types";
import { getStageColor, STAGE_COLORS } from "../types";

/** Configuration for PDF export. */
export interface PdfExportOptions {
  /** SCAFFOLD data to export. */
  data: ScaffoldJSON;
  /** Key data for label restoration (null = masked). */
  keyData: KeyScafData | null;
  /** Currently selected end product (null = full graph). */
  selectedProduct: string | null;
  /** Canvas element from the graph view (Sigma WebGL). */
  graphCanvas: HTMLCanvasElement | null;
  /** SVG element from the sankey view. */
  sankeySvg: SVGSVGElement | null;
  /** Current view mode. */
  viewMode: "graph" | "sankey";
}

/**
 * Render an SVG element to a canvas for rasterization.
 */
function svgToCanvas(svg: SVGSVGElement): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  const bbox = svg.getBoundingClientRect();
  const scale = 2; // 2x for retina quality
  canvas.width = bbox.width * scale;
  canvas.height = bbox.height * scale;

  const ctx = canvas.getContext("2d")!;
  ctx.scale(scale, scale);

  // Serialize SVG to data URL
  const serializer = new XMLSerializer();
  const svgString = serializer.serializeToString(svg);
  const svgBlob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(svgBlob);

  return canvas; // The actual drawing is async — handled in generatePdf
}

/**
 * Draw a summary statistics table onto a canvas (rasterized, anti-OCR).
 */
function drawSummaryCanvas(
  data: ScaffoldJSON,
  keyData: KeyScafData | null,
): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = 1200;
  canvas.height = 800;
  const ctx = canvas.getContext("2d")!;

  // Background
  ctx.fillStyle = "#0f1117";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Title
  ctx.fillStyle = "#e4e6eb";
  ctx.font = "bold 28px sans-serif";
  ctx.fillText("SCAFFOLD Structure Audit Report", 40, 50);

  // Subtitle
  ctx.font = "14px sans-serif";
  ctx.fillStyle = "#9ca3af";
  ctx.fillText(
    `Generated: ${data.meta.generated} | Version: ${data.meta.version}`,
    40,
    80,
  );
  ctx.fillText(
    keyData ? "Labels: Restored" : "Labels: Masked (anonymized)",
    40,
    100,
  );

  // Stats
  const nodeCount = Object.keys(data.nodes).length;
  const edgeCount = data.edges.length;
  const endProducts = Object.keys(data.paths).length;
  const stages = new Set(Object.values(data.nodes).map((n) => n.stage));
  const sites = new Set(Object.values(data.nodes).map((n) => n.site));
  const maxDepth = Math.max(0, ...Object.values(data.nodes).map((n) => n.depth));
  const singleSource = Object.values(data.risk).filter((r) => r.single_source).length;

  const stats = [
    ["Total Nodes", String(nodeCount)],
    ["Total Edges", String(edgeCount)],
    ["End Products", String(endProducts)],
    ["Stages", String(stages.size)],
    ["Sites", String(sites.size)],
    ["Max BOM Depth", String(maxDepth)],
    ["Single Source Parts", String(singleSource)],
  ];

  // Table header
  const tableY = 140;
  ctx.fillStyle = "#252830";
  ctx.fillRect(40, tableY, 500, 32);
  ctx.fillStyle = "#e4e6eb";
  ctx.font = "bold 14px sans-serif";
  ctx.fillText("Metric", 56, tableY + 22);
  ctx.fillText("Value", 340, tableY + 22);

  // Table rows
  ctx.font = "14px sans-serif";
  for (let i = 0; i < stats.length; i++) {
    const y = tableY + 32 + i * 30;
    ctx.fillStyle = i % 2 === 0 ? "#1a1d27" : "#0f1117";
    ctx.fillRect(40, y, 500, 30);
    ctx.fillStyle = "#9ca3af";
    ctx.fillText(stats[i][0], 56, y + 20);
    ctx.fillStyle = "#e4e6eb";
    ctx.fillText(stats[i][1], 340, y + 20);
  }

  // Stage legend
  const legendY = tableY + 32 + stats.length * 30 + 30;
  ctx.fillStyle = "#e4e6eb";
  ctx.font = "bold 16px sans-serif";
  ctx.fillText("Stage Legend", 40, legendY);

  let lx = 40;
  const ly = legendY + 25;
  for (const stage of Array.from(stages).sort()) {
    const color = getStageColor(stage);
    const label = keyData?.stages?.[stage]
      ? `${stage} (${keyData.stages[stage]})`
      : stage;
    ctx.fillStyle = color;
    ctx.fillRect(lx, ly, 12, 12);
    ctx.fillStyle = "#9ca3af";
    ctx.font = "12px sans-serif";
    ctx.fillText(label, lx + 18, ly + 11);
    lx += ctx.measureText(label).width + 36;
    if (lx > canvas.width - 100) {
      lx = 40;
    }
  }

  // Risk highlights
  const riskY = ly + 40;
  ctx.fillStyle = "#e4e6eb";
  ctx.font = "bold 16px sans-serif";
  ctx.fillText("Risk Highlights", 40, riskY);

  const topRisks = Object.entries(data.risk)
    .sort((a, b) => b[1].max_lt - a[1].max_lt)
    .slice(0, 5);

  ctx.font = "13px sans-serif";
  for (let i = 0; i < topRisks.length; i++) {
    const [hash, risk] = topRisks[i];
    const label = keyData?.nodes?.[hash]
      ? `${keyData.nodes[hash].part}@${keyData.nodes[hash].site}`
      : hash.slice(0, 12) + "...";
    const y = riskY + 25 + i * 22;
    ctx.fillStyle = risk.single_source ? "#ea4335" : "#9ca3af";
    ctx.fillText(
      `${label}  LT=${risk.max_lt}  Depth=${risk.depth}${risk.single_source ? "  SINGLE SOURCE" : ""}`,
      56,
      y,
    );
  }

  return canvas;
}

/**
 * Generate a rasterized PDF from the current SCAFFOLD view.
 *
 * Returns a Blob containing the PDF data.
 * All text is rendered as images — anti-OCR by design.
 */
export async function generateRasterizedPdf(
  options: PdfExportOptions,
): Promise<Blob> {
  const { jsPDF } = await import("jspdf");

  const doc = new jsPDF({
    orientation: "landscape",
    unit: "px",
    format: [1200, 800],
  });

  // Page 1: Summary statistics (rasterized)
  const summaryCanvas = drawSummaryCanvas(options.data, options.keyData);
  const summaryImg = summaryCanvas.toDataURL("image/png");
  doc.addImage(summaryImg, "PNG", 0, 0, 1200, 800);

  // Page 2: Current visualization
  if (options.viewMode === "graph" && options.graphCanvas) {
    doc.addPage([1200, 800], "landscape");
    const graphImg = options.graphCanvas.toDataURL("image/png");
    doc.addImage(graphImg, "PNG", 0, 0, 1200, 800);
  } else if (options.viewMode === "sankey" && options.sankeySvg) {
    doc.addPage([1200, 800], "landscape");
    // Rasterize SVG: serialize → Image → Canvas → PNG
    const svgImg = await rasterizeSvg(options.sankeySvg);
    doc.addImage(svgImg, "PNG", 0, 0, 1200, 800);
  }

  return doc.output("blob");
}

/**
 * Rasterize an SVG element to a PNG data URL.
 */
async function rasterizeSvg(svg: SVGSVGElement): Promise<string> {
  return new Promise((resolve) => {
    const serializer = new XMLSerializer();
    const svgString = serializer.serializeToString(svg);
    const blob = new Blob([svgString], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);

    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = 2400; // 2x resolution
      canvas.height = 1600;
      const ctx = canvas.getContext("2d")!;
      ctx.fillStyle = "#0f1117";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
      resolve(canvas.toDataURL("image/png"));
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      // Fallback: return blank
      const canvas = document.createElement("canvas");
      canvas.width = 2400;
      canvas.height = 1600;
      resolve(canvas.toDataURL("image/png"));
    };
    img.src = url;
  });
}

/**
 * Trigger browser download of a Blob.
 */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
