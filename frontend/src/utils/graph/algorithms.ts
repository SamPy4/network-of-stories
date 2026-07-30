import DirectedGraph from "graphology";
import { hasCycle } from 'graphology-dag'
import { connectedComponents } from "graphology-components";

export function findOutComponent(graph: DirectedGraph, nodeId: string) {
  if (!graph.hasNode(nodeId)) return {};
  console.log("The graph has a cycle: " + hasCycle(graph))

  const visitedNodes = new Set<string>();
  const visitedEdges = new Set<string>();
  const stack: string[] = [nodeId];

  while (stack.length > 0) {
    const current = stack.pop() as string;

    if (!visitedNodes.has(current)) {
      visitedNodes.add(current);
      graph.mapOutEdges(current, (e) => {
        visitedEdges.add(e);
      });

      // Traverse outgoing neighbors
      graph.forEachOutboundNeighbor(current, (neighbor) => {
        if (!visitedNodes.has(neighbor)) {
          stack.push(neighbor);
        }
      });
    }
  }
  // If you don't want to include the start node itself, remove it:
  // visitedNodes.delete(nodeId);

  return { nodes: visitedNodes, edges: visitedEdges };
}

export function findOldestNeighbor(graph: DirectedGraph, nodeId: string) {
  const olderNeigh = graph.inNeighbors(nodeId);
  if (!olderNeigh.length) return;
  const oldestNeighbor = olderNeigh.reduce((oldest, current) => {
    const currDate = new Date(
      graph.getNodeAttribute(current, "published_time"),
    );
    const oldestDate = new Date(
      graph.getNodeAttribute(oldest, "published_time"),
    );
    return currDate < oldestDate ? current : oldest;
  });
  return oldestNeighbor;
}

export function evaluateGraph(graph: DirectedGraph) {
  const components = connectedComponents(graph);

  // Build ground truth groups
  const groups = graph
    .nodes()
    .reduce<Record<string, Set<string>>>((acc, item) => {
      const story_id = graph.getNodeAttribute(item, "story_id");
      if (!acc[story_id]) {
        acc[story_id] = new Set();
      }
      acc[story_id].add(item);
      return acc;
    }, {});

  const results = [];

  for (const component of components) {
    const componentSet = new Set(component);

    // Count group IDs inside component
    const counts: Record<string, number> = {};
    for (const node of component) {
      const groupId = graph.getNodeAttribute(node, "story_id");

      counts[groupId] = (counts[groupId] || 0) + 1;
    }


    // Dominant group in component
    const dominantGroup = Object.entries(counts).sort(
      (a, b) => b[1] - a[1],
    )[0][0];

    const trueGroup = groups[dominantGroup];

    const tp = counts[dominantGroup];
    const fp = component.length - tp;
    const fn = trueGroup.size - tp;

    const precision = tp / (tp + fp);
    const recall = tp / (tp + fn);

    const f1 = (2 * precision * recall) / (precision + recall);

    results.push({
      dominantGroup,
      componentSize: component.length,
      tp,
      fp,
      fn,
      precision,
      recall,
      f1,
    });
  }

  return results;
}

export function calculateOverallScore(results) {
  // Macro-average F1
  const macroF1 =
    results.reduce((sum, r) => sum + r.f1, 0) /
    results.length

  // Weighted-average F1
  const totalNodes =
    results.reduce((sum, r) => sum + r.componentSize, 0)

  const weightedF1 =
    results.reduce(
      (sum, r) => sum + r.f1 * r.componentSize,
      0
    ) / totalNodes

  return {
    macroF1,
    weightedF1,
  }
}