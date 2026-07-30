<template>
  <div
    v-if="visible"
    class="hover-box"
    :style="{
      left: `${x}px`,
      top: `${y}px`,
    }"
  >
    <strong>{{ title }}</strong>
    <div class="content">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  visible: boolean;
  x: number;
  y: number;
  title?: string;
}>();
</script>
<style scoped>
.hover-box {
  position: absolute;
  pointer-events: none; /* important for hover tooltips */
  background: rgba(250, 250, 250, 0.75);
  backdrop-filter: blur(6px);
  border: 1px solid #ddd;
  border-radius: 3px;
  padding: 6px 20px;
  font-size: 18px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translate(-50%, -110%);
  white-space: nowrap;
  z-index: 10;
}

.content {
  margin-top: 4px;
  color: #555;
}
</style>
