<template>
    <div class="login-container">
      <div class="login-card">
        <div class="logo-section">
          <img src="../assets/ai-logo.svg" alt="AI创作平台" class="logo">
          <h1>加入笔羽</h1>
          <p>用AI，轻松创作😊～</p>
        </div>
  
        <form @submit.prevent="handleRegister" class="login-form">
          <div class="form-group">
            <label for="username">用户名</label>
            <input 
              type="text" 
              id="username" 
              v-model="username"
              placeholder="设置您的用户名"
              required
            >
          </div>
  
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
              @input="validatePassword"
              placeholder="设置密码(至少8位，包含大小写字母和数字)"
              required
              minlength="8"
            >
            <p class="error-message" v-if="passwordError">{{ passwordError }}</p>
          </div>
  
          <div class="form-group">
            <label for="confirmPassword">确认密码</label>
            <input 
              type="password" 
              id="confirmPassword" 
              v-model="confirmPassword"
              placeholder="再次输入密码"
              required
              minlength="8"
            >
          </div>
  
          <button type="submit" class="login-btn">注 册</button>
          
          <div class="login-footer">
            <span>已有账号?</span>
            <router-link to="/login">立即登录</router-link>
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
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        passwordError: ''  // 新增密码错误提示
      }
    },
    methods: {
      validatePassword() {
        const hasLenght = this.password.length > 8;
        const hasNumber = /\d/.test(this.password);
        const hasUpper = /[A-Z]/.test(this.password);
        const hasLower = /[a-z]/.test(this.password);
        
        if (!hasNumber || !hasUpper || !hasLower || !hasLenght) {
          this.passwordError = '密码必须是包含数字、大写字母和小写字母的8位以上字符串';
          return false;
        }
        this.passwordError = '';
        return true;
      },
      async handleRegister() {
        if (this.password !== this.confirmPassword) {
          ElMessage.error('两次输入的密码不一致');
          return;
        }
        // 这里添加注册逻辑
        console.log('注册信息:', this.username, this.email, this.password);
        try{
            await this.$axios.post('/manages/signin',{
              username: this.username,
              email: this.email,
              password: this.password
            }
          )
          ElMessage.success('注册成功!正在跳转登陆页面～')
          await new Promise(resolve => setTimeout(resolve, 500))
          this.$router.push('/login')
        }catch(error){
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
  /* 复用登录页面的样式，保持风格一致 */
  .login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    width: 100vw;
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
    justify-content: center;
    align-items: center;
    gap: 8px;
    margin-top: 20px;
    font-size: 14px;
  }
  
  .login-footer span {
    color: #666;
  }
  
  .login-footer a {
    color: #667eea;
    text-decoration: none;
  }
  
  .login-footer a:hover {
    text-decoration: underline;
  }
  .error-message {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 5px;
}
  </style>