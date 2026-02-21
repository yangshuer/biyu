<template>
  <div class="login-container">
    <div class="login-card">
      <div class="logo-section">
        <img src="@/assets/ai-logo.svg" alt="AI创作平台" class="logo">
        <h1>重置密码</h1>
        <p>请输入您的注册邮箱接收重置链接</p>
      </div>

      <form @submit.prevent="handleReset" class="login-form">
        <div class="form-group">
          <label for="email">电子邮箱</label>
          <input type="email" id="email" v-model="email" placeholder="请输入您的注册邮箱">
        </div>

        <button type="submit" class="login-btn">发送重置链接</button>

        <div class="login-footer">
          <router-link to="/login">返回登录</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script>
import { ElMessage } from 'element-plus'
export default {
  data() {
    return {
      email: ''
    }
  },
  methods: {
    async handleReset() {
      // 这里添加发送重制密码连接到邮箱的逻辑。
      if (!this.email) {
        ElMessage.error('请输入您的注册邮箱')
        return
      }
      try {
        const res = await this.$axios.post('/manages/forgot-password', { email: this.email })
        console.log(res)
        if (res.status === 200) {
          ElMessage.success('重置密码链接已发送，请查收您的邮箱')
        } else {
          ElMessage.error('重置邮件失败')
        }
      } catch (error) {
        ElMessage.error(error.message)
      }
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100vw;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  background: white;
  border-radius: 16px;
  padding: 40px;
  width: 100%;
  max-width: 420px;
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
}

.logo-section {
  text-align: center;
  margin-bottom: 30px;
}

.logo {
  width: 80px;
  height: 80px;
  margin-bottom: 15px;
}

h1 {
  color: #333;
  font-size: 24px;
  margin-bottom: 8px;
}

p {
  color: #666;
  font-size: 14px;
}

.form-group {
  margin-bottom: 20px;
}

label {
  display: block;
  margin-bottom: 8px;
  color: #555;
  font-size: 14px;
}

input {
  width: 100%;
  padding: 12px 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  transition: border 0.3s;
}

input:focus {
  border-color: #667eea;
  outline: none;
}

.login-btn {
  width: 100%;
  padding: 12px;
  background: linear-gradient(to right, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: opacity 0.3s;
}

.login-btn:hover {
  opacity: 0.9;
}

.login-footer {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
  font-size: 14px;
}

.login-footer a {
  color: #667eea;
  text-decoration: none;
}

.login-footer a:hover {
  text-decoration: underline;
}
</style>