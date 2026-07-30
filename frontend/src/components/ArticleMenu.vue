<template>
  <aside class="article-menu">
    <div class="article-modal" v-for="node in connectedNodes">
      <div :key="node.key" :ref="(el) => setItemRef(el, node.key)">
        <span class="article-domain">{{ node?.attributes?.domain }}</span>
        <h2
          class="selected-article"
          @click="toggleText(node.key)"
          v-if="node.key == graphStore.selectedNode"
        >
          {{ node?.attributes?.title }}
        </h2>
        <h2
          class="temporal-selected-article"
          @click="toggleText(node.key)"
          v-else-if="node.key == temporalSelectedNode.node"
        >
          {{ node?.attributes?.title }}
        </h2>
        <h2 @click="toggleText(node.key)" v-else>
          {{ node?.attributes?.title }}
        </h2>
        <div v-if="openedTexts[node.key]">
          <h3>Index: {{ node.key }}</h3>
          <HighlightedText
            :text="node?.attributes?.text"
            :highlights="node?.attributes?.important_words"
          />
        </div>
        <span class="article-date">{{ node?.attributes?.published_time }}</span>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from "vue";
import HighlightedText from "./HighlightedText.vue";
import { storeToRefs } from "pinia";
import { useGraphDataStore } from "@/stores/graph.store";

const props = defineProps({
  connectedNodes: {
    type: Array,
    required: true,
    default: [],
  },
  selectedNode: {
    type: undefined,
    required: true,
    default: {},
  },
  selectedEdgeArticles: {
    type: undefined,
    required: true,
    default: {},
  },
  temporalSelectedNode: {
    type: undefined,
    required: false,
    default: {},
  },
});

const graphStore = useGraphDataStore();
const emit = defineEmits(["select", "selectDatasource", "refresh"]);

const selected = ref();
const openedTexts = ref({});
const itemRefs = ref<Record<string, HTMLElement>>({});
const { selectedNode } = storeToRefs(graphStore);

function setItemRef(el: HTMLElement | null, key: string) {
  if (el) {
    itemRefs.value[key] = el;
  }
}

// Keep the local selected in sync with prop changes
// watch(
//   () => props.selectedNode,
//   (newVal) => {
//     showNodeArticles(newVal);
//   },
// );

watch(
  () => props.connectedNodes,
  (newVal) => {
    props.connectedNodes.value = newVal;
    processListedArticles();
  },
);

watch(selectedNode, async (newKey) => {
  await nextTick(); // wait for DOM update

  const el = itemRefs.value[newKey];
  if (el) {
    el.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });
  }
});
// watch(
//   () => props.selectedNode,
//   (newVal) => {
//     selectedNode.value = newVal;
//   },
// );

// watch(
//   () => props.showEdgeArticles,
//   (newVal) => {
//     console.log("Edge selected");
//     console.log(props.selectedEdgeArticles);
//     if (props.selectedEdgeArticles) {
//       showEdgeArticles(newVal);
//     } else {
//       showNodeArticles(newVal);
//     }
//   },
// );

function toggleText(key) {
  if (key in openedTexts.value) {
    openedTexts.value[key] = 1 - openedTexts.value[key];
    return;
  }
  openedTexts.value[key] = 1;
}

function onSelect(id) {
  emit("select", id);
}

function onDatasourceChange() {
  emit("selectDatasource", selected.value);
}

function showNodeArticles(newVal) {
  openedTexts.value = Object.fromEntries(newVal.map((n) => [n.key, false]));
}

function showEdgeArticles(newVal) {
  console.log(connectedNodes.value);
  connectedNodes.value = newVal;
  console.log(connectedNodes.value);
}

function processListedArticles() {
  console.log("Sorting #: " + props.connectedNodes.length);
  if (
    !props.connectedNodes.map((n) => n.key).includes(props.selectedNode.key)
  ) {
    props.connectedNodes.push(props.selectedNode);
  }
  props.connectedNodes = props.connectedNodes.sort(
    (n1, n2) => n1.attributes.published_time <= n2.attributes.published_time,
  );
}
</script>

<style scoped>
.article-menu {
  position: fixed;
  bottom: 15px;
  /* transform: translateY(-50%); */
  background: rgba(20, 20, 20, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 10px;
  z-index: 10;
  background: rgba(20, 20, 20, 0.75);
  backdrop-filter: blur(6px);
  color: white;
  overflow-y: auto;
  height: 35%;
  width: 75%;
}

.article-modal {
  background: rgba(20, 20, 20, 0.75);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  padding: 5px;
  margin: 10px;
  z-index: 10;
  /* backdrop-filter: blur(6px); */
  color: white;
}

.article-date {
  position: relative;
}

.article-domain {
  position: relative;
}

.selected-article {
  color: green;
}

.temporal-selected-article {
  color: pink;
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
