<template>
  <div class="booklist-container">
    <!-- 搜索和新建按钮 -->
    <div class="action-bar">
      <div>
        <ElInput v-model="searchText" placeholder="搜索作品" class="search-box" :suffix-icon="Search" />
        <el-button type="primary" plain class="search-btn" @click="searchWorks">搜索</el-button>
      </div>
      <ElButton type="primary" class="create-btn" :icon="Plus" @click="createNewWork">
        新建作品
      </ElButton>
    </div>

    <!-- 作品列表 - 使用无限滚动 -->
    <div class="works-list" v-infinite-scroll="loadMore" :infinite-scroll-disabled="disabled"
      :infinite-scroll-distance="100">
      <div v-for="(work, index) in works" :key="index" class="work-item">
        <div class="work-preview">
          <img :src="work.surface_plot || '../../src/assets/book-covers.jpeg'" alt="作品封面" class="cover-image" />
        </div>
        <div class="work-info">
          <div class="work-title">{{ work.title }}</div>
          <div class="work-tags">
            <span v-for="(item, index) in work.tags.split(/[,，]/)" class="tag"
              :class="['primary', 'secondary', 'tertiary'][index % 3]">{{ item }}</span>
          </div>
          <el-tooltip effect="dark" :content="work.summary" placement="top" :disabled="work.summary.length <= 80">
            <div class="work-description">{{ work.summary.length > 80 ? work.summary.substring(0, 80) + '...' :
              work.summary }}</div>
          </el-tooltip>
          <div class="work-meta">
            <div><span>最近创作: </span>第{{ work.latest_chapter?.chapter_number || '*' }}章 (文章){{ work.latest_chapter?.title
              || '*' }}
            </div>
            <!-- <div><span>最近创作: </span>第{{ work.latest_chapter?.chapter_number || '*' }}章 (文章){{ work.latest_chapter?.title
              || '*' }} ｜ 第{{ work.latest_video?.chapter_number || '*' }}章 (视频){{ work.latest_video?.title || '*' }}
            </div> -->
            <!-- <div>{{ work.count_word_num }}字 | {{ work.stats }}</div> -->
          </div>
        </div>
        <div class="work-actions">
          <el-button type="danger" plain class="action-btn" @click="deleteWork(work.id)">删除</el-button>
          <el-button type="primary" plain class="action-btn" @click="outline(work.id)">创作</el-button>
          <!-- <el-button type="success" plain class="action-btn" @click="editWork(work.id)">作品创作</el-button> -->
        </div>
      </div>

      <!-- 加载提示 -->
      <div v-if="loading && works.length !== 0" class="loading-text">加载中...</div>
      <div v-if="noMore & works.length !== 0" class="loading-text">没有更多了～</div>

      <div v-if="works.length === 0 && !loading" class="empty-works">
        <img src="../assets/empty-folder.png" alt="空作品列表" class="empty-image" />
        <div class="empty-text">请创建您的首个作品～</div>
      </div>
    </div>
  </div>
</template>

<script>
import { Search, Plus } from '@element-plus/icons-vue'
import { ElButton, ElInput, ElLoading, ElMessage } from 'element-plus'
export default {
  name: 'BookList',
  components: {
    ElButton,
    ElInput
  },
  data() {
    return {
      searchText: '',
      works: [],
      currentPage: 1,
      totalPages: 1,
      loading: false,
      noMore: false
    }
  },
  computed: {
    disabled() {
      return this.loading || this.noMore
    }
  },
  setup() {
    return {
      Search,
      Plus
    }
  },
  async created() {
    await this.loadWorks()
    // 在进入页面的时候从localStorage删除当前作业 作品 ID「currentBookId」
    localStorage.removeItem('currentBookId');
  },
  methods: {
    async loadWorks() {
      if (this.loading) return

      this.loading = true
      const loadingInstance = ElLoading.service({
        lock: true,
        text: '加载中...',
        background: 'rgba(0, 0, 0, 0.7)'
      })

      try {
        const userId = JSON.parse(localStorage.getItem('userInfo')).userId
        const response = await this.$axios.get('/manages/getbooklist', {
          params: {
            query: this.searchText,
            userid: userId,
            page: this.currentPage
          },
          headers: {
            'X-Auth-Token': localStorage.getItem('token')
          }
        })

        if (response.data && response.data.booklist) {
          console.log(response.data)
          this.works = [...this.works, ...response.data.booklist]
          this.totalPages = response.data.all_page || 1

          if (this.currentPage >= this.totalPages) {
            this.noMore = true
          }
        }
      } catch (error) {
        if (error.response.status === 401) {
          this.$message.error('登录已过期，请重新登录');
          this.$router.push('/login');
          return;
        }
        console.error('获取书籍列表失败:', error)
        ElMessage.error('获取书籍列表失败，请稍后重试')
      } finally {
        loadingInstance.close()
        this.loading = false
      }
    },
    async loadMore() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++
        await this.loadWorks()
      }
    },
    searchWorks() {
      // 重置搜索条件
      this.works = []
      this.currentPage = 1
      this.noMore = false
      this.loadWorks()
    },
    createNewWork() {
      this.$router.push({
        path: '/workbench/createbook',
        query: {
          actiontab: 'info'
        }
      })
    },
    outline(id) {
      // 在进入页面的时候从localStorage设置当前作业 作品 ID「currentBookId」
      localStorage.setItem('currentBookId', id)
      this.$router.push({
        path: '/workbench/createbook',
        query: {
          actiontab: 'newcreate'
        }
      })
      console.log('编辑作品:', id)
    },
    editWork(id) {
      // 在进入页面的时候从localStorage设置当前作业 作品 ID「currentBookId」
      localStorage.setItem('currentBookId', id)
      this.$router.push({
        path: '/workbench/createbook',
        query: {
          actiontab: 'newcreate'
        }
      })
      console.log('编辑作品:', id)
    },
    async deleteWork(id) {
      try {
        // 确认删除操作
        await this.$confirm('确定要删除该作品吗？删除后将无法恢复', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })

        // 调用删除接口
        const res = await this.$axios.delete('/manages/delbook', {
          headers: {
            'X-Auth-Token': localStorage.getItem('token')
          },
          data: {
            id: id
          }
        })

        if (res.data.message) {
          this.$message.success(res.data.message)
          // 删除成功后重置并重新加载列表
          this.works = []
          this.currentPage = 1
          this.noMore = false
          await this.loadWorks()
        }
      } catch (error) {
        if (error === 'cancel') {
          // 用户取消删除
          return
        }
        if (error.response) {
          if (error.response.status === 401) {
            this.$message.error('登录已过期，请重新登录')
            this.$router.push('/login')
          } else {
            this.$message.error(error.response.data.error || '删除失败')
          }
        } else {
          this.$message.error('网络错误，请稍后重试')
        }
        console.error('删除失败:', error)
      }
    },
  }
}
</script>

