<template>
  <div class="container">
    <header class="header">
      <div class="header-content">
        <div class="header-left">
          <el-icon class="back-icon" @click="goBack">
            <ArrowLeft />
          </el-icon>
        </div>
        <h1 class="title">编辑角色</h1>
        <!-- <el-button type="primary"  class="confirm-btn">确认</el-button> -->
        <el-button type="success" @click="savecharacherinfo" plain :icon='Check' text style="font-size: 1.25rem;"
          circle />
      </div>
    </header>
    <main class="main-content">
      <h3 class="relation-title" style="margin-bottom: 15px;">角色信息</h3>
      <div>
        <div class="card-body">
          <div class="avatar-section">
            <el-image :src="form.avatarUrl || '../../src/assets/baseheadimg.png'" class="avatar-img" alt="角色头像"
              :preview-src-list="[form.avatarUrl || '../../src/assets/baseheadimg.png']" :initial-index="0"
              :zoom-rate="1.2" :max-scale="7" :min-scale="0.2" fit="cover" hide-on-click-modal />
            <el-button @click="createhead" type="primary" class="avatar-btn">AI 生成头像</el-button>
          </div>
          <div class="form-section">
            <div class="form-grid">
              <div class="form-item">
                <label class="form-label">姓名</label>
                <el-input v-model="form.name" placeholder="请输入姓名" />
              </div>
              <div class="form-item">
                <label class="form-label">性别</label>
                <el-select v-model="form.gender" placeholder="请选择性别">
                  <el-option label="男" value="male" />
                  <el-option label="女" value="female" />
                </el-select>
              </div>
              <div class="form-item">
                <label class="form-label">年龄</label>
                <el-input v-model="form.age" placeholder="请输入年龄" />
              </div>
              <div class="form-item">
                <label class="form-label">种族</label>
                <el-input v-model="form.race" placeholder="请输入种族" />
              </div>
              <div class="form-item">
                <label class="form-label">职业</label>
                <el-input v-model="form.occupation" placeholder="请输入职业" />
              </div>
            </div>
            <div class="form-grid-double">
              <div class="form-item">
                <label class="form-label">长相描述</label>
                <el-input v-model="form.appearance" placeholder="请描述角色长相特征" />
              </div>
              <div class="form-item">
                <label class="form-label">体型描述</label>
                <el-input v-model="form.physique" placeholder="请描述角色体型特征" />
              </div>
            </div>
          </div>
        </div>
        <div class="textarea-section">
          <div class="textarea-item">
            <label class="form-label">性格</label>
            <el-input v-model="form.personality" type="textarea" :rows="4" placeholder="请描述角色性格" />
          </div>
          <div class="textarea-item">
            <label class="form-label">背景</label>
            <el-input v-model="form.background" type="textarea" :rows="4" placeholder="请描述角色背景" />
          </div>
        </div>
        <div class="relation-section">
          <div class="relation-header">
            <h3 class="relation-title">角色关系</h3>
            <el-button type="primary" class="add-btn" @click="addRelation">
              <el-icon class="plus-icon">
                <Plus />
              </el-icon>添加关系
            </el-button>
          </div>
          <el-table :data="relations" class="relation-table">
            <el-table-column label="关联角色" prop="name" />
            <el-table-column :label="form.name == '' ? '关系' : '关系(「关联角色」是「' + form.name + '」的什么)'"
              prop="relationship" />
            <el-table-column label="操作" width="160">
              <template #default="scope">
                <el-button type="primary" text class="action-btn edit-btn" @click="editRelation(scope.row)">
                  编辑
                </el-button>
                <el-button type="danger" text class="action-btn delete-btn" @click="deleteRelation(scope.row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </main>
    <el-dialog v-model="dialogVisible" title="添加角色关系" width="30%">
      <el-form :model="relationForm" label-width="100px">
        <el-form-item label="关联角色">
          <el-select v-model="relationForm.name" filterable remote reserve-keyword placeholder="请搜索关联角色"
            :remote-method="searchCharacters" :loading="loading" @change="handleCharacterSelect">
            <el-option v-for="item in characterOptions" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="'关系'">
          <el-input v-model="relationForm.relationship" placeholder="请输入关系描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitRelation">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue';
