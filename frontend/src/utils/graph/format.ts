import DirectedGraph from "graphology";
import { forEachConnectedComponent } from "graphology-components";
import betweennessCentrality from "graphology-metrics/centrality/betweenness";
import { colors } from "@/utils/graph/colors";
import { sizes } from "@/utils/graph/colors";
import { findOutComponent, findOldestNeighbor } from "@/utils/graph/algorithms";

function gradientColor(t: number, thresholdValue: number) {
  function lerp(a: number, b: number, t: number) {
    return a + (b - a) * t;
  }

  // clamp just in case
  // t = Math.min(1, Math.max(0, t));
  t = Math.min(1, Math.max(0, (t - thresholdValue) / (1 - thresholdValue)));

  const start = { r: 0, g: 0, b: 255 }; // blue
  const end = { r: 255, g: 0, b: 0 }; // red

  const r = Math.round(lerp(start.r, end.r, t));
  const g = Math.round(lerp(start.g, end.g, t));
  const b = Math.round(lerp(start.b, end.b, t));

  return `rgb(${r}, ${g}, ${b})`;
}

export function clearAllFormatting(graph: DirectedGraph) {
  // Nodes
  // graph.nodes().forEach((n) => graph.setNodeAttribute(n, "label", ""));
  graph
    .nodes()
    .forEach((n) => graph.setNodeAttribute(n, "color", colors.node.default));

  const grouped = graph
    .nodes()
    .reduce<Record<string, string[]>>((acc, item) => {
      const story_id = graph.getNodeAttribute(item, "story_id");
      if (!acc[story_id]) {
        acc[story_id] = [];
      }
      acc[story_id].push(item);
      return acc;
    }, {});

  const color_story_ids = true;
  const highlight_true_origin = true;
  if (color_story_ids) {
    for (const [groupId, ids] of Object.entries(grouped)) {
      for (const id of ids) {
        graph.setNodeAttribute(id, "color", wordToRgb(groupId));
      }
    }

    graph.nodes().forEach((n) => {
      if (graph.getNodeAttribute(n, "story_id") != undefined) {
        if (graph.getNodeAttribute(n, "story_id") == "20260227130126111") {
          graph.setNodeAttribute(n, "color", "green");
        }
        if (graph.getNodeAttribute(n, "story_id") == "20260304123357106") {
          graph.setNodeAttribute(n, "color", "orange");
        }
        if (graph.getNodeAttribute(n, "story_id") == "20260304124042359") {
          graph.setNodeAttribute(n, "color", "cyan");
        }
        if (graph.getNodeAttribute(n, "story_id") == "20260305144404014") {
          graph.setNodeAttribute(n, "color", "white");
        }
        if (graph.getNodeAttribute(n, "story_id") == "20260305145041354") {
          graph.setNodeAttribute(n, "color", "pink");
        }
        if (graph.getNodeAttribute(n, "story_id") == "20260305145234643") {
          graph.setNodeAttribute(n, "color", "yellow");
        }
        if (graph.getNodeAttribute(n, "text").length <= "5") {
          graph.setNodeAttribute(n, "color", "red");
        }
      }
    });
  }

  graph
    .nodes()
    .forEach((n) => graph.setNodeAttribute(n, "size", sizes.node.default));
  graph.nodes().forEach((n) => graph.setNodeAttribute(n, "hidden", false));

  if (highlight_true_origin) {
    // Highlight the truly oldest source for each story
    for (const [groupId, ids] of Object.entries(grouped)) {
      let oldest_id = "";
      let oldest_time = new Date();
      for (const id of ids) {
        if (
          oldest_time > new Date(graph.getNodeAttribute(id, "published_time"))
        ) {
          oldest_id = id;
          oldest_time = new Date(graph.getNodeAttribute(id, "published_time"))
        } else {
          // console.log("Was not considered older:");
          // console.log(
          //   oldest_time.toString() +
          //     " <= " +
          //     new Date(graph.getNodeAttribute(id, "published_time")).toString(),
          // );
          // console.log("\n");
        }
      }
      graph.setNodeAttribute(oldest_id, "size", 10);
    }
  }

  // Edges
  graph
    .edges()
    .forEach((e) => graph.setEdgeAttribute(e, "color", colors.edge.default));
  graph
    .edges()
    .forEach((e) => graph.setEdgeAttribute(e, "size", sizes.edge.default));
  graph.edges().forEach((e) => graph.setEdgeAttribute(e, "hidden", false));
}

