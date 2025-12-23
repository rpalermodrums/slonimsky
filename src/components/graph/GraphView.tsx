import { useEffect, useRef, useMemo, useState } from "react";
import * as d3 from "d3";
import { buildMelodicGraph } from "@/core";
import { usePatternStore } from "@/stores/patternStore";
import { usePlaybackStore } from "@/stores/playbackStore";
import type { PitchClass } from "@/core/types";

interface D3Node extends d3.SimulationNodeDatum {
  id: number;
  name: string;
  patternCount: number;
}

interface D3Link extends d3.SimulationLinkDatum<D3Node> {
  source: D3Node | number;
  target: D3Node | number;
  weight: number;
  interval: number;
}

interface GraphViewProps {
  width?: number;
  height?: number;
  onNodeClick?: (pitchClass: PitchClass) => void;
  onNodeHover?: (pitchClass: PitchClass | null) => void;
  onEdgeClick?: (source: number, target: number, patterns: string[]) => void;
}

export function GraphView({
  width = 600,
  height = 500,
  onNodeClick,
  onNodeHover,
  onEdgeClick,
}: GraphViewProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const { catalog, selectedPattern } = usePatternStore();
  const [selectedNode, setSelectedNode] = useState<number | null>(null);
  const { currentNoteIndex } = usePlaybackStore();

  const highlightedPath = useMemo(() => {
    return selectedPattern?.pitchClasses ?? [];
  }, [selectedPattern]);

  const highlightedEdges = useMemo(() => {
    if (highlightedPath.length < 2) return [];
    const result: { source: number; target: number }[] = [];
    for (let i = 0; i < highlightedPath.length - 1; i++) {
      const from = highlightedPath[i];
      const to = highlightedPath[i + 1];
      result.push({ source: from, target: to });
    }
    return result;
  }, [highlightedPath]);

  const highlightedPathSet = useMemo(
    () => new Set(highlightedPath),
    [highlightedPath]
  );

  const currentlyHighlightedNode = useMemo(() => {
    return highlightedPath[(currentNoteIndex ?? 0) % highlightedPath.length] ?? null;
  }, [highlightedPath, currentNoteIndex]);

  const graph = useMemo(() => buildMelodicGraph(catalog), [catalog]);

  const { nodes, links } = useMemo(() => {
    const nodes: D3Node[] = graph.nodes.map((n) => ({
      id: n.id,
      name: n.name,
      patternCount: n.patterns.size,
    }));

    const links: D3Link[] = graph.edges.map((e) => ({
      source: e.source,
      target: e.target,
      weight: e.weight,
      interval: e.interval,
    }));

    return { nodes, links };
  }, [graph]);

  useEffect(() => {
    if (!svgRef.current || nodes.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const g = svg.append("g");

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 3])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });

    svg.call(zoom);

    const simulation = d3.forceSimulation<D3Node>(nodes)
      .force("link", d3.forceLink<D3Node, D3Link>(links)
        .id((d) => d.id)
        .distance(80))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius(30));

