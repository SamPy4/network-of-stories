<template>
  <div class="app-root">
    <SideMenu
      :items="menuItems"
      :activeId="activeItem"
      :datasourceOptions="datasourceOptions"
      :embeddingOptions="embeddingOptions"
      :datasource="activeDatasource"
      :physicsState="togglePhysics"
      @select="handleSelect"
      @selectDatasource="handleDatasource"
      @selectEmbedding="handleEmbedding"
      @refresh="handleRefresh"
      @toggleAtlas="handleTogglePhysics"
      @updateThresholdValue="handleThreshold"
      @toggleGraphView="handleToggleGraphView"
      @domainColors="handleDomainColors"
      @betweenness="handleBetweenness"
    />
    <h1
      style="
        position: fixed;
        color: white;
        left: 40px;
        top: 10px;
        padding: 20px;
      "
    >
      {{ !graphView ? "Force directed" : "Temporal tree" }}
    </h1>
    <GraphView
      v-if="graphView == 0"
      endpoint="http://localhost:8000/graph"
      :activeMenu="activeItem"
      :dataset="activeDatasource"
      :embedding="activeEmbedding"
      :refresh="activeRefresh"
      :togglePhysics="togglePhysics"
      :thresholdValue="thresholdValue"
      :domainColors="domainColors"
      :betweennessColors="betweennessColors"
      @outComponentGraph="handleOutComponentGraph"
      @nodeSelected="handleNodeSelect"
      @nodeLeft="handleLeaveNode"
      @nodeHovered="handleNodeHover"
      @edgeHovered="handleEdgeHover"
      @edgeLeft="handleLeaveEdge"
    />
    <TemporalGraph
      v-if="graphView == 1"
      @nodeSelected="handleTemporalNodeSelect"
    />
    <NodeTooltip
      :visible="tooltipVisible"
      :x="selectedNodeX"
      :y="selectedNodeY"
      :title="selectedNodeLabel"
    ></NodeTooltip>
    <EdgeTooltip
      :visible="tooltipVisible"
      :x="selectedNodeX"
      :y="selectedNodeY"
      :title="selectedNodeLabel"
    ></EdgeTooltip>
    <ArticleMenu
      :selectedNode="selectedNode"
      :temporalSelectedNode="temporalNodeSelected"
      :connectedNodes="connectedNodes"
      :selectedEdgeArticles="selectedEdgeArticles"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import DirectedGraph from "graphology";
import GraphView from "./components/GraphView.vue";
import SideMenu from "./components/SideMenu.vue";
import ArticleMenu from "./components/ArticleMenu.vue";
import NodeTooltip from "./components/NodeTooltip.vue";
import EdgeTooltip from "./components/EdgeTooltip.vue";
import TemporalGraph from "./components/TreeGraph.vue";
import { useGraphDataStore } from "@/stores/graph.store";

const graphStore = useGraphDataStore();

const activeItem = ref(undefined);
const activeDatasource = ref("combined_ground_news");
const activeEmbedding = ref("tf-idf");
const connectedNodes = ref([]);
const selectedNode = ref([]);
const temporalNodeSelected = ref([]);
const selectedEdgeArticles = ref([]);
const togglePhysics = ref(1);
const thresholdValue = ref(1.0);
const domainColors = ref(false);
const betweennessColors = ref(false);

const activeRefresh = ref(0);
const graphView = ref(0);

const graph = ref();
const outComponentGraph = ref();

let tooltipVisible = ref(false);
let selectedNodeX = ref(0);
let selectedNodeY = ref(0);
let selectedNodeLabel = ref("");

const menuItems = [
  //  { id: "layout", label: "Layout", icon: "🧩" },
  //  { id: "filter", label: "Filter", icon: "🔍" },
  //  { id: "export", label: "Export", icon: "⬇️" },
  //  { id: "refresh", label: "Refresh", icon: "🔄" },
];

const datasourceOptions = [
  // { id: "data1.json", label: "Data 1" },
  // { id: "data2.json", label: "Data 2" },
  // { id: "data3.json", label: "Data 3" },
  // { id: "data4.json", label: "Data 4" },
  // { id: "data5.json", label: "Data 5" },
  // { id: "data6.json", label: "Data 6" },
  // { id: "data7.json", label: "Data 7" },
  // { id: "data8.json", label: "Data 8" },
  { id: "combined_ecbizfin_2000", label: "Combined 2000" },
  { id: "combined_ecbizfin_4000", label: "Combined 4000" },
  { id: "combined_ecbizfin_8000", label: "Combined 8000" },
  { id: "ten_articles", label: "Ten articles" },
  { id: "combined_ground_news", label: "Ground news" },
  { id: "combined_ground_news2", label: "Ground news 2" },
  {
    id: "Economy_Business_and_Finance_2025",
    label: "Economy_Business_and_Finance_2025",
  },
  { id: "postgres", label: "Postgres data" },
  { id: "stream1", label: "Stream 1" },
  { id: "tell_me_again_set", label: "Tell me again!" },
  { id: "tell_me_again_set_nonanon", label: "Tell me again! (not anon)" },
  { id: "test_network_formulation", label: "Test network formulation" },
  { id: "disaster_and_accident", label: "Disasters and Accidents (1000)" },
  {
    id: "combined_disaster_and_accident",
    label: "Disasters and Accidents (en)",
  },
];

const embeddingOptions = [
  { id: "tf-idf", label: "TF-IDF" },
  { id: "alibaba", label: "Alibaba GTE" },
  { id: "random", label: "Random" },
];

const props = defineProps({
  endpoint: {
    type: String,
    default: "http://localhost:8000/graph",
  },
});

