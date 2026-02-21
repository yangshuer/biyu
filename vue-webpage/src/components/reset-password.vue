<template>
    <div class="reset-root">
        <div class="reset-password">
        <h2>重置密码</h2>
        <form @submit.prevent="handleSubmit">
            <div class="form-group">
            <label>新密码</label>
            <input 
                type="password" 
                v-model="password" 
                @input="validatePassword"
                required 
                placeholder="请输入新密码(包含大小写字母和数字)"
            />
            <p class="error-message" v-if="passwordError">{{ passwordError }}</p>
            </div>
            <div class="form-group">
            <label>确认密码</label>
            <input 
                type="password" 
                v-model="confirmPassword" 
                required 
                placeholder="请再次输入密码"
            />
            </div>
            <button type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? '提交中...' : '提交' }}
            </button>
        </form>
        </div>
    </div>
  </template>
  
  <script>
  import { ElMessage } from 'element-plus'
  export default {
    data() {
      return {
        password: '',
        confirmPassword: '',
        isSubmitting: false,
        passwordError: ''  // 新增密码错误提示
      }
    },
    computed: {
      email() {
        return this.$route.params.email
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
      async handleSubmit() {
        if (this.password !== this.confirmPassword) {
          ElMessage.error('两次输入的密码不一致')
          return
        }
  
        this.isSubmitting = true
        try {
          await this.$axios.post('/manages/reset-password', {
            email: this.email,
            password: this.password
          })
          ElMessage.success('密码重置成功!正在跳转登陆页面～')
          await new Promise(resolve => setTimeout(resolve, 500))
          this.$router.push('/login')
        } catch (error) {
          console.error('重置密码失败:', error)
          ElMessage.error('重置密码失败，请稍后重试')
        } finally {
          this.isSubmitting = false
        }
      }
    }
  }
  </script>
  
  <style scoped>
  .reset-root{
    width: 100vw;
  }
  .reset-password {
    max-width: 400px;
    margin: 5rem auto;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    background: white;
  }
  
  h2 {
    text-align: center;
    color: #2c3e50;
    margin-bottom: 2rem;
    font-size: 1.8rem;
  }
  
  form {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  label {
    font-weight: 500;
    color: #2c3e50;
    font-size: 0.95rem;
  }
  
  input {
    width: 100%;
    padding: 12px 16px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    font-size: 1rem;
    transition: border-color 0.3s;
  }
  
  input:focus {
    outline: none;
    border-color: #42b983;
    box-shadow: 0 0 0 2px rgba(66, 185, 131, 0.2);
  }
  
  button {
    width: 100%;
    padding: 12px;
    background-color: #42b983;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 500;
    cursor: pointer;
    transition: background-color 0.3s;
    margin-top: 1rem;
  }
  
  button:hover {
    background-color: #3aa876;
  }
  
  button:disabled {
    background-color: #a0a0a0;
    cursor: not-allowed;
  }
  
  @media (max-width: 480px) {
    .reset-password {
      margin: 2rem auto;
      padding: 1.5rem;
      width: 90%;
    }
  }
  .error-message {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 5px;
}
  </style>