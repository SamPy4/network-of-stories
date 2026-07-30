<template>
  <div ref="container" class="graph-container"></div>
</template>

<script lang="ts" setup>
import { onMounted, onBeforeUnmount, ref, watch, onUnmounted } from "vue";
import { NodeSquareProgram } from "@sigma/node-square";
import Sigma from "sigma";
import DirectedGraph from "graphology";
import forceAtlas2 from "graphology-layout-forceatlas2";
import FA2Layout from "graphology-layout-forceatlas2/worker";
import { EdgeArrowProgram } from "sigma/rendering";
import {
  clearAllFormatting,
  darkenNotConnectedEdges,
  darkenNotSelectedNodes,
  highlightConnectedEdges,
  highlightOutComponents,
  highlightSelectedNode,
  highlightOldestNeighbor,
  increaseNodeSize,
  hideDegreeZeroNodes,
  findOutComponent,
  highlightNeigbors,
  colorNodesByDomain,
  highlightLargeComponents,
  highlightTopKBetweennessCetnralityPerComponent,
  evaluateGraph,
  calculateOverallScore,
} from "@/utils";
import { useGraphDataStore } from "@/stores/graph.store";

const emit = defineEmits([
  "nodeSelected",
  "nodeHovered",
  "nodeLeft",
  "edgeHovered",
  "edgeLeft",
  "graph",
  "outComponentGraph",
]);

const props = defineProps({
  endpoint: {
    type: String,
    default: "http://localhost:8000/graph",
  },
  thresholdValue: {
    type: Number,
    default: 0.8,
  },
  activeMenu: { type: String, default: "layout" },
  dataset: { type: String, default: "ten_articles" },
  togglePhysics: {
    type: Number,
    default: 1,
  },
  embedding: { type: String, default: "tf-idf" },
  refresh: { type: Number, default: 0 },
  domainColors: { type: Boolean, default: false },
  betweennessColors: { type: Boolean, default: false },
});

const graphStore = useGraphDataStore();

const container = ref<HTMLElement>();
const toggleForceAtlas = ref(1);
let sigmaInstance: Sigma | undefined = undefined;

const graph = ref<DirectedGraph>(new DirectedGraph());
let fa2Layout: FA2Layout | undefined = undefined;

async function initGraph() {
  console.log("Init graph...");
  if (!container.value) return;
  if (sigmaInstance) {
    sigmaInstance.clear();
    sigmaInstance.kill();
    sigmaInstance = undefined;
  }

  // Fetch graph data
  graph.value = new DirectedGraph();

  await updateGraph(true);
  enableForce();

  // hideDegreeZeroNodes(graph);
  clearAllFormatting(graph.value);

  // Initialize Sigma
  sigmaInstance = new Sigma(graph.value, container.value, {
    enableEdgeEvents: true,
    nodeProgramClasses: {
      square: NodeSquareProgram,
    },
    edgeProgramClasses: {
      arrow: EdgeArrowProgram,
      // arrow: ArrowColorEdgeProgram,
    },
  });

  clearAllFormatting(graph.value);

  bindClickNode();
  bindEnterNode();
  bindLeaveNode();
  bindEnterEdge();
  bindLeaveEdge();
  bindClickStage();
}

async function fetchGraphData() {
  if (props.thresholdValue <= 0.01) {
    console.warn("WARN threshold below 1%");
    return false;
  } else {
    const response = await fetch(
      `${props.endpoint}?dataset=${props.dataset}&embedding=${props.embedding}&threshold=${props.thresholdValue}`,
    );
    return await response.json();
  }
}

async function updateGraph(clear = false) {
  console.log("Updating graph...");
  const newData = await fetchGraphData();
  if (!newData) return;
  if (clear) {
    graph.value.clearEdges();
    populateGraph(newData);
    clearAllFormatting(graph.value);
    return;
  }
  populateGraph(newData);
}

function populateGraph(data) {
  console.log("The original graph has size: " + graph.value.nodes().length);
  data.nodes.forEach((node) => {
    if (!graph.value.hasNode(node.key)) {
      // if (!graphStore.graphPopulated) {
      graph.value.addNode(node.key, node.attributes);
      console.log("New node added !");
    }
  });
  // graphStore.graphPopulated = true;

  data.edges.forEach((edge) => {
    if (graph.value.hasEdge(edge.source, edge.target)) {
      // console.warn(`Edge already exists: ${edge.source} → ${edge.target}`);
      return;
    } else if (
      !graph.value.hasNode(edge.source) ||
      !graph.value.hasNode(edge.target)
    ) {
      console.warn(
        `No node! Source: ${graph.value.hasNode(edge.source)}; Target: ${graph.value.hasNode(edge.target)}`,
      );
    } else {
      graph.value.addDirectedEdge(edge.source, edge.target, edge.attributes);
    }
  });
}

function enableForce() {
  const physcisSettings = forceAtlas2.inferSettings(graph.value);
  fa2Layout = new FA2Layout(graph.value, {
    settings: { ...physcisSettings },
  });
  fa2Layout.start();
}

function toggleForce() {
  console.log("Nodes in graph: " + graph.value.nodes().length);
  console.log("Edges in graph: " + graph.value.edges().length);
  if (!fa2Layout) return;
  if (!toggleForceAtlas.value) {
    fa2Layout.start();
  } else {
    fa2Layout.stop();
  }
}

