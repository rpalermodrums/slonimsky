import type { PitchClass, SlonimskyPattern } from "./types";

export interface GraphNode {
  id: PitchClass;
  name: string;
  patterns: Set<string>;
}

export interface GraphEdge {
  source: PitchClass;
  target: PitchClass;
  interval: number;
  patterns: Set<string>;
  weight: number;
}

export interface MelodicGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

const PITCH_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"] as const;

export function buildMelodicGraph(patterns: SlonimskyPattern[]): MelodicGraph {
  const nodeMap = new Map<PitchClass, GraphNode>();
  const edgeMap = new Map<string, GraphEdge>();

  for (let pc = 0; pc < 12; pc++) {
    nodeMap.set(pc as PitchClass, {
      id: pc as PitchClass,
      name: PITCH_NAMES[pc],
      patterns: new Set(),
    });
  }

  for (const pattern of patterns) {
    const pitchClasses = pattern.pitchClasses;

    for (const pc of pitchClasses) {
      nodeMap.get(pc)?.patterns.add(pattern.id);
    }

    for (let i = 0; i < pitchClasses.length - 1; i++) {
      const source = pitchClasses[i];
      const target = pitchClasses[i + 1];
      const interval = pattern.intervals[i];
      const edgeKey = `${source}->${target}`;

      const existing = edgeMap.get(edgeKey);
      if (existing) {
        existing.patterns.add(pattern.id);
        existing.weight++;
      } else {
        edgeMap.set(edgeKey, {
          source,
          target,
          interval,
          patterns: new Set([pattern.id]),
          weight: 1,
        });
      }
    }
  }

  return {
    nodes: Array.from(nodeMap.values()),
    edges: Array.from(edgeMap.values()),
  };
}

export function getEdgesByNode(graph: MelodicGraph, pitchClass: PitchClass): GraphEdge[] {
  return graph.edges.filter(
    (e) => e.source === pitchClass || e.target === pitchClass
  );
}

export function getPatternsByEdge(
  graph: MelodicGraph,
  source: PitchClass,
  target: PitchClass
): string[] {
  const edge = graph.edges.find(
    (e) => e.source === source && e.target === target
  );
  return edge ? Array.from(edge.patterns) : [];
}
