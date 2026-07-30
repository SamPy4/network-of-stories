<template>
  <aside class="side-menu">
    <ul class="menu-list">
      <li @click="emit('toggleAtlas')">
        Toggle force atlas: {{ physicsState }}
      </li>
      <li
        v-for="item in items"
        :key="item.id"
        :class="{ active: item.id === activeId }"
        @click="onSelect(item.id)"
      >
        <span class="menu-icon">{{ item.icon }}</span>
        <span class="menu-label">{{ item.label }}</span>
      </li>
    </ul>

    <div class="threshold-slider">
      <p class="threshold-value">Threshold: {{ thresholdValue }}</p>
      <input
        type="range"
        min="0"
        max="1"
        step="0.01"
        @change="handleThresholdChange"
        v-model.number="thresholdValue"
      />
    </div>

    <!-- Datasource Dropdown -->
    <div class="datasource">
      <div class="datasource-title">Datasource</div>
      <select v-model="selected" @change="onDatasourceChange">
        <option
          v-for="source in datasourceOptions"
          :key="source.id"
          :value="source.id"
        >
          {{ source.label }}
        </option>
      </select>
    </div>

    <!-- Embedding Dropdown -->
    <div class="embedding">
      <div class="embedding-title">Embedding</div>
      <select v-model="selectedEmbedding" @change="onEmbeddingChange">
        <option
          v-for="source in embeddingOptions"
          :key="source.id"
          :value="source.id"
        >
          {{ source.label }}
        </option>
      </select>
    </div>
    <div class="refresh-button" @click="emit('refresh')">
      <span class="refresh-title">🔄 Refresh</span>
    </div>
    <div class="refresh-button" @click="emit('toggleGraphView')">
      <span class="refresh-title">Toggle graph view</span>
    </div>
    <div class="refresh-button" @click="emit('domainColors')">
      <span class="refresh-title">Highlight domains</span>
    </div>
    <div class="refresh-button" @click="emit('betweenness')">
      <span class="refresh-title">Highlight betweenness centralities</span>
    </div>
  </aside>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from "vue";
import { useGraphDataStore } from "@/stores/graph.store";

const props = defineProps({
  items: {
    type: Array,
    required: true,
    default: () => [],
  },
  activeId: {
    type: [String, Number],
    default: null,
  },
  datasourceOptions: {
    type: Array,
    default: () => [],
  },
  embeddingOptions: {
    type: Array,
    default: () => [],
  },
  datasource: {
    type: String,
    default: "",
  },
  embedding: {
    type: String,
    default: "",
  },
  physicsState: {
    type: Number,
    default: 1,
  },
  toggleGraphView: {
    type: Number,
    default: 1,
  },
});

const emit = defineEmits([
  "select",
  "selectDatasource",
  "refresh",
  "toggleAtlas",
  "updateThresholdValue",
  "toggleGraphView",
  "domainColors",
  "betweenness",
]);

const graphStore = useGraphDataStore();
const selected = ref(props.datasource);
const selectedEmbedding = ref(props.embeddingOptions[0].id);
const thresholdValue = ref(0.8);

function round2(value) {
  return Math.round(value * 100) / 100;
}

function handleGlobalKeydown(event) {
  const step = 0.01;

  if (event.key === "ArrowLeft") {
    event.preventDefault();
    thresholdValue.value = round2(Math.max(0, thresholdValue.value - step));
  }

  if (event.key === "ArrowRight") {
    event.preventDefault();
    thresholdValue.value = round2(Math.min(1, thresholdValue.value + step));
  }
  handleThresholdChange();
}

let atlasState = 1;

// Keep the local selected in sync with prop changes
watch(
  () => props.datasource,
  (newVal) => {
    selected.value = newVal;
  },
);

function onSelect(id) {
  emit("select", id);
}

function onDatasourceChange() {
  emit("selectDatasource", selected.value);
}
function onEmbeddingChange() {
  emit("selectEmbedding", selectedEmbedding.value);
}

function handleThresholdChange() {
  graphStore.thresholdValue = thresholdValue;
  emit("updateThresholdValue", thresholdValue);
}

function onRefresh() {
  emit("refresh");
}

function toggleGraphView() {
  emit("toggleGraphView");
}

onMounted(() => {
  window.addEventListener("keydown", handleGlobalKeydown);
});

onBeforeUnmount(() => {
  window.removeEventListener("keydown", handleGlobalKeydown);
});
</script>

<style scoped>
.side-menu {
  position: absolute;
  left: 16px;
  top: 32%;
  transform: translateY(-50%);
  background: rgba(20, 20, 20, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 10px;
  z-index: 10;
  backdrop-filter: blur(6px);
}

.menu-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.menu-list li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  color: white;
  transition: background 0.2s ease;
}

.menu-list li:hover {
  background: rgba(255, 255, 255, 0.12);
}

.menu-list li.active {
  background: rgba(255, 255, 255, 0.18);
}

.menu-icon {
  width: 24px;
  text-align: center;
}

/* Datasource styles */
.datasource {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
}

.datasource-title {
  color: #fff;
  font-weight: bold;
  margin-bottom: 8px;
}

/* Embedding styles */
.embedding {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
}

.refresh-button {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 10px;
  cursor: pointer;
  color: white;
  transition: background 0.2s ease;
}
.refresh-button:hover {
  background: rgba(255, 255, 255, 0.12);
}

.refresh-title {
  color: white;
  font-weight: bold;
}

.embedding-title {
  color: #fff;
  font-weight: bold;
  margin-bottom: 8px;
}

.threshold-slider {
  color: white;
}
.threshold-value {
  color: white;
}

select {
  width: 100%;
  padding: 8px;
  border-radius: 8px;
  border: none;
  outline: none;
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}
</style>