function bindClickNode() {
  if (!sigmaInstance) return;
  sigmaInstance.on("clickNode", ({ node}) => {
    const nodeId = node;
    if (!nodeId) return;
    if (!sigmaInstance) return;
    clearAllFormatting(graph.value);
    darkenNotConnectedEdges(graph.value, nodeId);
    darkenNotSelectedNodes(graph.value, nodeId);
    highlightNeigbors(graph.value, nodeId);
    highlightOldestNeighbor(graph.value, nodeId);
    // highlightConnectedEdges(graph.value, nodeId);
    highlightOutComponents(graph.value, nodeId);
    highlightSelectedNode(graph.value, nodeId);
    increaseNodeSize(graph.value, nodeId);

    console.log(graphStore.hasSelection);
    console.log(graphStore.selectedNode);
    graphStore.selectNode(nodeId);

    emit(
      "nodeSelected",
      { key: nodeId, attributes: graph.value.getNodeAttributes(nodeId) },
      sigmaInstance.graphToViewport(graph.value.getNodeAttributes(nodeId)).x,
      sigmaInstance.graphToViewport(graph.value.getNodeAttributes(nodeId)).y,
      graph.value.degree(nodeId),
      graph.value.mapNeighbors(nodeId, (n) => ({
        key: n,
        attributes: graph.value.getNodeAttributes(n),
      })),
    );

    // Construct the out component graph for the temporal view
    const outComponent = findOutComponent(graph.value, node);
    const outGraph = new DirectedGraph();
    outComponent.nodes?.forEach((n) =>
      outGraph.addNode(n, graph.value.getNodeAttributes(n)),
    );
    outComponent.edges?.forEach((e) => {
      const source = graph.value.source(e);
      const target = graph.value.target(e);
      const edgeAttrs = graph.value.getEdgeAttributes(e);
      outGraph.addDirectedEdge(source, target, edgeAttrs);
    });
    console.log("Out component graph:");
    console.log("Nodes: " + outGraph.nodes().length);
    console.log("Edges: " + outGraph.edges().length);
    graphStore.outComponentGraph = outGraph;
    // emit("outComponentGraph", outGraph);
  });
}

function bindEnterNode() {
  if (!sigmaInstance) return;
  sigmaInstance.on("enterNode", ({ node }) => {
    emit(
      "nodeHovered",
      graph.value.getNodeAttributes(node),
      sigmaInstance.graphToViewport(graph.value.getNodeAttributes(node)).x,
      sigmaInstance.graphToViewport(graph.value.getNodeAttributes(node)).y,
    );
  });
}

function bindLeaveNode() {
  if (!sigmaInstance) return;
  sigmaInstance.on("leaveNode", ({ node }) => {
    emit("nodeLeft");
  });
}

function bindEnterEdge() {
  if (!sigmaInstance) return;
  sigmaInstance.on("enterEdge", ({ edge }) => {
    emit(
      "edgeHovered",
      graph.value.getEdgeAttributes(edge),
      graph.value.getSourceAttribute(edge, "published_time"),
      graph.value.getTargetAttribute(edge, "published_time"),
    );
  });
}

function bindLeaveEdge() {
  if (!sigmaInstance) return;
  sigmaInstance.on("leaveEdge", ({ edge }) => {
    emit("edgeLeft", graph.value.getEdgeAttributes(edge));
  });
}

function bindClickStage() {
  if (!sigmaInstance) return;
  sigmaInstance.on("clickStage", ({ node }) => {
    const c = sigmaInstance.getCamera();
    clearAllFormatting(graph.value);
    if (props.domainColors) {
      colorNodesByDomain(graph.value);
    }
  });
}

watch(
  () => props.activeMenu,
  async (newValue) => {
    if (!sigmaInstance) return;

    if (newValue === "layout") {
      console.log("Layout selected");
      // run layout
    }
    if (newValue === "filter") {
      console.log("Filter selected");
      // filter nodes
    }
    if (newValue === "export") {
      console.log("Export selected");
      // export graph
    }
    if (newValue === "refresh") {
      await initGraph();
    }
  },
);

watch(
  () => props.refresh,
  async () => {
    await initGraph();
  },
);

watch(
  () => props.togglePhysics,
  (newValue) => {
    toggleForceAtlas.value = 1 - newValue;
    toggleForce();
  },
);

watch(
  () => props.dataset,
  async () => {
    await initGraph();
  },
);

watch(
  () => props.embedding,
  async () => {
    await initGraph();
  },
);

watch(
  () => props.thresholdValue,
  async (newValue) => {
    await updateGraph(true);
  },
);

watch(
  () => props.domainColors,
  async (newValue) => {
    if (newValue) {
      colorNodesByDomain(graph.value);
    } else {
      clearAllFormatting(graph.value);
    }
  },
);

watch(
  () => props.betweennessColors,
  async (newValue) => {
    console.log(evaluateGraph(graph.value));
    console.log(calculateOverallScore(evaluateGraph(graph.value)));
    highlightTopKBetweennessCetnralityPerComponent(graph.value, 5);
  },
);

onMounted(async () => {
  // setInterval(updateGraphData, 1000);
  await initGraph();
});

onBeforeUnmount(() => {
  if (graph) {
    console.log("Destroying graph of size: " + graph.value.nodes().length);
    graph.value = new DirectedGraph();
  }
  if (sigmaInstance) {
    sigmaInstance.kill();
    sigmaInstance = undefined;
  }
});

onUnmounted(() => {
  if (graph) {
    console.log("Destroying graph of size: " + graph.value.nodes().length);
    graph.value = new DirectedGraph();
  }
  if (sigmaInstance) {
    sigmaInstance.kill();
    sigmaInstance = undefined;
  }
});
</script>

<style scoped>
.graph-container {
  position: fixed;
  width: 82%;
  height: 61%;
  right: 0px;
  top: 0px;
  border-radius: 10px;
  border-style: groove;
  border-color: white;
  background-color: black;
}
</style>
