import { DirectedGraph } from "graphology";
import { defineStore } from "pinia";
import { ref, computed } from "vue";

class ColorState {
  private nodeStates = [
    "default",
    "selected",
    "domain",
    "component",
    "neighbor",
  ];

  public node: Record<string, boolean> = {
    default: true,
    selected: false,
    domain: false,
    component: false,
    neighbor: false,
  };

  constructor() {
    return;
  }

  private allOtherNodeStatesFalse(stateKey: string): boolean {
    // Return true iff all other states are false
    let result = false;
    this.nodeStates.forEach((key) => {
      if (key === stateKey) return;
      result = result || this.node[key];
    });
    return !result;
  }

  private exactlyOneOtherNodeStateTrue(stateKey: string): boolean {
    // Return true iff exactly one other state is true
    // For each other state, check if all other states are false
    // At least one is true
    if (this.allOtherNodeStatesFalse(stateKey)) return false;
    let result = true;
    let state = 0;
    this.nodeStates.forEach((key) => {
      if (key === stateKey) return;
      if (this.node[key]) state += 1;
      if (state === 2) result = false;
    });
    return result;
  }

  private setAllOtherNodeStatesFalse(stateKey: string) {
    this.nodeStates.forEach((key) => {
      if (key === stateKey) return;
      this.node[key] = false;
    });
  }

  private enforceRules(stateKey: string, stateValue: boolean) {
    // Enforce: Exactly one state is active at one time
    if (!this.allOtherNodeStatesFalse(stateKey)) {
      this.setAllOtherNodeStatesFalse(stateKey);
    }
  }

  setNodeState(stateKey: string, stateValue: boolean) {
    this.node[stateKey] = stateValue;
    this.enforceRules(stateKey, stateValue);
  }
}

type NodeId = string;

export const useGraphDataStore = defineStore("graphData", () => {
  // ─────────────────────────────
  // STATE
  // ─────────────────────────────

  const nodes = ref<Record<NodeId, any>>({});
  const openedTexts = ref<Record<NodeId, boolean>>({});
  const selectedNode = ref<NodeId>("");
  const outComponentGraph = ref<DirectedGraph | undefined>(undefined);
  const thresholdValue = ref<number>(1);
  const graphPopulated = ref(false);
  const colorHighlightState = {
    node: {
      default: true,
      selected: false,
      domain: false,
      component: false,
      neighbor: false,
    },
    edge: {
      default: true,
      selected: false,
      neighbor: false,
      component: false,
      outComponent: false,
    },
  };

  // ─────────────────────────────
  // GETTERS (computed)
  // ─────────────────────────────

  const hasSelection = computed(() => selectedNode.value !== null);

  const selectedNodeData = computed(() => {
    if (!selectedNode.value) return null;
    return nodes.value[selectedNode.value] ?? null;
  });

  // ─────────────────────────────
  // ACTIONS
  // ─────────────────────────────

  function setNodes(newNodes: Record<NodeId, any>) {
    nodes.value = newNodes;
  }

  function selectNode(id: NodeId) {
    selectedNode.value = id;
  }

  function toggleText(id: NodeId, open: boolean = true) {
    if (open) {
      openedTexts.value[id] = true;
    } else {
      delete openedTexts.value[id];
    }
  }

  function isTextOpen(id: NodeId) {
    return !!openedTexts.value[id];
  }

  function clear() {
    nodes.value = {};
    openedTexts.value = {};
    selectedNode.value = null;
  }

  function requireAllOtherNodeStates(stateKey) {
    colorHighlightState.node;
  }
  function setNodeColorState(stateKey: string, stateValue: boolean) {
    colorHighlightState.node[stateKey] = stateValue;
    // After change we require the stict rules of the states
    // The wanted behaviour is that if default=true, then all others should be false
    // Also, if any of the others=true, default should be false
    colorHighlightState.node.default =
      colorHighlightState.node.default ||
      !(
        colorHighlightState.node.selected &&
        colorHighlightState.node.component &&
        colorHighlightState.node.domain &&
        colorHighlightState.node.neighbor &&
        colorHighlightState.node.selected
      );
  }

  // ─────────────────────────────
  // EXPOSE
  // ─────────────────────────────

  return {
    // state
    nodes,
    openedTexts,
    selectedNode,
    outComponentGraph,
    thresholdValue,
    graphPopulated,
    colorHighlightState,

    // getters
    hasSelection,
    selectedNodeData,

    // actions
    setNodes,
    selectNode,
    toggleText,
    isTextOpen,
    clear,
  };
});
