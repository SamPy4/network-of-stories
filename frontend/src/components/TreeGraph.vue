<script setup lang="ts">
import { onMounted, ref } from "vue";
import { NodeSquareProgram } from "@sigma/node-square";
import Sigma from "sigma";
import { EdgeArrowProgram } from "sigma/rendering";
import { DirectedGraph } from "graphology";
import {
  highlightConnectedEdges,
  highlightSelectedNode,
  highlightNeigbors,
  defaultTemporalFormatting,
  darkenNotSelectedNodes,
  darkenNotConnectedEdges,
  hideNotConnectedEdges,
  hideNotSelectedNodes,
} from "@/utils";
import { useGraphDataStore } from "@/stores/graph.store";

const emit = defineEmits(["nodeSelected"]);

const graphStore = useGraphDataStore();

const container = ref(null);
let renderer: Sigma;
const temporalGraph = ref<DirectedGraph>(new DirectedGraph());
const rootId = ref<string>("");
const ticks = ref([]);
let cameraListener = false;
let draggedNodeId: string = "";
let previousNodeColor: string = "white";

const scaleSpacingX = ref(10);
const scaleSpacingY = ref(120);
const showOnlyNeighbors = ref(false);

/**
 * Compute a temporal left-to-right layout
 */
function computeTemporalLayout() {
  if (!temporalGraph.value.nodes()) return;

  const positions = {};

  // --- 1. Collect and sort nodes by time ---
  const nodes = temporalGraph.value.nodes().map((id) => ({
    id,
    time:
      new Date(
        temporalGraph.value.getNodeAttribute(id, "published_time"),
      ).getTime() || 0,
  }));

  nodes.sort((a, b) => a.time - b.time);
  nodes.forEach((n) => {
    console.log(n.time);
  });

  const times = nodes.map((n) => n.time).filter((t) => Number.isFinite(t));

  const minTime = times.length ? Math.min(...times) : 0;
  const maxTime = times.length ? Math.max(...times) : 1;
  const timeRange = maxTime - minTime || 1;
  const width = container.value.clientWidth;

  const xScale = (t) => ((t - minTime) / timeRange) * width;

  // --- 2. BFS from root to structure vertical layers ---
  const visited = new Set();
  const queue = [{ id: rootId.value, depth: 0 }];
  const layers = new Map();

  while (queue.length) {
    const { id, depth } = queue.shift();
    if (visited.has(id)) continue;
    visited.add(id);

    if (!layers.has(depth)) layers.set(depth, []);
    layers.get(depth).push(id);

    temporalGraph.value.forEachOutNeighbor(id, (neighbor) => {
      queue.push({ id: neighbor, depth: depth + 1 });
    });
  }

  // --- 3. Assign positions ---
  const verticalSpacing = scaleSpacingY.value; //120;
  const horizontalSpacing = scaleSpacingX.value;

  layers.forEach((layerNodes, depth) => {
    layerNodes.forEach((id, index) => {
      const time =
        new Date(
          temporalGraph.value.getNodeAttribute(id, "published_time"),
        ).getTime() || 0;

      positions[id] = {
        x: xScale(time) * horizontalSpacing,
        y: depth * verticalSpacing + index * 100,
      };
    });
  });

  if (!cameraListener) {
    renderer.getCamera().on("updated", () => {
      // force Vue to re-render ticks
      generateTicks(temporalGraph.value);
    });
    cameraListener = true;
  }

  return positions;
}

/**
 * Apply layout to graph
 */
function applyLayout() {
  console.log("Applying layout");
  console.log(temporalGraph.value);
  console.log(temporalGraph.value?.nodes().length);
  console.log(temporalGraph.value?.edges().length);
  if (!temporalGraph.value) return;
  if (!temporalGraph.value.nodes() || !rootId.value) return;

  const positions = computeTemporalLayout(temporalGraph.value, rootId.value);

  Object.entries(positions).forEach(([id, pos]) => {
    temporalGraph.value.setNodeAttribute(id, "x", pos.x);
    temporalGraph.value.setNodeAttribute(id, "y", pos.y);
  });
  temporalGraph.value.forEachNode((id) => {
    console.log("After x: " + temporalGraph.value.getNodeAttribute(id, "x"));
  });

  temporalGraph.value.forEachEdge((edge) => {
    temporalGraph.value.setEdgeAttribute(edge, "type", "arrow");
    temporalGraph.value.setEdgeAttribute(edge, "color", "#ffffff");
    temporalGraph.value.setEdgeAttribute(edge, "size", 3);
  });
  temporalGraph.value.nodes().forEach((n) => {
    if (n) {
      temporalGraph.value.setNodeAttribute(n, "size", 10);
      temporalGraph.value.setNodeAttribute(n, "color", "#ffffff");
    }
  });

  defaultTemporalFormatting(temporalGraph.value, graphStore.thresholdValue);
  if (showOnlyNeighbors.value) {
    hideNotSelectedElements();
  }

  if (renderer) renderer.refresh();
}