const maxWeight = Math.max(...links.map((l) => l.weight), 1);

    const link = g.append("g")
      .selectAll("line")
      .data(links)
      .join("line")
      .attr("stroke", (d) => {
        const sourceId = typeof d.source === "object" ? d.source.id : d.source;
        const targetId = typeof d.target === "object" ? d.target.id : d.target;
        const isHighlighted = highlightedEdges.some(
          (he) => he.source === sourceId && he.target === targetId
        );
        return isHighlighted ? "#22c55e" : "#525252";
      })
      .attr("stroke-opacity", (d) => {
        const sourceId = typeof d.source === "object" ? d.source.id : d.source;
        const targetId = typeof d.target === "object" ? d.target.id : d.target;
        const isHighlighted = highlightedEdges.some(
          (he) => he.source === sourceId && he.target === targetId
        );
        return isHighlighted ? 0.9 : 0.3;
      })
      .attr("stroke-width", (d) => {
        const sourceId = typeof d.source === "object" ? d.source.id : d.source;
        const targetId = typeof d.target === "object" ? d.target.id : d.target;
        const isHighlighted = highlightedEdges.some(
          (he) => he.source === sourceId && he.target === targetId
        );
        return isHighlighted ? 3 : Math.max(1, (d.weight / maxWeight) * 3);
      })
      .style("cursor", "pointer")
      .on("click", (event, d) => {
        event.stopPropagation();
        const sourceId = typeof d.source === "object" ? d.source.id : d.source;
        const targetId = typeof d.target === "object" ? d.target.id : d.target;
        const edge = graph.edges.find(
          (e) => e.source === sourceId && e.target === targetId
        );
        if (edge && onEdgeClick) {
          onEdgeClick(sourceId, targetId, Array.from(edge.patterns));
        }
      });

    const node = g.append("g")
      .selectAll("g")
      .data(nodes)
      .join("g")
      .style("cursor", "pointer")
      .call(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        d3.drag<any, any>()
          .on("start", (event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>, d: D3Node) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>, d: D3Node) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event: d3.D3DragEvent<SVGGElement, D3Node, D3Node>, d: D3Node) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    node.append("circle")
      .attr("r", (d) => {
        const baseRadius = 15 + Math.min(d.patternCount / 10, 10);
        const isHighlighted = highlightedPathSet.has(d.id as PitchClass);
        const isCurrent = d.id === currentlyHighlightedNode;
        if (isCurrent) return baseRadius + 8;
        if (isHighlighted) return baseRadius + 4;
        return baseRadius;
      })
      .attr("fill", (d) => {
        const hue = (d.id / 12) * 360;
        const isHighlighted = highlightedPathSet.has(d.id as PitchClass);
        const isCurrent = d.id === currentlyHighlightedNode;
        if (isCurrent) return "#22c55e";
        if (isHighlighted) return `hsl(${hue}, 70%, 60%)`;
        return `hsl(${hue}, 70%, 50%)`;
      })
      .attr("stroke", (d) => {
        const isCurrent = d.id === currentlyHighlightedNode;
        return isCurrent ? "#fff" : "#fff";
      })
      .attr("stroke-width", (d) => {
        const isHighlighted = highlightedPathSet.has(d.id as PitchClass);
        const isCurrent = d.id === currentlyHighlightedNode;
        if (isCurrent) return 4;
        if (isHighlighted) return 3;
        return 2;
      });

    node.append("text")
      .text((d) => d.name)
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("fill", "#fff")
      .attr("font-size", "12px")
      .attr("font-weight", "bold")
      .attr("pointer-events", "none");

    node.on("click", (_, d) => {
      setSelectedNode(d.id);
      onNodeClick?.(d.id as PitchClass);
    })
      .on("mouseenter", (_, d) => {
        onNodeHover?.(d.id as PitchClass);
      })
      .on("mouseleave", () => {
        onNodeHover?.(null);
      });

    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as D3Node).x!)
        .attr("y1", (d) => (d.source as D3Node).y!)
        .attr("x2", (d) => (d.target as D3Node).x!)
        .attr("y2", (d) => (d.target as D3Node).y!);

      node.attr("transform", (d) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [nodes, links, width, height, graph, onNodeClick, onEdgeClick, onNodeHover]);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);

    svg.selectAll<SVGCircleElement, D3Node>("circle")
      .attr("r", (d) => {
        const baseRadius = 15 + Math.min(d.patternCount / 10, 10);
        const isHighlighted = highlightedPathSet.has(d.id as PitchClass);
        const isCurrent = d.id === currentlyHighlightedNode;
        if (isCurrent) return baseRadius + 8;
        if (isHighlighted) return baseRadius + 4;
        return baseRadius;
      })
      .attr("fill", (d) => {
        const hue = (d.id / 12) * 360;
        const isHighlighted = highlightedPathSet.has(d.id as PitchClass);
        const isCurrent = d.id === currentlyHighlightedNode;
        if (isCurrent) return "#22c55e";
        if (isHighlighted) return `hsl(${hue}, 70%, 60%)`;
        return `hsl(${hue}, 70%, 50%)`;
      })
      .attr("stroke-width", (d) => {
        const isHighlighted = highlightedPathSet.has(d.id as PitchClass);
        const isCurrent = d.id === currentlyHighlightedNode;
        if (isCurrent) return 4;
        if (isHighlighted) return 3;
        return 2;
      });

    svg.selectAll<SVGLineElement, D3Link>("line")
      .attr("stroke", (d) => {
        const sourceId = typeof d.source === "object" ? d.source.id : d.source;
        const targetId = typeof d.target === "object" ? d.target.id : d.target;
        const isHighlighted = highlightedEdges.some(
          (he) => he.source === sourceId && he.target === targetId
        );
        return isHighlighted ? "#22c55e" : "#525252";
      })
      .attr("stroke-opacity", (d) => {
        const sourceId = typeof d.source === "object" ? d.source.id : d.source;
        const targetId = typeof d.target === "object" ? d.target.id : d.target;
        const isHighlighted = highlightedEdges.some(
          (he) => he.source === sourceId && he.target === targetId
        );
        return isHighlighted ? 0.9 : 0.3;
      });
  }, [highlightedPathSet, highlightedEdges, currentlyHighlightedNode]);

  return (
    <div className="relative bg-zinc-900 rounded-lg border border-zinc-800 overflow-hidden">
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="w-full h-full"
      />
      {selectedNode !== null && (
        <div className="absolute top-2 left-2 bg-zinc-800/90 backdrop-blur px-3 py-2 rounded-lg text-sm">
          <span className="text-zinc-400">Selected:</span>{" "}
          <span className="text-white font-medium">
            {graph.nodes.find((n) => n.id === selectedNode)?.name}
          </span>
          <span className="text-zinc-500 ml-2">
            ({graph.nodes.find((n) => n.id === selectedNode)?.patterns.size} patterns)
          </span>
        </div>
      )}
    </div>
  );
}
