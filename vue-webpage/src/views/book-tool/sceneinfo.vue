<template>
  <div class="container">
    <header class="header">
      <div class="header-content">
        <div class="header-left">
          <el-icon class="back-icon" @click="goBack">
            <ArrowLeft />
          </el-icon>
        </div>
        <h1 class="title">编辑场景</h1>
        <!-- <el-button type="primary"  class="confirm-btn">确认</el-button> -->
        <el-button type="success" @click="savescence" plain :icon='Check' text style="font-size: 1.25rem;" circle />
      </div>
    </header>
    <main class="main-content">
      <!-- <h3 class="relation-title" style="margin-bottom: 15px;">角色信息</h3> -->
      <div>
        <div class="card-body">
          <div class="avatar-section">
            <el-image :src="form.avatar" class="avatar-img" alt="场景图片" :preview-src-list="[form.avatar]"
              :zoom-rate="1.2" :max-scale="7" :min-scale="0.2" fit="cover" />
            <el-button @click="createscene" type="primary" class="avatar-btn">AI 生成场景</el-button>
          </div>
          <div class="form-section">
            <div class="textarea-section">
              <div class="textarea-item">
                <label class="form-label">地点</label>
                <el-input v-model="form.location" type="textarea" :rows="4" placeholder="请描述场景地点的名称，例如：后山思过崖" />
              </div>
              <div class="textarea-item">
                <label class="form-label">环境</label>
                <el-input v-model="form.environment" type="textarea" :rows="4"
                  placeholder="请描述场景的环境状态，例如：巍峨的山崖中部有一处平台，平台上有一处茅草屋，仅有一条小道通往上下，平台侧面有一处瀑布。" />
              </div>
              <div class="textarea-item">
                <label class="form-label">用途</label>
                <el-input v-model="form.purpose" type="textarea" :rows="4"
                  placeholder="请描述场景地点的用途，例如：为了惩罚门派中犯了重大错误的人，相当于禁闭室。" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { ArrowLeft, Plus, Check } from '@element-plus/icons-vue';
// import baseimg from 
export default defineComponent({
  name: 'CharacterInfo',
  components: {
    ArrowLeft,
    Plus,
    Check,
  },
  setup() {
    return {
      ArrowLeft,
      Plus,
      Check,
    }
  },
  data() {
    return {
      prompt: '',
      form: {
        id: 1,
        location: '',
        environment: '',
        purpose: '',
        avatar: '',
      },
    }
  },
  methods: {
    goBack() {
      // 返回上一页
      this.$router.push('/workbench/createbook/scenelist');
    },
    async createscene() {
      // 调用AI生成场景
      const requiredFields = ['location', 'environment', 'purpose'];
      const missingFields = requiredFields.filter(field => !this.form[field]?.trim());
      this.form.location = this.form.location?.trim() || '';
      this.form.environment = this.form.environment?.trim() || '';
      this.form.purpose = this.form.purpose?.trim() || '';
      if (missingFields.length > 0) {
        this.$message.error(`请填写完整场景信息: ${missingFields.map(f => {
          if (f === 'location') return '地点';
          if (f === 'environment') return '环境';
          if (f === 'purpose') return '用途';
          return f;
        }).join(', ')}`);
        return;
      }
      // 添加加载状态
      const loadingInstance = this.$loading({
        text: 'AI正在生成场景...',
        background: 'rgba(0, 0, 0, 0.7)'
      });
      // 构建请求参数
      const params = {
        userid: JSON.parse(localStorage.getItem('userInfo'))?.userId,
        bookid: localStorage.getItem('currentBookId'),
        sceneid: this.$route.query.id || null,
        sceneinfo: {
          location: this.form.location,
          environment: this.form.environment,
          purpose: this.form.purpose
        }
      };

      try {
        const res = await this.$axios.post('/agents/create-scene', params, {
          headers: {
            'X-Auth-Token': localStorage.getItem('token')
          }
        });

        if (res.data.scene) {
          this.form.avatar = res.data.scene + `?t=${Date.now()}`;
          this.$message.success('场景图片生成成功');
        }
      } catch (error) {
        if (error.response && error.response.status === 401) {
          this.$message.error('登录已过期，请重新登录');
          this.$router.push('/login');
        } else {
          console.error('生成场景图片失败:', error);
          this.$message.error(error.response?.data?.error || '生成场景图片失败');
        }
      } finally {
        this.$loading().close();
      }
    },
    async savescence() {
      // 保存场景信息
      const bookId = localStorage.getItem('currentBookId');
      if (!bookId) {
        this.$message.error('请先保存作品信息');
        return;
      }

      const params = {
        id: this.$route.query.id || null,
        book_id: bookId,
        space_name: this.form.location?.trim() || '',
        description: this.form.environment?.trim() || '',
        image: this.form.avatar,
        space_use: this.form.purpose?.trim() || ''
      };

      this.form = {
        id: params.id,
        location: params.space_name,
        environment: params.description,
        purpose: params.space_use,
        avatar: params.image,
      }

      // 校验必填字段
      const requiredFields = ['space_name', 'description', 'space_use'];
      const missingFields = requiredFields.filter(field => !params[field]);

      if (missingFields.length > 0) {
        this.$message.error(`请填写完整场景信息: ${missingFields.map(f => {
          if (f === 'space_name') return '地点';
          if (f === 'description') return '环境';
          if (f === 'space_use') return '用途';
          return f;
        }).join(', ')}`);
        return;
      }

      try {
        const res = await this.$axios.post('/manages/savesescene', params, {
          headers: {
            'X-Auth-Token': localStorage.getItem('token')
          }
        });

        if (res.data.message) {
          this.$message.success(res.data.message);
          // 更新路由中的场景ID（如果是新增）
          if (!this.$route.query.id && res.data.id) {
            this.$router.replace({
              query: { ...this.$route.query, id: res.data.id }
            });
          }
        }
      } catch (error) {
        if (error.response && error.response.status === 401) {
          this.$message.error('登录已过期，请重新登录');
          this.$router.push('/login');
        } else {
          console.error('保存场景失败:', error);
          this.$message.error(error.response?.data?.error || '保存场景失败');
        }
      }
      // 返回场景列表页
      this.$router.push('/workbench/createbook/scenelist');
    },
    deleteScence(row: any) {
      // 删除场景
    }
  },
  async mounted() {
    // 获取传参信息能够获取到则是编辑，获取不到则是新增
    const scene = this.$route.query;
    console.log(scene)
    if (scene) {
      // 编辑模式，获取场景数据
      this.form = {
        id: scene.id,
        location: scene.location,
        environment: scene.environment,
        purpose: scene.purpose,
        avatar: scene.avatar || '/src/assets/basescene.png'
      };
    }
  }
});
</script>