function generateTicks() {
  // console.log("TIMELIEN OGES BRRR");
  const timeAndX: Array<Object> = [];
  let i = 0;
  temporalGraph.value.nodes().forEach((id) => {
    if (
      showOnlyNeighbors.value &&
      !(id === graphStore.selectedNode) &&
      !temporalGraph.value.areNeighbors(id, graphStore.selectedNode)
    ) {
      return;
    }
    let t = new Date(
      temporalGraph.value.getNodeAttribute(id, "published_time"),
    ).getTime();
    let date = new Date(
      temporalGraph.value.getNodeAttribute(id, "published_time"),
    );
    const formatted = new Intl.DateTimeFormat([], {
      timeZone: "UTC",
      day: "2-digit",
      month: "2-digit",
      year: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    })
      .format(date)
      .replace(",", "");
    const x = temporalGraph.value.getNodeAttribute(id, "x");
    const y = temporalGraph.value.getNodeAttribute(id, "y");
    i += 1;
    timeAndX.push({
      time: t,
      x: renderer.graphToViewport({ x, y }).x - 50, // Hokkuspokkus -50px
      y: i % 3 ? (i % 3 === 1 ? 5 : 15) : -10,
      label: formatted,
      nodeId: id,
    });
  });

  timeAndX.sort((a, b) => {
    return a.time - b.time;
  });

  var j = 0;
  timeAndX.map((tick) => {
    j += 1;
    tick.y = j % 3 ? (j % 3 === 1 ? 5 : 20) : -10;
    return tick;
  });
  console.log("THE J " + j);
  ticks.value = timeAndX;
}

function setNodeDrag() {
  // Add listener to node drag
  const camera = renderer.getCamera();
  const mouse = renderer.getMouseCaptor();
  renderer.on("downNode", (n) => {
    draggedNodeId = n.node;
    camera.disable(); // stop panning
  });

  mouse.on("mousemove", (e) => {
    if (!temporalGraph.value.nodes()) return;
    // Convert screen → graph coordinates
    const pos = renderer.viewportToGraph({
      x: e.x,
      y: e.y,
    });

    // Update node position
    if (draggedNodeId) {
      // temporalGraph.value.setNodeAttribute(draggedNodeId, "x", pos.x); // Allow x-axis repositioning
      temporalGraph.value.setNodeAttribute(draggedNodeId, "y", pos.y);

      // Re-render
      renderer.refresh();
    }
  });

  // On node release
  renderer.getMouseCaptor().on("mouseup", () => {
    draggedNodeId = "";
    camera.enable();
  });
}

function bindClickStage(renderer: Sigma) {
  renderer.on("clickStage", () => {
    if (!temporalGraph.value.nodes()) return;
    // if (showOnlyNeighbors.value) showOnlyNeighbors.value = false;
    defaultTemporalFormatting(temporalGraph.value, graphStore.thresholdValue);
    if (showOnlyNeighbors.value) {
      highlightSelectedNode(temporalGraph.value, graphStore.selectedNode);
      highlightConnectedEdges(
        temporalGraph.value,
        graphStore.selectedNode,
        graphStore.thresholdValue,
      );
      highlightNeigbors(temporalGraph.value, graphStore.selectedNode);
      showOnlyNeighbors.value = false;
    }
  });
}

function bindClickNode(renderer: Sigma) {
  renderer.on("clickNode", (node) => {
    if (!temporalGraph.value) return;
    graphStore.selectedNode = node.node;
    console.log(graphStore.thresholdValue);
    defaultTemporalFormatting(temporalGraph.value, graphStore.thresholdValue);
    highlightSelectedNode(temporalGraph.value, node.node);
    highlightConnectedEdges(
      temporalGraph.value,
      node.node,
      graphStore.thresholdValue,
    );
    highlightNeigbors(temporalGraph.value, node.node);
    if (showOnlyNeighbors.value) {
      hideNotSelectedElements();
    }
  });
}

function enterTimeTick(nodeId) {
  // Enter tick with mouse
  previousNodeColor = temporalGraph.value?.getNodeAttribute(nodeId, "color");
  temporalGraph.value?.setNodeAttribute(nodeId, "color", "red");
}
function leaveTimeTick(nodeId) {
  // Leave tick with mouse
  temporalGraph.value?.setNodeAttribute(nodeId, "color", previousNodeColor);
}

function handleScaleChange() {
  applyLayout();
  highlightSelectedNode(temporalGraph.value, graphStore.selectedNode);
  highlightConnectedEdges(
    temporalGraph.value,
    graphStore.selectedNode,
    graphStore.thresholdValue,
  );
  highlightNeigbors(temporalGraph.value, graphStore.selectedNode);
}