<style scoped>
/* 保持原有样式不变，只添加新的加载提示样式 */
.loading-text {
  text-align: center;
  padding: 10px;
  color: #999;
  font-size: 14px;
}

/* 其他原有样式保持不变 */
.el-button--danger.is-link,
.el-button--danger.is-plain,
.el-button--danger.is-text {
  --el-button-bg-color: #ffffff;
}

.booklist-container {
  width: 100%;
  height: calc(100vh - 50px);
}

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

.search-btn,
.create-btn {
  height: 38px;
}

.works-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
  scrollbar-width: thin;
  scrollbar-color: #c0c4cc #f5f7fa;
  padding-right: 5px;
}

.empty-works {
  margin-top: 10vh;
  height: 50vh;
  width: 100%;
}

.empty-image {
  height: 400px;
  width: 400px;
  display: block;
  margin: 0 auto;
}

.empty-text {
  margin: 0 auto;
  text-align: center;
  font-size: 18px;
  color: #909399;
  margin-top: 20px;
}

.works-list::-webkit-scrollbar {
  width: 4px;
}

.works-list::-webkit-scrollbar-track {
  background: #f5f7fa;
  border-radius: 10px;
}

.works-list::-webkit-scrollbar-thumb {
  background-color: #c0c4cc;
  border-radius: 10px;
  border: 1px solid #f5f7fa;
}

.works-list::-webkit-scrollbar-thumb:hover {
  background-color: #eff4ff;
}

.work-item {
  display: flex;
  background-color: #fff;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  border: 1px #f5f7fa solid;
}

.work-preview {
  width: 120px;
  height: 150px;
  margin-right: 20px;
  overflow: hidden;
  border-radius: 4px;
}

.cover-image {
  width: 100%;
  height: 100%;
  object-fit: fill;
}

.work-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.work-title {
  font-size: 18px;
  font-weight: bold;
  margin-bottom: 10px;
}

.work-tags {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.tag {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.tag.primary {
  background-color: #e6f7ff;
  color: #1890ff;
}

.tag.secondary {
  background-color: #f6ffed;
  color: #52c41a;
}

.tag.tertiary {
  background-color: #fff7e6;
  color: #fa8c16;
}

.work-description {
  color: #666;
  font-size: 14px;
  margin-bottom: 10px;
  line-height: 1.5;
}

.work-meta {
  color: #999;
  font-size: 12px;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.work-actions {
  display: inline-block;
  flex-direction: column;
  gap: 10px;
  margin-left: 20px;
}

.action-btn {
  width: 60px;
  height: 30px;
  margin-top: 5px;
}

:deep(.el-button>span) {
  font-size: 12px;
}

@media (max-width: 768px) {
  .search-box {
    width: 200px;
  }

  .work-item {
    flex-direction: column;
  }

  .work-preview {
    width: 100%;
    height: 200px;
    margin-right: 0;
    margin-bottom: 15px;
  }

  .work-actions {
    flex-direction: row;
    margin-left: 0;
    margin-top: 15px;
  }
}
</style>