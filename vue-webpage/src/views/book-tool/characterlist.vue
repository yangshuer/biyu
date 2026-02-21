<template>
  <div>
    <div class="content">
      <!-- 顶部搜索区域 -->
      <div class="search-area">
        <div class="search-group">
          <ElInput v-model="searchText" placeholder="搜索角色" class="search-input" :suffix-icon="Search" />
          <el-button @click="searchCharacters" type="primary" plain class="search-button">
            搜索
          </el-button>
        </div>
        <el-button type="primary" :icon="Plus" class="new-button" @click="tocharaterinfo">
          新建角色
        </el-button>
      </div>

      <!-- 角色列表 -->
      <div class="character-list" v-infinite-scroll="loadMore" :infinite-scroll-disabled="disabled"
        :infinite-scroll-distance="100">
        <div v-for="character in characters" :key="character.id" class="character-card">
          <div class="character-content">
            <div class="avatar-container">
              <img :src="character.avatar || '../../src/assets/baseheadimg.png'" :alt="character.name" class="avatar" />
            </div>
            <div class="character-info">
              <div class="info-grid">
                <div class="info-item">
                  <span class="info-label">姓名:</span>
                  <span>{{ character.name }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">性别:</span>
                  <span>{{ character.gender }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">年龄:</span>
                  <span>{{ character.age }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">职业:</span>
                  <span>{{ character.occupation }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">种族:</span>
                  <span>{{ character.race }}</span>
                </div>
              </div>
              <div class="details">
                <div class="detail-item">
                  <span class="detail-label">性格:</span>
                  <span class="detail-text">{{ character.personality }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">背景:</span>
                  <span class="detail-text">{{ character.background }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">长相:</span>
                  <span class="detail-text">{{ character.appearance }}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">体格:</span>
                  <span class="detail-text">{{ character.physique }}</span>
                </div>
              </div>
            </div>
            <div class="action-buttons">
              <el-button type="danger" plain class="action-button" @click="handleDelete(character.id)">
                删除
              </el-button>
              <el-button type="primary" class="action-button" @click="handleEdit(character.id)">
                编辑
              </el-button>
            </div>
          </div>
        </div>
        <!-- 加载提示 -->
        <div v-if="loading && characters.length !== 0" class="loading-text">加载中...</div>
        <div v-if="noMore && characters.length !== 0" class="loading-text">没有更多了～</div>
      </div>
      <div v-if="characters.length === 0" class="empty-state">
        <img src="@/assets/empty-folder.png" alt="空列表" class="empty-image">
        <p class="empty-text">暂无角色数据</p>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { Search, Plus } from '@element-plus/icons-vue'
import { defineComponent } from 'vue';
import { ElButton, ElInput } from 'element-plus'
import { th } from 'element-plus/es/locale';
export default defineComponent({
  components: {
    ElButton,
    ElInput
  },
  setup() {
    return {
      Search,
      Plus
    }
  },
  data() {
    return {
      searchText: '',
      characters: [
        // 可以添加更多角色数据
      ],
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
  async created() {
    await this.loadCharacters()
  },
  methods: {
    searchCharacters() {
      this.searchText = this.searchText.trim()
      this.characters = []
      this.loadCharacters()
    },
    async loadCharacters() {
      if (this.loading) return
      const loadingInstance = this.$loading({
        lock: true,
        text: '加载中...',
        background: 'rgba(0, 0, 0, 0.7)',
      })
      try {
        const bookId = localStorage.getItem('currentBookId')
        if (!bookId) {
          this.$message.error('管理角色关系请先保存作品信息～')
          console.log('没有保存作品，未获取到当前书籍ID')
          return
        }

        const response = await this.$axios.get('/manages/book_characters', {
          params: {
            book_id: bookId,
            query: this.searchText,
            page: this.current_page
          },
          headers: {
            'X-Auth-Token': localStorage.getItem('token')
          }
        })
        if (response.data && response.data.characters) {
          this.characters = [...this.characters, ...response.data.characters.map(char => ({
            id: char.id,
            name: char.name,
            gender: char.gender,
            personality: char.personality,
            background: char.background,
            age: char.age,
            occupation: char.occupation,
            appearance: char.appearance,
            physique: char.physique,
            avatar: char.face_image,
            race: char.race
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
          console.error('获取角色列表失败:', error)
          this.$message.error('获取角色列表失败')
        }
      } finally {
        loadingInstance.close()
      }
    },
    loadMore() {
      if (this.current_page < this.all_page) {
        this.current_page++
        this.loadCharacters()
      }
    },
    async handleDelete(id: number) {
      console.log('删除:', id)
      try {
        await this.$confirm('确定要删除该角色吗？删除后将无法恢复', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        });
        const response = await this.$axios.delete(`/manages/delcharacters`, {
          data: {
            id: id,
            book_id: localStorage.getItem('currentBookId')
          },
          headers: {
            'X-Auth-Token': localStorage.getItem('token')
          }
        });
        if (response.status === 200) {
          this.$message.success('删除成功');
          this.characters = this.characters.filter(char => char.id !== id);
        }
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除角色失败:', error);
          this.$message.error('删除角色失败');
        }
      }
    },
    handleEdit(id: number) {
      // 跳转到角色信息页面-编辑角色
      this.$router.push({
        path: '/workbench/createbook/character',
        query: this.characters.find(char => char.id === id)
      });
    },
    tocharaterinfo() {
      // 跳转到角色信息页面-新建角色
      this.$router.push('/workbench/createbook/character');
    }
  }
});
</script>

<style scoped>
.loading-text {
  text-align: center;
  padding: 10px;
  color: #999;
  font-size: 14px;
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

.character-list {
  /* margin-top: 50px; */
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 16px;

}

.character-card {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  border: #f5f7fa 1px solid;
  padding: 16px;
}

.character-content {
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

.character-info {
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
</style>