<template>
  <div>
    <div class="content">
      <!-- 顶部搜索区域 -->
      <div class="search-area">
        <div class="search-group">
          <ElInput v-model="searchText" placeholder="搜索场景" class="search-input" :suffix-icon="Search" />
          <el-button @click="searchScenes" type="primary" plain class="search-button"> 搜索 </el-button>
        </div>
        <el-button type="primary" :icon="Plus" class="new-button" @click="tocharaterinfo">
          新建场景
        </el-button>
      </div>

      <!-- 角色列表 -->
      <div class="scene-list" v-infinite-scroll="loadMore" :infinite-scroll-disabled="disabled"
        :infinite-scroll-distance="100">
        <div v-for="scene in scenes" :key="scene.id" class="scene-card">
          <div class="scene-content">
            <div class="avatar-container">
              <img :src="scene.avatar" class="avatar" />
            </div>
            <div class="scene-info">
              <div class="details">
                <div class="detail-item">
                  <span class="detail-label">地点:</span>
                  <span class="detail-text">{{ scene.location }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">环境:</span>
                  <span class="detail-text">{{ scene.environment }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">用途:</span>
                  <span class="detail-text">{{ scene.purpose }}</span>
                </div>
              </div>
            </div>
            <div class="action-buttons">
              <el-button type="danger" plain class="action-button" @click="handleDelete(scene.id)">
                删除
              </el-button>
              <el-button type="primary" class="action-button" @click="handleEdit(scene.id)">
                编辑
              </el-button>
            </div>
          </div>
        </div>
        <!-- 添加加载提示 -->
        <div v-if="loading && scenes.length !== 0" class="loading-text">加载中...</div>
        <div v-if="noMore && scenes.length !== 0" class="loading-text">没有更多了～</div>
      </div>
      <!-- 空状态 -->
      <div v-if="scenes.length === 0" class="empty-state">
        <img src="@/assets/empty-folder.png" alt="空列表" class="empty-image">
        <p class="empty-text">暂无场景数据</p>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { Search, Plus } from '@element-plus/icons-vue'
import { defineComponent } from 'vue'
import { ElButton, ElInput } from 'element-plus'
export default defineComponent({
  components: {
    ElButton,
    ElInput,
  },
  setup() {
    return {
      Search,
      Plus,
    }
  },
  data() {
    return {
      searchText: '',
      scenes: [
        // {
        //   id: 1,
        //   location:
        //     '阿拉深刻的积分啦开始的积分了卡技术来的快解放啦开始觉得浪费空间阿莱克斯的积分啦看见了深刻的',
        //   environment:
        //     '11110岁阿里大熟风暴阿莱克斯的积分啦开始短短发了卡拉卡上的积分啦看见收到了饭就来啦但是快解放了',
        //   purpose:
        //     '10岁阿里大熟风暴阿莱克斯的积分啦开始稍微发了卡拉卡上的积分啦看见收到了饭就来啦但是快解放了',
        //   avatar: '/src/assets/basescene.png',
        // },
        // 可以添加更多角色数据
      ] as scene[],
      all_page: null,
      current_page: 1,
      loading: false,
      noMore: false
    }
  },
  computed: {
    disabled() {
      return this.loading || this.noMore
    }
  },
  methods: {
    async handleDelete(id: number) {
      // 调接口删除场景
      // 确认删除操作
      await this.$confirm('确定要删除该场景吗？删除后将无法恢复', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      try {
        const bookId = localStorage.getItem('currentBookId')
        if (!bookId) {
          this.$message.error('删除场景请先保存作品信息～')
          return
        }

        await this.$axios.post('/manages/deletesescene', {
          id: id,
          book_id: bookId
        }, {
          headers: {
            'X-Auth-Token': localStorage.getItem('token')
          }
        })
        this.$message.success('删除场景成功')
      } catch (error) {
        if (error.response && error.response.status === 401) {
          this.$message.error('登录已过期，请重新登录')
          this.$router.push('/login')
        } else {
          console.error('删除场景失败:', error)
          this.$message.error('删除场景失败')
        }
      }

      this.scenes = this.scenes.filter((char) => char.id !== id)
    },
    handleEdit(id: number) {
      // 跳转到编辑场景页面并传递当前场景数据
      this.$router.push({
        path: '/workbench/createbook/scene',
        query: this.scenes.find(scene => scene.id === id)
      })
    },
    tocharaterinfo() {
      // 跳转到角色信息页面
      this.$router.push('/workbench/createbook/scene')
    },
    searchScenes() {
      this.searchText = this.searchText.trim()
      this.scenes = []
      this.current_page = 1
      this.noMore = false
      this.fetchScenes()
    },
    loadMore() {
      if (this.current_page < this.all_page) {
        this.current_page++
        this.fetchScenes()
      }
    },
    async fetchScenes() {
      if (this.loading) return
      const loadingInstance = this.$loading({
        lock: true,
        text: '加载中...',
        background: 'rgba(0, 0, 0, 0.7)',
      })
      try {
        const bookId = localStorage.getItem('currentBookId')
        if (!bookId) {
          this.$message.error('管理场景请先保存作品信息～')
          return
        }

        const response = await this.$axios.get('/manages/querysescene', {
          params: {
            book_id: bookId,
            query: this.searchText,
            page: this.current_page
          },
          headers: {
            'X-Auth-Token': localStorage.getItem('token')
          }
        })
        console.log(response.data) //打印当前书籍场景列表
        if (response.data && response.data.scenes) {
          this.scenes = [...this.scenes, ...response.data.scenes.map(scene => ({
            id: scene.id,
            location: scene.space_name,
            environment: scene.description,
            purpose: scene.space_use,
            avatar: scene.image || '/src/assets/basescene.png'
          }))]

          this.all_page = response.data.all_page
          if (this.current_page >= this.all_page) {
            this.noMore = true
          }
        }
      } catch (error) {
        if (error.response && error.response.status === 401) {
          this.$message.error('登录已过期，请重新登录')
          this.$router.push('/login')
        } else {
          console.error('获取场景列表失败:', error)
          this.$message.error('获取场景列表失败')
        }
      } finally {
        loadingInstance.close()
      }
    },
  },
  created() {
    // 这里可以添加调用API获取场景列表的逻辑
    this.fetchScenes()
  },
})

interface scene {
  id: number
  location: string
  environment: string
  purpose: string
  avatar: string
}
</script>

<style scoped>
.loading-text {
  text-align: center;
  padding: 10px;
  color: #999;
  font-size: 14px;
}

.content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 16px;
}

.search-area {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0;
  position: sticky;
  top: 0;
  background-color: white;
  z-index: 10;
  padding-bottom: 10px;
  /* box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); */
}

.search-group {
  display: flex;
  align-items: center;
  flex: 1;
  max-width: 36rem;
}

.search-input {
  border: #e7e7e7 1px solid;
  border-radius: 5px;
  height: 40px;
  width: 300px;

  &:focus-within {
    border-color: var(--el-color-primary);
  }
}

.search-button,
.new-button {
  height: 40px;
}

.action-button {
  border-radius: 8px;
  white-space: nowrap;
  width: 40px;
  margin: 0;
  height: 30px;
}

.search-button {
  margin-left: 8px;
  height: 40px;
}

.scene-list {
  /* margin-top: 50px; */
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.scene-card {
  /* environment-color: white; */
  border-radius: 8px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  border: #f5f7fa 1px solid;
  padding: 16px;
}

.scene-content {
  display: flex;
}

.avatar-container {
  width: 96px;
  height: 96px;
  flex-shrink: 0;
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.scene-info {
  flex: 1;
  margin-left: 16px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 16px;
  margin-bottom: 8px;
}

.info-item {
  display: flex;
  align-items: center;
}

.info-label {
  color: #6b7280;
  margin-right: 8px;
}

.details {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-item {
  display: flex;
}

.detail-label {
  color: #6b7280;
  margin-right: 8px;
  white-space: nowrap;
}

.detail-text {
  font-size: 14px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 8px;
  margin-left: 16px;
}

/* 覆盖Element Plus默认样式 */
.el-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
}

.el-input :deep(.el-input__inner) {
  height: 40px;
}

.el-input :deep(.el-input__prefix) {
  left: 12px;
}

.search-icon {
  color: #9ca3af;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}

.empty-image {
  width: 400px;
  height: 400px;
  margin-bottom: 20px;
}

.empty-text {
  color: #999;
  font-size: 16px;
}
</style>
