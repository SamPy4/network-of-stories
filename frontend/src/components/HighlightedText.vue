<template>
  <p v-html="highlightedText"></p>
</template>

<script>
export default {
  props: {
    text: String,
    highlights: Array,
  },
  computed: {
    highlightedText() {
      if (!this.highlights?.length) return this.text;

      // Escape regex characters in highlight words

      const scores = Object.fromEntries(this.highlights);

      const escaped = this.highlights
        .filter(Boolean)
        .map((word) => String(word[0]).replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));

      const regex = new RegExp(`\\b(${escaped.join("|")})\\b`, "gi");
      return this.text.replace(regex, (match, group1) => {
        return `<span title="${scores[group1.toLowerCase().trim()]}" class="highlight">${group1}</span>`;
      });
    },
  },
};
</script>
<style>
.highlight {
  background-color: blue;
  padding: 0 2px;
  border-radius: 3px;
}
</style>
