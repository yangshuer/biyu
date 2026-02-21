<template>
  <div>
    <!-- 搜索和新建按钮 -->
    <div class="action-bar">
      <div>
        <ElInput v-model="searchText" placeholder="搜索作品" class="search-box" :suffix-icon="Search" />
        <el-button type="primary" plain class="create-btn">搜索</el-button>
      </div>
      <ElButton type="primary" class="create-btn" :icon="Plus" @click="createNewWork">
        新建
      </ElButton>
    </div>
    <div style="display: flex; justify-content: center; align-items: center; height: 50%; min-height: 400px;">
      <img src="../assets/empty-folder.png" style="height: 300px; width: 300px;">
    </div>
    <div style="display: flex; justify-content: center;  height: 50%; min-height: 400px;">
      <p style="color: darkgray;">您还没有创建任何作品～</p>
    </div>
  </div>
</template>

<script>
import { Search, Plus } from '@element-plus/icons-vue'
import {
  ElButton,
  ElInput
} from 'element-plus'
export default {
  data() {
    return {
      searchText: ''
    }
  },
  methods: {
    createNewWork() {
      this.$router.push({
        path: '/workbench/createbook',
        query: {
          actiontab: 'info'  // 这里可以设置默认的tab值
        }
      })
    }
  },
  setup() {
    return {
      Search,
      Plus
    }
  },
}
</script>

<style scoped>
.action-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.search-box {
  width: 300px;
  height: 38px;
  margin: 0 10px 0 0;
}

.create-btn {
  height: 38px;
}

/* 内容区域样式 */
.content-area {
  background-color: #fff;
  border-radius: 8px;
  height: calc(100% - 90px);
  padding: 20px;
}

.notification-dot {
  font-size: 12px;
  color: red;
  font-weight: bold;
}
</style>