import { ArrowLeft, Plus, Check } from '@element-plus/icons-vue';
import { data } from 'uview-ui/libs/mixin/mixin';
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
      form: {
        id: null,
        name: '',
        gender: '',
        race: '',
        age: '',
        occupation: '',
        appearance: '',
        physique: '',
        personality: '',
        background: '',
        avatarUrl: ''
      },
      relations: [
        // {
        //   name: '米老鼠',
        //   id: 1,
        //   relationship: '好友',
        // }
      ],
      dialogVisible: false,  // 新增对话框显示状态
      relationForm: {       // 新增关系表单数据
        name: '',
        id: null,
        relationship: ''
      },
      loading: false,
      characterOptions: [], // 存储搜索到的角色选项
      bookAllCharacter: []  //书籍全部角色list
    }
  },
  methods: {
    async createhead() {
      // 生成角色头像
      try {
        // 校验必填字段
        const requiredFields = ['gender', 'race', 'age', 'occupation', 'appearance', 'physique'];
        const missingFields = requiredFields.filter(field => !this.form[field]?.trim());

        if (missingFields.length > 0) {
          this.$message.error(`请先填写完整角色信息: ${missingFields.join(', ')}`);
          return;
        }

        // 准备请求参数
        const params = {
          userid: JSON.parse(localStorage.getItem('userInfo'))?.userId,
          bookid: localStorage.getItem('currentBookId'),
          charaterid: this.form.id || null,
          charaterinfo: {
            race: this.form.race.trim(),
            gender: this.form.gender === 'male' ? '男' : this.form.gender === '' ? '' : '女',
            age: this.form.age.trim(),
            appearance: this.form.appearance.trim(),
            physique: this.form.physique.trim(),
            occupation: this.form.occupation.trim()
          }
        };

        const loadingInstance = this.$loading({
          lock: true,
          text: 'AI正在生成头像...',
          background: 'rgba(0, 0, 0, 0.7)'
        });

        // 调用生成头像接口
        const response = await this.$axios.post('/agents/create-charater-head', params, {
          headers: {
            'X-Auth-Token': localStorage.getItem('token')
          },
          timeout: 60000 // 60秒超时
        });

        if (response.data?.charater_head) {
          // console.log(this.form.avatarUrl,response.data.charater_head)
          this.form.avatarUrl = response.data.charater_head + `?t=${Date.now()}`;
          this.$message.success('头像生成成功');
        } else {
          this.$message.error('头像生成失败');
        }
      } catch (error) {
        console.error('生成头像失败:', error);
        if (error.code === 'ECONNABORTED') {
          this.$message.error('头像生成超时，请重试');
        } else if (error.response?.status === 401) {
          this.$message.error('登录已过期，请重新登录');
          this.$router.push('/login');
        } else {
          this.$message.error('头像生成失败');
        }
      } finally {
        this.$loading().close();
      }
    },
    handleCharacterSelect(characterId) {
      const selectedCharacter = this.characterOptions.find(item => item.id === characterId);
      if (selectedCharacter) {
        this.relationForm.id = characterId;
        this.relationForm.name = selectedCharacter.name;
      }
    },
    async searchCharacters(query) {
      if (query) {
        this.loading = true;
        try {
          this.characterOptions = this.bookAllCharacter.filter(character =>
            character.name.includes(query)
          );
        } finally {
          this.loading = false;
        }
      } else {
        this.characterOptions = this.bookAllCharacter;
      }
    },
    goBack() {
      // 返回上一页
      this.$router.push('/workbench/createbook/characterlist');
    },
    async savecharacherinfo() {
      // 保存角色信息
      const bookId = localStorage.getItem('currentBookId');
      if (!bookId) {
        this.$message.error('请先保存作品信息');
        return;
      }

      const params = {
        id: this.$route.query.id || null,
        book_id: bookId,
        name: this.form.name,
        gender: this.form.gender === 'male' ? '男' : this.form.gender === '' ? '' : '女',
        personality: this.form.personality,
        background: this.form.background,
        age: this.form.age,
        occupation: this.form.occupation,
        appearance: this.form.appearance,
        physique: this.form.physique,
        avatar: this.form.avatarUrl,
        race: this.form.race,
        relations: this.relations
      };
      // 对字符串字段进行trim处理并更新回this.form，排除gender字段
      Object.keys(params).forEach(key => {
        if (typeof params[key] === 'string' && key !== 'gender') {
          params[key] = params[key].trim();
          // 更新回this.form中对应的字段
          if (key in this.form) {
            this.form[key] = params[key];
          }
        }
      });
      console.log(params)

      // 校验必填字段
      const fields = {
        name: '姓名',
        gender: '性别',
        age: '年龄',
        race: '种族',
        occupation: '职业',
        appearance: '长相描述',
        physique: '体型描述',
        personality: '性格',
        background: '背景'
      }
      for (const [key, label] of Object.entries(fields)) {
        if (key === 'gender') {
          if (!this.form.gender) {
            this.$message.error(`${label}不能为空`);
            return;
          }
        } else if (!params[key]) {
          this.$message.error(`${label}不能为空`);
          return;
        }
      }

      try {
        const res = await this.$axios.post('/manages/savecharacter', params, {
          headers: {
            'X-Auth-Token': localStorage.getItem('token')
          }
        });

        if (res.data.message) {
          this.$message.success(res.data.message);
          // 更新路由中的角色ID（如果是新增）
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
          console.error('保存角色失败:', error);
          this.$message.error(error.response?.data?.error || '保存角色失败');
        }
      }
      // 返回上一页
      this.$router.push('/workbench/createbook/characterlist');
    },
    addRelation() {
      // 添加关联角色
      if (this.bookAllCharacter.length === 0) {
        this.$message.error('当前作品仅有当前角色，无法创建关系')
        return;  // 如果没有角色数据则直接返回
      }
      this.dialogVisible = true;
      this.relationForm = {  // 重置表单
        name: '',
        id: null,
        relationship: ''
      };
    },
    submitRelation() {
      // 检查是否已存在相同ID的关系
      const existingRelation = this.relations.find(item => item.id === this.relationForm.id);
      const index = this.relations.findIndex(item => item.id === this.relationForm.id);
      if (existingRelation) {
        // 编辑待实现
        this.relations.splice(index, 1, {
          name: this.relationForm.name,
          id: this.relationForm.id,
          relationship: this.relationForm.relationship
        });
        this.dialogVisible = false;
      } else {
        // 新增
        this.relations.push({
          name: this.relationForm.name,
          id: this.relationForm.id,
          relationship: this.relationForm.relationship
        });
        this.dialogVisible = false;
      }
      console.log('保存后', this.relations)
    },
    editRelation(row: any) {
      // 编辑关联角色
      this.dialogVisible = true;
      this.relationForm = {
        name: row.name,
        id: row.id,
        relationship: row.relationship
      };
    },
    deleteRelation(row: any) {
      // 删除关联角色
      const index = this.relations.findIndex(item => item.id === row.id);
      if (index !== -1) {
        this.relations.splice(index, 1);
      }
    }
  },
  async mounted() {
    // 获取传参信息能够获取到则是编辑，获取不到则是新增
    const characterinfo = this.$route.query
    if (Object.keys(characterinfo).length > 0) {
      // 编辑
      console.log('编辑', characterinfo)
      this.form = {
        id: characterinfo.id,
        name: characterinfo.name,
        gender: characterinfo.gender === '男' ? 'male' : characterinfo.gender === '' ? '' : 'female',
        personality: characterinfo.personality,
        background: characterinfo.background,
        age: characterinfo.age,
        occupation: characterinfo.occupation,
        appearance: characterinfo.appearance,
        physique: characterinfo.physique,
        avatar: characterinfo.avatar,
        race: characterinfo.race,
        avatarUrl: characterinfo.avatar
      }
      // 获取角色关系列表
      try {
        const response = await this.$axios.get('/manages/characterrelations', {
          params: {
            character_id: characterinfo.id
          },
          headers: {
            'X-Auth-Token': localStorage.getItem('token')
          }
        });

        if (response.data && response.data.relations) {
          this.relations = response.data.relations;
          console.log('角色关系列表', this.relations);
        }
      } catch (error) {
        console.error('获取角色关系列表失败:', error);
        this.$message.error('获取角色关系列表失败');
      }
    } else {
      // 新增
      console.log('新增')
    }
    // 获取书籍角色列表
    try {
      const bookId = localStorage.getItem('currentBookId')
      const response = await this.$axios.get('/manages/querycharacter', {
        params: {
          book_id: bookId
        },
        headers: {
          'X-Auth-Token': localStorage.getItem('token')
        }
      })

      if (response.data && response.data.characterlist) {
        this.bookAllCharacter = response.data.characterlist.filter(character =>
          String(character.id) !== this.form.id
        );
      }
    } catch (error) {
      console.error('获取角色列表失败:', error)
      this.$message.error('获取角色列表失败')
    }
  }
},
);
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
  border-radius: 9999px;
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
  margin-top: 2rem;
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