/**
 * L2-29: Rasterized PDF Export (Light + Heavy tier).
 * L2-31: Editable PPT Export (Heavy tier only).
 *
 * Sidebar panel with tier-gated export buttons.
 * All generation happens client-side — no network calls.
 */

import { useState, useCallback } from "react";
import { useScaffold } from "../context/ScaffoldContext";
import { generateRasterizedPdf, downloadBlob } from "../lib/exportPdf";
import { generateEditablePpt } from "../lib/exportPpt";
import type { PdfExportOptions } from "../lib/exportPdf";
import type { PptExportOptions } from "../lib/exportPpt";

/** Resolve the effective tier from upload.json meta. */
function getEffectiveTier(tier?: string): "Free" | "Light" | "Heavy" {
  if (tier === "Heavy") return "Heavy";
  if (tier === "Light") return "Light";
  return "Free";
}

/** Map internal tier keys to customer-facing pricing names. */
const TIER_DISPLAY: Record<"Free" | "Light" | "Heavy", string> = {
  Free: "Taste",
  Light: "Scope",
  Heavy: "Deliver",
};

export function ExportPanel() {
  const { data, keyData, selectedProduct, viewMode } = useScaffold();
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pptLoading, setPptLoading] = useState(false);
  const [error, setError] = useState("");

  const tier = getEffectiveTier(data?.meta?.tier);
  const canExportPdf = tier === "Light" || tier === "Heavy";
  const canExportPpt = tier === "Heavy";

  const handleExportPdf = useCallback(async () => {
    if (!data) return;
    setPdfLoading(true);
    setError("");

    try {
      // Try to capture the current graph canvas
      const graphCanvas = document.querySelector<HTMLCanvasElement>(
        ".graph-container canvas",
      );
      // Try to capture the current sankey SVG
      const sankeySvg = document.querySelector<SVGSVGElement>(
        ".sankey-container svg",
      );

      const options: PdfExportOptions = {
        data,
        keyData,
        selectedProduct,
        graphCanvas,
        sankeySvg,
        viewMode,
      };

      const blob = await generateRasterizedPdf(options);
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
      downloadBlob(blob, `SCAFFOLD_Report_${timestamp}.pdf`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "PDF export failed");
    } finally {
      setPdfLoading(false);
    }
  }, [data, keyData, selectedProduct, viewMode]);

  const handleExportPpt = useCallback(async () => {
    if (!data) return;
    setPptLoading(true);
    setError("");

    try {
      const graphCanvas = document.querySelector<HTMLCanvasElement>(
        ".graph-container canvas",
      );

      const options: PptExportOptions = {
        data,
        keyData,
        selectedProduct,
        graphCanvas,
      };

      const blob = await generateEditablePpt(options);
      const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, 19);
      downloadBlob(blob, `SCAFFOLD_Report_${timestamp}.pptx`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "PPT export failed");
    } finally {
      setPptLoading(false);
    }
  }, [data, keyData, selectedProduct]);

  if (!data) return null;

  return (
    <div className="sidebar-section">
      <h3>Export</h3>

      <div className="export-tier-badge">
        Tier: <span className={`tier-${tier.toLowerCase()}`}>{TIER_DISPLAY[tier]}</span>
      </div>

      {/* L2-29: Rasterized PDF */}
      <button
        className="btn export-btn"
        onClick={handleExportPdf}
        disabled={!canExportPdf || pdfLoading}
        title={
          canExportPdf
            ? "Export rasterized PDF (anti-OCR)"
            : "Requires Scope or Deliver tier"
        }
      >
        {pdfLoading ? "Generating PDF..." : "Export PDF"}
        {!canExportPdf && <span className="tier-lock">Scope+</span>}
      </button>

      {/* L2-31: Editable PPT */}
      <button
        className="btn export-btn"
        onClick={handleExportPpt}
        disabled={!canExportPpt || pptLoading}
        title={
          canExportPpt
            ? "Export editable PowerPoint"
            : "Requires Deliver tier"
        }
      >
        {pptLoading ? "Generating PPT..." : "Export PPT"}
        {!canExportPpt && <span className="tier-lock">Deliver</span>}
      </button>

      {error && <div className="export-error">{error}</div>}
    </div>
  );
}
