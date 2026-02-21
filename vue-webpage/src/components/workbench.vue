<template>
  <div>
    <ElContainer class="app-container">
      <!-- 顶部导航 -->
      <ElHeader class="header">
        <div class="logo-container">
          <img src="../assets/ai-logo.svg" alt="Logo" class="logo" />
          <span class="logo-text">
            <p style="font-size: 26px;">笔羽</p>
            <p style="font-size: 12px; margin-left: 14px;margin-top: 14px;">用AI，轻松创作😊～</p>
          </span>
        </div>
        <div style="font-size: 18px; font-weight: bolder; align-items: center;">
          {{ bookname }}
        </div>
        <div class="header-right">
          <div class="header-link hover-pointer">使用教程</div>
          <!-- <div class="header-link">
            消息通知
            <span v-if="notification_number > 0" class="notification-dot"
              :key="notification_number">+{{ notification_number }}</span>
          </div> -->
          <div @click="setModel" class="header-link hover-pointer">模型配置</div>
          <div class="header-link">｜</div>
          <div class="header-link">
            <!-- 使用 ElTooltip 组件，鼠标悬停显示退出按钮 -->
            <ElTooltip placement="bottom" effect="light">
              <template #content>
                <ElButton size="small" @click="handleLogout">退出登录</ElButton>
              </template>
              <span style="font-weight: bold;">{{ userinfo.username }}</span>
            </ElTooltip>
          </div>
          <!-- <div class="header-link" style="font-weight: bold;">{{ userinfo.username }}</div> -->
          <!-- <div class="header-link" style="font-weight: bold;">{{ userinfo.username.length <= 4 ? userinfo.username :
            userinfo.username.slice(0, 3) + '...' }}</div>
              <img src="../assets/default-profile-picture.png" class="logo"
                style="margin-right: 0;border-radius: 50%; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);" /> -->
        </div>
        <!-- 弹窗组件 -->
        <ElDialog v-model="dialogVisible" title="模型配置" width="70%">
          <div>
            <div class="model-card">
              <p style="margin: 5px;">配置创作模型，仅支持OpenAI式API,推荐使用gemini-2.5,deepseek-r1,默认配置gemini-2.5-pro(免费)</p>
              <ElInput style="margin: 5px; width: calc(100% - 10px);" v-model="model.creations.model"
                placeholder="请输入模型名称">
                <template #prepend>Model</template>
              </ElInput>
              <ElInput style="margin: 5px; width: calc(100% - 10px);" v-model="model.creations.api_key"
                placeholder="请输入API Key">
                <template #prepend>API Key</template>
              </ElInput>
              <ElInput style="margin: 5px; width: calc(100% - 10px);" v-model="model.creations.base_url"
                placeholder="请输入Base URL">
                <template #prepend>Base URL</template>
              </ElInput>
            </div>
            <div class="model-card">
              <p style="margin: 5px;">配置助手模型，仅支持OpenAI式API,默认配置glm-4-flash-250414(免费)</p>
              <ElInput style="margin: 5px; width: calc(100% - 10px);" v-model="model.chat.model" placeholder="请输入模型名称">
                <template #prepend>Model</template>
              </ElInput>
              <ElInput style="margin: 5px; width: calc(100% - 10px);" v-model="model.chat.api_key"
                placeholder="请输入API Key">
                <template #prepend>API Key</template>
              </ElInput>
              <ElInput style="margin: 5px; width: calc(100% - 10px);" v-model="model.chat.base_url"
                placeholder="请输入Base URL">
                <template #prepend>Base URL</template>
              </ElInput>
            </div>
            <div class="model-card">
              <p style="margin: 5px;">配置情节模型，仅支持OpenAI式API,默认配置glm-4-flash-250414(免费)</p>
              <ElInput style="margin: 5px; width: calc(100% - 10px);" v-model="model.plots.model" placeholder="请输入模型名称">
                <template #prepend>Model</template>
              </ElInput>
              <ElInput style="margin: 5px; width: calc(100% - 10px);" v-model="model.plots.api_key"
                placeholder="请输入API Key">
                <template #prepend>API Key</template>
              </ElInput>
              <ElInput style="margin: 5px; width: calc(100% - 10px);" v-model="model.plots.base_url"
                placeholder="请输入Base URL">
                <template #prepend>Base URL</template>
              </ElInput>
            </div>
            <div class="model-card">
              <p style="margin: 5px;">配置生图模型api_key，默认配置CogView-3-Flash(免费)</p>
              <el-input v-model="model.img.api_key" style="margin: 5px; width: calc(100% - 10px);"
                placeholder="请输入API Key">
                <template #prepend>API Key</template>
              </el-input>
            </div>
          </div>
          <template #footer>
            <span class="dialog-footer">
              <ElButton @click="dialogVisible = false">取消</ElButton>
              <ElButton type="primary" @click="update_models">保存</ElButton>
            </span>
          </template>
        </ElDialog>
      </ElHeader>
      <!-- 主内容区域 -->
      <ElMain class="main-content">
        <div class="content-area">
          <RouterView />
        </div>
      </ElMain>
    </ElContainer>
  </div>
