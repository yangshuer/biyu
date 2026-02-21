<template>
    <div class="login-container">
      <div class="login-card">
        <div class="logo-section">
          <img src="../assets/ai-logo.svg" alt="AI创作平台" class="logo">
          <h1>笔羽</h1>
          <p>用AI，轻松创作😊～</p>
        </div>
  
        <form @submit.prevent="handleLogin" class="login-form">
          <div class="form-group">
            <label for="email">电子邮箱</label>
            <input 
              type="email" 
              id="email" 
              v-model="email"
              placeholder="请输入您的邮箱"
              required
            >
          </div>
  
          <div class="form-group">
            <label for="password">密码</label>
            <input 
              type="password" 
              id="password" 
              v-model="password"
              placeholder="请输入密码"
              required
            >
          </div>
  
          <button type="submit" class="login-btn">登 录</button>
          
          <div class="login-footer">
            <router-link to="/signin">注册账号</router-link>
            <router-link to="/forgot-password">忘记密码?</router-link>
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
        email: '',
        password: ''
      }
    },
    methods: {
      async handleLogin() {
        console.log('登录信息:', this.email, this.password)
        try {
          const response = await this.$axios.post('/manages/login', {
            email: this.email,
            password: this.password
          })
          
          ElMessage.success('登录成功')
          // 存储token到localStorage
          localStorage.setItem('token', response.data.token)
          localStorage.setItem('userInfo', JSON.stringify({
            email: response.data.email,
            username: response.data.username,
            userId: response.data.user_id
          }))
          // 延迟500ms后跳转到首页
          await new Promise(resolve => setTimeout(resolve, 500))
          this.$router.push('/workbench')
        } catch (error) {
          if (error.request) {
            ElMessage.error(`${JSON.parse(error.request.responseText).error}`)
          } else {
            ElMessage.error('登录失败，请检查网络连接')
          }
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