<template>
  <div class="empty-page">
    <div class="empty-content">
      <p>功能还在开发中，敬请期待～</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ZeroPage',
  data() {
    return {}
  },
  methods: {},
  mounted() {}
}
</script>

<style scoped>
.empty-page {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.empty-content {
  text-align: center;
  color: #999;
  font-size: 16px;
}
</style>
