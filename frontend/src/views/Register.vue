<template>
  <div class="register-wrapper">
    <div class="register-header">
      <router-link to="/" class="logo-link">
        <h1>🌍 HelloAgents智能旅行助手</h1>
      </router-link>
    </div>

    <div class="register-card">
      <h2 class="register-title">创建账号</h2>
      <p class="register-subtitle">注册并开始规划你的旅行</p>

      <a-form
        :model="formState"
        :rules="rules"
        ref="formRef"
        @finish="handleRegister"
        layout="vertical"
      >
        <a-form-item label="用户名" name="username">
          <a-input
            v-model:value="formState.username"
            placeholder="请输入用户名"
            size="large"
          >
            <template #prefix>👤</template>
          </a-input>
        </a-form-item>

        <a-form-item label="邮箱" name="email">
          <a-input
            v-model:value="formState.email"
            placeholder="请输入邮箱"
            size="large"
          >
            <template #prefix>📧</template>
          </a-input>
        </a-form-item>

        <a-form-item label="密码" name="password">
          <a-input-password
            v-model:value="formState.password"
            placeholder="请输入密码（至少6位）"
            size="large"
          >
            <template #prefix>🔑</template>
          </a-input-password>
        </a-form-item>

        <a-form-item label="确认密码" name="confirmPassword">
          <a-input-password
            v-model:value="formState.confirmPassword"
            placeholder="请再次输入密码"
            size="large"
          >
            <template #prefix>🔑</template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-button
            type="primary"
            html-type="submit"
            size="large"
            block
            :loading="loading"
          >
            注册
          </a-button>
        </a-form-item>

        <div class="register-footer">
          <span>已有账号？</span>
          <router-link to="/login">立即登录</router-link>
        </div>
      </a-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { register, type AuthResponse } from '../services/api'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

const formState = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validateConfirmPassword = (_rule: any, value: string, callback: any) => {
  if (!value) {
    return callback('请确认密码')
  }
  if (value !== formState.password) {
    return callback('两次输入的密码不一致')
  }
  callback()
}

const rules = {
  username: [
    { required: true, message: '请输入用户名' },
    { min: 2, max: 20, message: '用户名需2-20个字符' }
  ],
  email: [
    { required: true, message: '请输入邮箱' },
    { type: 'email', message: '请输入有效的邮箱地址' }
  ],
  password: [
    { required: true, message: '请输入密码' },
    { min: 6, message: '密码至少6位' }
  ],
  confirmPassword: [
    { required: true, validator: validateConfirmPassword }
  ]
}

const handleRegister = async () => {
  loading.value = true
  try {
    const response: AuthResponse = await register({
      username: formState.username,
      email: formState.email,
      password: formState.password
    })

    localStorage.setItem('trip_token', response.access_token)
    localStorage.setItem('trip_user', JSON.stringify(response.user))

    message.success('注册成功！')
    setTimeout(() => router.push('/'), 500)
  } catch (e: any) {
    message.error(e.detail || '注册失败，请重试')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-wrapper {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
}

.register-header {
  text-align: center;
  margin-bottom: 40px;
}

.logo-link {
  text-decoration: none;
  color: white;
}

.logo-link h1 {
  font-size: 28px;
  margin: 0;
}

.register-card {
  max-width: 440px;
  margin: 0 auto;
  background: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.register-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #333;
}

.register-subtitle {
  color: #666;
  margin: 0 0 32px 0;
  font-size: 14px;
}

.register-footer {
  text-align: center;
  color: #666;
  font-size: 14px;
  margin-top: 8px;
}

.register-footer a {
  color: #1677ff;
  text-decoration: none;
  font-weight: 500;
  margin-left: 4px;
}
</style>