function hideNotSelectedElements() {
  darkenNotSelectedNodes(temporalGraph.value, graphStore.selectedNode);
  hideNotConnectedEdges(temporalGraph.value, graphStore.selectedNode);
  hideNotSelectedNodes(temporalGraph.value, graphStore.selectedNode);
  hideNotSelectedTicks();
}

function hideNotSelectedTicks() {}

onMounted(() => {
  if (!graphStore.outComponentGraph) return;
  if (!graphStore.selectedNode) return;

  temporalGraph.value = graphStore.outComponentGraph.copy();
  rootId.value = graphStore.selectedNode;

  renderer = new Sigma(temporalGraph.value, container.value, {
    allowInvalidContainer: true,
    renderLabels: true,
    enableEdgeEvents: true,
    nodeProgramClasses: {
      square: NodeSquareProgram,
    },
    edgeProgramClasses: {
      arrow: EdgeArrowProgram,
      // arrow: ArrowColorEdgeProgram,
    },
    nodeReducer(node, data) {
      if (data?.hidden) {
        return {
          ...data,
          hidden: true,
        };
      }
      return data;
    },
    edgeReducer(edge, data) {
      if (data?.hidden) {
        return {
          ...data,
          hidden: true,
        };
      }
      return data;
    },
  });

  bindClickStage(renderer);
  bindClickNode(renderer);
  setNodeDrag();

  applyLayout();
  generateTicks();
});
</script>

<template>
  <div ref="container" class="graph-container">
    <div style="position: absolute; margin: 40px; z-index: 20">
      <h4 style="position: fixed; top: 10px; color: white">
        Horizontal spacing: {{ scaleSpacingX }}
      </h4>
      <input
        type="range"
        min="1"
        max="100"
        step="1"
        style="position: fixed; top: 50px"
        @change="handleScaleChange"
        v-model.number="scaleSpacingX"
      />
      <h4 style="position: fixed; color: white">
        Vertical spacing: {{ scaleSpacingY }}
      </h4>
      <input
        type="range"
        min="50"
        max="20000"
        step="1"
        style="position: fixed; top: 95px"
        @change="handleScaleChange"
        v-model.number="scaleSpacingY"
      />
      <h4 style="position: fixed; top: 100px; color: white">
        Show only neighboring nodes: {{ showOnlyNeighbors }}
      </h4>
      <input
        type="checkbox"
        @change="handleScaleChange"
        v-model="showOnlyNeighbors"
        style="position: fixed; top: 150px"
      />
    </div>
    <!-- Timeline overlay -->
    <div class="timeline">
      <div
        v-for="tick in ticks"
        :key="tick.time"
        class="tick"
        :style="{ left: tick.x + 'px', top: tick.y + 'px' }"
        @mouseenter="enterTimeTick(tick.nodeId)"
        @mouseleave="leaveTimeTick(tick.nodeId)"
      >
        <div class="tick-line"></div>
        <div class="tick-label">{{ tick.label }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.graph-container {
  position: absolute;
  width: 82%;
  height: 60%;
  right: 10px;
  top: 10px;
  border-radius: 10px;
  border-style: groove;
  border-color: white;
  border-style: dashed;
  border-bottom: none;
  background-color: black;
  overflow: hidden;
}
.timeline {
  position: absolute;
  bottom: 0;
  width: 100%;
  height: 60px;
  background-color: black;
  border-color: white;
  border-style: solid;
  border-bottom: none;
  z-index: 2;
}

.tick {
  position: absolute;
  text-align: center;
  z-index: 1;
}

/* vertical line */
.tick-line {
  width: 1px;
  height: 14px;
  background: rgba(255, 255, 255, 0.7);
  margin: 0 auto;
  transition: background 0.1s ease;
  z-index: -1;
}

/* label (bigger!) */
.tick-label {
  color: rgba(255, 255, 255, 0.95);
  font-size: 14px;
  font-weight: 500;
  margin-top: 6px;
  white-space: nowrap;
}

.tick:hover {
  transform: scale(1.8);
  transform-origin: center;
  transition: transform 0.1s ease-in-out;
  background-color: black;
  margin: 3px;
  margin-bottom: 7px;
  padding-bottom: 70px;
  cursor: text;
  z-index: 2;
}

/* subtle vertical grid across graph */
.tick::before {
  content: "";
  position: absolute;
  top: -1000px;
  left: 50%;
  width: 2px;
  height: 1000px;
  transform: translateX(-50%);
  transition:
    background 0.2s ease,
    width 0.2s ease;
  background: rgba(255, 255, 255, 0.2);
  z-index: 1;
}

/* highlight short tick line */
.tick:hover .tick-line {
  background: #ff4d4d;
}

/* highlight full vertical grid line */
.tick:hover::before {
  background: rgba(255, 77, 77, 0.6);
  width: 2px; /* make it more visible */
}
</style>