export function defaultTemporalFormatting(
  graph: DirectedGraph,
  thresholdValue: number,
) {
  graph
    .nodes()
    .forEach((n) =>
      graph.setNodeAttribute(n, "color", colors.node.temporalDefault),
    );
  graph
    .nodes()
    .forEach((n) =>
      graph.setNodeAttribute(n, "size", sizes.node.temporalDefault),
    );
  graph.nodes().forEach((n) => graph.setNodeAttribute(n, "hidden", false));
  graph
    .edges()
    .forEach((e) => graph.setEdgeAttribute(e, "color", colors.edge.default));
  graph.edges().forEach((e) => graph.setEdgeAttribute(e, "hidden", false));
  // Highlight all edges in the temporal graph
  graph
    .nodes()
    .forEach((n) => highlightConnectedEdges(graph, n, thresholdValue));
  graph.edges().forEach((e) => graph.setEdgeAttribute(e, "hidden", false));
}

export function highlightLargeComponents(graph: DirectedGraph) {
  forEachConnectedComponent(graph, (component) => {
    if (component.length >= 5) {
      const comopnentIdentifier = component.toString();
      component.forEach((n) =>
        graph.setNodeAttribute(n, "color", wordToRgb(comopnentIdentifier)),
      );
    }
  });
}

export function darkenNotConnectedEdges(graph: DirectedGraph, nodeId: string) {
  const connectedEdges = graph.edges(nodeId);
  const notConnectedEdges = graph.filterEdges(
    (e) => !connectedEdges.includes(e),
  );
  notConnectedEdges.map((e) =>
    graph.setEdgeAttribute(e, "color", colors.edge.darken),
  );
  notConnectedEdges.map((e) =>
    graph.setEdgeAttribute(e, "size", sizes.edge.decreased),
  );
}

export function hideNotConnectedEdges(graph: DirectedGraph, nodeId: string) {
  const connectedEdges = graph.edges(nodeId);
  const notConnectedEdges = graph.filterEdges(
    (e) => !connectedEdges.includes(e),
  );
  notConnectedEdges.map((e) => graph.setEdgeAttribute(e, "hidden", true));
}

export function hideNotSelectedNodes(graph: DirectedGraph, nodeId: string) {
  const focusedNodes = graph.neighbors(nodeId);
  focusedNodes.push(nodeId);
  const notSelectedNodes = graph.filterNodes((n) => !focusedNodes.includes(n));
  notSelectedNodes.map((n) => graph.setNodeAttribute(n, "hidden", true));
}

export function darkenNotSelectedNodes(graph: DirectedGraph, nodeId: string) {
  const focusedNodes = graph.neighbors(nodeId);
  focusedNodes.push(nodeId);
  const notSelectedNodes = graph.filterNodes((n) => !focusedNodes.includes(n));
  notSelectedNodes.map((n) =>
    graph.setNodeAttribute(n, "color", colors.node.darken),
  );
}

export function highlightOutComponents(graph: DirectedGraph, nodeId: string) {
  const outComponents = findOutComponent(graph, nodeId);
  if (!outComponents.nodes || !outComponents.edges) return;

  outComponents.nodes.forEach((n) => {
    graph.setNodeAttribute(n, "color", colors.node.outComponent);
  });

  outComponents.edges.forEach((e) => {
    graph.setEdgeAttribute(e, "color", colors.edge.outComponent);
  });

  //   const emitGraph = new DirectedGraph();
  //   const componentNodes = graph.filterNodes((n) => visitedNodes.has(n));
  //   const componentEdges = graph.filterEdges((e) => visitedEdges.has(e));

  //   componentNodes.forEach((n) =>
  //     emitGraph.addNode(n, graph.getNodeAttributes(n)),
  //   );
  //   componentEdges.forEach((e) => {
  //     emitGraph.addEdge(
  //       graph.source(e),
  //       graph.target(e),
  //       graph.getEdgeAttributes(e),
  //     );
  //   });

  //   console.log("emitGraph Edges:");
  //   console.log(emitGraph.edges());
  //   emit("graph", emitGraph);
}

export function highlightSelectedNode(graph: DirectedGraph, nodeId: string) {
  graph.setNodeAttribute(nodeId, "color", colors.node.select);
}