<style scoped>
.el-textarea :deep(.el-textarea__inner) {
  overflow-y: auto !important;
}

.relation-table {
  width: 100%;
}

.relation-table :deep(.el-table__header th .cell) {
  font-weight: bold;
  color: #4b5563;
}

.container {
  min-height: 100px;
  max-width: 1400px;
  margin: 0 auto;
  /* background-color: #f9fafb; */
}

.header {
  background-color: white;
  /* box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); */
  padding: 0;
  margin-left: 15px;
  /* margin-left: calc((100% - 80rem) / 2); */
  padding-bottom: 15px;
  position: sticky;
  top: 0;
  z-index: 1000;
  border-bottom: #e7e7e7 1px solid;
  max-width: 1400px;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  /* padding: 1rem; */
  /* max-width: 80rem; */
  margin: 0 auto;
}

.header-left {
  display: flex;
  align-items: center;
}

.back-icon {
  color: #4b5563;
  cursor: pointer;
  font-size: 1.25rem;
  height: 32px;
  width: 32px;

  &:hover {
    background-color: #F7F9FB;
    border-radius: 50%;
  }
}

.title {
  font-size: 14px;
  font-weight: 500;
  color: #111827;
}

.confirm-btn {
  border-radius: 9999px;
  white-space: nowrap;
}

.main-content {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.5rem 1rem;
}

.card-body {
  display: flex;
  gap: 2rem;
}

.avatar-section {
  position: relative;
  width: 12rem;
  height: 12rem;
  flex-shrink: 0;
}

.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 5px;
  object-fit: cover;
}

.avatar-btn {
  border-radius: 9999px;
  white-space: nowrap;
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  bottom: -40px;
}

.form-section {
  flex: 1;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.form-grid-double {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.form-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.textarea-section {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  /* margin-top: 2rem; */
}

.textarea-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.relation-section {
  margin-top: 2rem;
}

.relation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.relation-title {
  font-size: 1.125rem;
  font-weight: 500;
  color: #111827;
}

.add-btn {
  border-radius: 9999px;
  white-space: nowrap;
}

.plus-icon {
  margin-right: 0.25rem;
}

.relation-table {
  width: 100%;
}

.action-btn {
  border-radius: 9999px;
  white-space: nowrap;
  padding: 0;
}

.edit-btn {
  margin-right: 0.5rem;
}

.el-input :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #e5e7eb;
}

.el-input :deep(.el-input__wrapper):hover {
  box-shadow: 0 0 0 1px #d1d5db;
}

.el-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px #e6f4ff, 0 0 0 1px #1677ff;
}

.el-select :deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #e5e7eb;
}

.el-select :deep(.el-input__wrapper):hover {
  box-shadow: 0 0 0 1px #d1d5db;
}

.el-select :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px #e6f4ff, 0 0 0 1px #1677ff;
}
</style>