</template>

<script>
import NProgress, { set } from 'nprogress'
import 'nprogress/nprogress.css'

import { RouterLink, RouterView } from 'vue-router'
import { Search, Plus } from '@element-plus/icons-vue'
import {
  ElHeader,
  ElMain,
  ElContainer,
  ElButton,
  ElInput
} from 'element-plus'
import { h } from 'vue'

export default {
  data() {
    return {
      hasData: true, // 是否显示缺省页面 false
      searchText: '',
      dialogVisible: false,
      model: {
        creations: {
          model: "",
          api_key: "",
          base_url: ""
        },
        chat: {
          model: "",
          api_key: "",
          base_url: ""
        },
        plots: {
          model: "",
          api_key: "",
          base_url: ""
        },
        img: {
          api_key: ""
        }
      }
    }
  },
  setup() {
    return {
      Search,
      Plus,
      userinfo: {
        userId: JSON.parse(localStorage.getItem('userInfo')).userId,
        username: JSON.parse(localStorage.getItem('userInfo')).username,
        email: JSON.parse(localStorage.getItem('userInfo')).email
      },
      notification_number: 0,
      bookname: ''//当前在创作的书名
    }
  },
  methods: {
    async setModel() {
      this.dialogVisible = true
      try {
        const res = await this.$axios.get('/manages/get-model-config', {
          headers: {
            'X-Auth-Token': localStorage.getItem('token'),
          }
        })
        if (res.status === 200) {
          this.model = res.data.model_config
        } else {
          this.$message.error('接口请求失败')
        }
      } catch (error) {
        this.$message.error('接口请求失败')
      }
    },
    async update_models() {
      try {
        const res = await this.$axios.post('/manages/update-model-config', {
          model_config: this.model
        }, {
          headers: {
            'X-Auth-Token': localStorage.getItem('token'),
          }
        })
        if (res.status === 200) {
          this.$message.success('模型配置更新成功')
          this.dialogVisible = false
        } else {
          this.$message.error('接口请求失败')
        }
      } catch (error) {
        this.$message.error('接口请求失败')
      }
    },
    handleRouteRedirect() {
      if (this.hasData) {
        this.$router.push('/workbench/booklist')
      } else {
        this.$router.push('/workbench/empty')
      }
    },
    handleLogout() {
      localStorage.removeItem('token')
      this.$router.push('/login')
    }
  },
  mounted() {
    if (this.hasData) {
      this.$router.push('/workbench/booklist')
    } else {
      this.$router.push('/workbench/empty')
    }

    // 初始化NProgress配置
    NProgress.configure({
      showSpinner: false,
      easing: 'ease',
      speed: 500
    })

    if (this.hasData) {
      this.$router.push('/workbench/booklist')
    } else {
      this.$router.push('/workbench/empty')
    }
  },
  created() {
    // 路由跳转前开始进度条
    this.$router.beforeEach((to, from, next) => {
      NProgress.start()
      next()
    })

    // 路由跳转完成后结束进度条
    this.$router.afterEach(() => {
      NProgress.done()
    })
  },
  watch: {
    notification_number(newVal, oldVal) {
      // 当notification_number变化时自动触发
      console.log(`通知数量从 ${oldVal} 变为 ${newVal}`);
      // 这里可以添加其他需要触发的逻辑
    },// 添加路由变化监听
    '$route'(to, from) {
      if (to.path === '/workbench') {
        this.handleRouteRedirect();
      }
    }
  }
}
</script>


<style scoped>
/* 添加NProgress样式覆盖 */
#nprogress .bar {
  background: #409EFF !important;
  /* 使用Element Plus的主色 */
  height: 3px !important;
}

.el-input-group__prepend {
  width: 80px;
}

.model-card {
  border: 1px solid #e7e7e7;
  /* height: 160px; */
  width: calc(100% - 40px);
  margin: 10px;
  border-radius: 8px;
}

.app-container {
  width: 100vw;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  background-color: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

.logo-container {
  display: flex;
  align-items: center;
}

.logo {
  height: 32px;
  margin-right: 10px;
}

.logo-text {
  font-size: 16px;
  font-weight: 500;
  color: #333;
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.header-link {
  color: #666;
  text-decoration: none;
  cursor: default;
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

.hover-pointer {
  cursor: pointer;
}

/* 主内容区域样式 */
.main-content {
  padding: 20px;
}

.el-main {
  overflow: hidden;
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

.create-btn {
  height: 38px;
}

/* 内容区域样式 */
.content-area {
  background-color: #fff;
  border-radius: 8px;
  height: calc(100vh - 100px);
  padding: 20px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .search-box {
    width: 200px;
  }

  .header-right {
    gap: 10px;
  }
}

.notification-dot {
  font-size: 12px;
  color: red;
  font-weight: bold;
}
</style>