export function increaseNodeSize(graph: DirectedGraph, nodeId: string) {
  graph.setNodeAttribute(nodeId, "size", sizes.node.selected);
}

export function highlightOldestNeighbor(graph: DirectedGraph, nodeId: string) {
  const oldestNeighbor = findOldestNeighbor(graph, nodeId);
  if (!oldestNeighbor) return;
  graph.setNodeAttribute(oldestNeighbor, "color", colors.node.oldest);
}

export function highlightConnectedEdges(
  graph: DirectedGraph,
  nodeId: string,
  thresholdValue: number,
) {
  graph.mapEdges(nodeId, (e) =>
    graph.setEdgeAttribute(
      e,
      "color",
      gradientColor(graph.getEdgeAttribute(e, "weight"), thresholdValue),
    ),
  );
}

export function highlightNeigbors(graph: DirectedGraph, nodeId: string) {
  graph
    .neighbors(nodeId)
    .forEach((n) => graph.setNodeAttribute(n, "color", colors.node.neighbor));
}

export function hideDegreeZeroNodes(graph: DirectedGraph) {
  if (graph) {
    const filteredNodes = graph.filterNodes((n) => graph.degree(n) == 0);
    filteredNodes.forEach((n) => graph.dropNode(n));
  }
}

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
    hash |= 0;
  }
  return hash;
}

function hslToRgb(h: number, s: number, l: number) {
  s /= 100;
  l /= 100;

  const k = (n: number) => (n + h / 30) % 12;
  const a = s * Math.min(l, 1 - l);
  const f = (n: number) =>
    l - a * Math.max(-1, Math.min(k(n) - 3, Math.min(9 - k(n), 1)));

  return [
    Math.round(255 * f(0)),
    Math.round(255 * f(8)),
    Math.round(255 * f(4)),
  ];
}

function wordToRgb(word: string): string {
  const hash = hashString(word);

  const hue = Math.abs(hash) % 360;
  const saturation = 60 + (hash % 20); // 60–80
  const lightness = 45 + (hash % 10); // 45–55

  const [r, g, b] = hslToRgb(hue, saturation, lightness);

  return `rgb(${r}, ${g}, ${b})`;
}

export function colorNodesByDomain(graph: DirectedGraph) {
  // For testing, count the frequencies of domains and sort the list
  const freq: Record<string, number> = {};
  const domains = graph.mapNodes((n) => graph.getNodeAttribute(n, "domain"));
  for (const domain of domains) {
    freq[domain] = (freq[domain] || 0) + 1;
  }
  const entries = Object.entries(freq);
  // It turns out that there are not many (~4) articles per domain...
  entries.sort((a, b) => b[1] - a[1]);

  console.log(entries);
  // console.log(bet);
  // console.log(bet.sort((a, b) => b[1] - a[1]));

  graph.forEachNode((n) =>
    graph.setNodeAttribute(
      n,
      "color",
      wordToRgb(graph.getNodeAttribute(n, "domain")),
    ),
  );

  console.log("Loops: " + graph.selfLoopCount);
}

export function highlightTopKBetweennessCetnralityPerComponent(
  graph: DirectedGraph,
  k: number,
) {
  betweennessCentrality.assign(graph, { normalized: true });
  forEachConnectedComponent(graph, (component) => {
    if (component.length < 5) return;
    const bet: Array = component.map((n) => [
      n,
      graph.getNodeAttribute(n, "betweennessCentrality"),
    ]);
    bet.sort((a, b) => b[1] - a[1]);
    const topK = bet.slice(0, k).map((tk) => tk[0]);
    console.log(topK[0]);
    component.forEach((n) => {
      if (topK.includes(n)) {
        if (topK[0] === n) {
          graph.setNodeAttribute(n, "size", 5);
        }
        graph.setNodeAttribute(n, "color", "red");
      }
    });
  });

  // bet.sort((a, b) => b[1] - a[1]);
  // const topK = bet.slice(0, k);

  // graph.forEachNode((n) => {
  //   if (topK.includes(n)) {
  //     graph.setNodeAttribute(n, "size", 20);
  //   }
  // });

  // forEachConnectedComponent(graph, (component) => {
  //   if (component.length >= 5) {
  //     const comopnentIdentifier = component.toString();
  //     component.forEach((n) =>
  //       graph.setNodeAttribute(n, "color", wordToRgb(comopnentIdentifier)),
  //     );
  //   }
  // });
}
