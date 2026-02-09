/**
 * L2-16: D3.js Sankey Renderer.
 * L2-17: Product Path Sankey.
 * L2-18: Sankey Stage Labels.
 *
 * Render multi-hop flow visualization for a selected end product.
 */

import { useEffect, useRef, useMemo } from "react";
import * as d3 from "d3";
import { sankey, sankeyLinkHorizontal, type SankeyNode, type SankeyLink } from "d3-sankey";
import { useScaffold } from "../context/ScaffoldContext";
import { getStageColor } from "../types";

interface SNode {
  id: string;
  label: string;
  stage: string;
  depth: number;
}

interface SLink {
  source: number;
  target: number;
  value: number;
}

export function SankeyView() {
  const svgRef = useRef<SVGSVGElement>(null);
  const { data, selectedProduct, keyData } = useScaffold();

  // Build sankey data from paths of selected product
  const sankeyData = useMemo(() => {
    if (!data || !selectedProduct) return null;

    const pathData = data.paths[selectedProduct];
    if (!pathData || pathData.length === 0) return null;

    // Collect all unique nodes in paths
    const nodeSet = new Set<string>();
    // pathData is array of node hashes representing paths
    // Each path is the node array from root to leaf
    // In upload.json, paths is: { fg_hash: [ [path1_nodes], [path2_nodes], ... ] }
    // or it might be: { fg_hash: [node1, node2, ...] }

    // Determine if paths are nested arrays or flat
    const paths: string[][] = [];
    if (Array.isArray(pathData[0])) {
      // Nested: array of paths
      for (const p of pathData as unknown as string[][]) {
        paths.push(p);
        for (const n of p) nodeSet.add(n);
      }
    } else {
      // Flat: single path
      paths.push(pathData as string[]);
      for (const n of pathData) nodeSet.add(n);
    }

    // Build node array
    const nodeArr: SNode[] = [];
    const nodeIndex = new Map<string, number>();
    for (const nodeId of nodeSet) {
      const idx = nodeArr.length;
      nodeIndex.set(nodeId, idx);
      const nodeInfo = data.nodes[nodeId];
      const restored = keyData?.nodes?.[nodeId];
      nodeArr.push({
        id: nodeId,
        label: restored
          ? `${restored.part}@${restored.site}`
          : nodeId.slice(0, 8),
        stage: nodeInfo?.stage ?? "S1",
        depth: nodeInfo?.depth ?? 0,
      });
    }

    // Build links from path edges
    const linkMap = new Map<string, number>();
    for (const path of paths) {
      for (let i = 0; i < path.length - 1; i++) {
        const srcIdx = nodeIndex.get(path[i]);
        const tgtIdx = nodeIndex.get(path[i + 1]);
        if (srcIdx !== undefined && tgtIdx !== undefined) {
          const key = `${srcIdx}->${tgtIdx}`;
          linkMap.set(key, (linkMap.get(key) ?? 0) + 1);
        }
      }
    }

    const links: SLink[] = [];
    for (const [key, value] of linkMap) {
      const [src, tgt] = key.split("->").map(Number);
      links.push({ source: src, target: tgt, value });
    }

    return { nodes: nodeArr, links };
  }, [data, selectedProduct, keyData]);

  // Render D3 Sankey
  useEffect(() => {
    if (!svgRef.current || !sankeyData) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const container = svgRef.current.parentElement;
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight;
    const margin = { top: 20, right: 120, bottom: 20, left: 20 };

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    // Configure sankey layout
    const sankeyLayout = sankey<SNode, SLink>()
      .nodeId((_d, i) => i)
      .nodeWidth(20)
      .nodePadding(12)
      .nodeSort(null)
      .extent([
        [margin.left, margin.top],
        [width - margin.right, height - margin.bottom],
      ]);

    const { nodes, links } = sankeyLayout({
      nodes: sankeyData.nodes.map((d) => ({ ...d })),
      links: sankeyData.links.map((d) => ({ ...d })),
    });

    // Draw links
    svg
      .append("g")
      .selectAll("path")
      .data(links)
      .join("path")
      .attr("class", "sankey-link")
      .attr("d", sankeyLinkHorizontal())
      .attr("stroke", (d) => {
        const src = d.source as SankeyNode<SNode, SLink>;
        return getStageColor(src.stage);
      })
      .attr("stroke-width", (d) => Math.max(1, d.width ?? 1));

    // Draw nodes
    const nodeGroup = svg
      .append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .attr("class", "sankey-node");

    nodeGroup
      .append("rect")
      .attr("x", (d) => d.x0 ?? 0)
      .attr("y", (d) => d.y0 ?? 0)
      .attr("width", (d) => (d.x1 ?? 0) - (d.x0 ?? 0))
      .attr("height", (d) => Math.max(1, (d.y1 ?? 0) - (d.y0 ?? 0)))
      .attr("fill", (d) => getStageColor(d.stage));

    // L2-18: Stage labels on nodes
    nodeGroup
      .append("text")
      .attr("x", (d) => (d.x1 ?? 0) + 6)
      .attr("y", (d) => ((d.y0 ?? 0) + (d.y1 ?? 0)) / 2)
      .attr("dy", "0.35em")
      .attr("text-anchor", "start")
      .text((d) => {
        const stageName = keyData?.stages?.[d.stage] ?? d.stage;
        return `${d.label} [${stageName}]`;
      })
      .attr("font-size", "11px")
      .attr("fill", "#9ca3af");
  }, [sankeyData, keyData]);

  if (!selectedProduct) {
    return (
      <div className="no-product-selected">
        Select an end product to view its Sankey flow
      </div>
    );
  }

  if (!sankeyData) {
    return (
      <div className="no-product-selected">
        No path data available for this product
      </div>
    );
  }

  return (
    <div className="sankey-container">
      <svg ref={svgRef} />
    </div>
  );
}