function formatDateDifference(dateStr1, dateStr2) {
  const date1 = new Date(dateStr1);
  const date2 = new Date(dateStr2);

  let diffMs = Math.abs(date2 - date1); // milliseconds difference

  const msInSec = 1000;
  const msInMin = msInSec * 60;
  const msInHour = msInMin * 60;
  const msInDay = msInHour * 24;

  const days = Math.floor(diffMs / msInDay);
  diffMs -= days * msInDay;

  const hours = Math.floor(diffMs / msInHour);
  diffMs -= hours * msInHour;

  const minutes = Math.floor(diffMs / msInMin);
  diffMs -= minutes * msInMin;

  const seconds = Math.floor(diffMs / msInSec);

  const parts = [];
  if (days) parts.push(days + "d");
  if (hours) parts.push(hours + "h");
  if (minutes) parts.push(minutes + "m");
  if (seconds || parts.length === 0) parts.push(seconds + "s");

  return parts.join(" ");
}

function handleSelect(id) {
  activeItem.value = id;
  console.log("Menu selected:", id);
}

function handleDatasource(id) {
  activeDatasource.value = id;
}
function handleEmbedding(id) {
  activeEmbedding.value = id;
}

function handleNodeSelect(
  clickedNode,
  nodeDisplayX,
  nodeDisplayY,
  degree,
  neighborNodes,
) {
  console.log(clickedNode);
  selectedNode.value = clickedNode;
  connectedNodes.value = neighborNodes;

  tooltipVisible.value = true;
  // selectedNodeLabel.value = selected_node.attributes.tooltip_label;
  selectedNodeLabel.value = degree;

  const app = document.getElementById("app");

  app.addEventListener("mousemove", function e(event) {
    const x = event.clientX; // X relative to viewport
    const y = event.clientY; // Y relative to viewport
    // selectedNodeX.value = x + 20; //  selected_node.attributes.x + 200;
    // selectedNodeY.value = y + 100; // selected_node.attributes.y + 200;
    selectedNodeX.value = nodeDisplayX + 450;
    selectedNodeY.value = nodeDisplayY + 70;
    console.log("THE XY:");
    console.log(x);
    console.log(y);
    console.log(nodeDisplayX);
    console.log(nodeDisplayY);
    app.removeEventListener("mousemove", e);
  });
  // selectedNodeX = sigmaInstance.getNodeDisplayData(node).x;
  // selectedNodeY = sigmaInstance.getNodeDisplayData(node).y;
}

function handleNodeHover(hoveredNodeAttributes, nodeDisplayX, nodeDisplayY) {
  tooltipVisible.value = true;
  selectedNodeLabel.value = hoveredNodeAttributes["domain"];
  app.addEventListener("mousemove", function e(event) {
    const x = event.clientX; // X relative to viewport
    const y = event.clientY; // Y relative to viewport
    // selectedNodeX.value = x + 20; //  selected_node.attributes.x + 200;
    // selectedNodeY.value = y + 100; // selected_node.attributes.y + 200;
    selectedNodeX.value = nodeDisplayX + 450;
    selectedNodeY.value = nodeDisplayY + 70;
    console.log("THE XY:");
    console.log(x);
    console.log(y);
    console.log(nodeDisplayX);
    console.log(nodeDisplayY);
    app.removeEventListener("mousemove", e);
  });
}

function handleLeaveNode() {
  tooltipVisible.value = false;
}

function handleEdgeHover(edgeAttributes, source_date, target_date) {
  tooltipVisible.value = true;
  // selectedNodeLabel.value = selected_node.attributes.tooltip_label;

  selectedNodeLabel.value = formatDateDifference(source_date, target_date);
  selectedNodeLabel.value += " [";
  selectedNodeLabel.value += Number(
    edgeAttributes.weight.toFixed(3),
  ).toString();
  selectedNodeLabel.value += "]";

  const app = document.getElementById("app");

  app.addEventListener("mousemove", function e(event) {
    const x = event.clientX; // X relative to viewport
    const y = event.clientY; // Y relative to viewport
    selectedNodeX.value = x + 20; //  selected_node.attributes.x + 200;
    selectedNodeY.value = y + 100; // selected_node.attributes.y + 200;
    app.removeEventListener("mousemove", e);
  });
}

function handleLeaveEdge(edgeAttributes) {
  console.log("Edge left");
  tooltipVisible.value = false;
}

function handleThreshold(newThreshold) {
  thresholdValue.value = newThreshold.value;
}

function handleTogglePhysics() {
  togglePhysics.value = 1 - togglePhysics.value;
}

function handleRefresh() {
  console.log(activeRefresh.value);
  activeRefresh.value = 1 - activeRefresh.value;
}

function handleToggleGraphView() {
  graphView.value = 1 - graphView.value;
  connectedNodes.value = graphStore.outComponentGraph.nodes().map((n) => ({
    key: n,
    attributes: graphStore.outComponentGraph?.getNodeAttributes(n),
  }));
}

function handleGraphEmit(newGraph: DirectedGraph) {
  graph.value = newGraph;
}

function handleOutComponentGraph(outGraph: DirectedGraph) {
  handleOutComponentGraph.value = outGraph;
}

function handleTemporalNodeSelect(node, componentNodes) {
  console.log(node);
  console.log(node.key);
  console.log(node.node);
  temporalNodeSelected.value = node;
  selectedNode.value = node;
  connectedNodes.value = componentNodes;
}

function handleDomainColors() {
  domainColors.value = !domainColors.value;
  graphStore.colorHighlightState.node.default = false;
}

function handleBetweenness() {
  betweennessColors.value = !betweennessColors.value;
}
</script>

<style>
.app-root {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
  background-color: black;
}
</style>
