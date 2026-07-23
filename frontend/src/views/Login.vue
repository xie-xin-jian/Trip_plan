<template>
  <div class="login-wrapper">
    <div class="login-header">
      <router-link to="/" class="logo-link">
        <h1>🌍 HelloAgents智能旅行助手</h1>
      </router-link>
    </div>

    <div class="login-card">
      <h2 class="login-title">登录账号</h2>
      <p class="login-subtitle">欢迎回来！开始规划你的旅行</p>

      <a-form
        :model="formState"
        :rules="rules"
        ref="formRef"
        @finish="handleLogin"
        layout="vertical"
      >
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
            placeholder="请输入密码"
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
            登录
          </a-button>
        </a-form-item>

        <div class="login-footer">
          <span>还没有账号？</span>
          <router-link to="/register">立即注册</router-link>
        </div>
      </a-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { login, type AuthResponse } from '../services/api'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

const formState = reactive({
  email: '',
  password: ''
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱' },
    { type: 'email', message: '请输入有效的邮箱地址' }
  ],
  password: [
    { required: true, message: '请输入密码' },
    { min: 6, message: '密码至少6位' }
  ]
}

const handleLogin = async () => {
  loading.value = true
  try {
    const response: AuthResponse = await login({
      email: formState.email,
      password: formState.password
    })

    localStorage.setItem('trip_token', response.access_token)
    localStorage.setItem('trip_user', JSON.stringify(response.user))

    message.success('登录成功！')
    setTimeout(() => router.push('/'), 500)
  } catch (e: any) {
    message.error(e.detail || '登录失败，请检查邮箱和密码')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
}

.login-header {
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

.login-card {
  max-width: 440px;
  margin: 0 auto;
  background: white;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
}

.login-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #333;
}

.login-subtitle {
  color: #666;
  margin: 0 0 32px 0;
  font-size: 14px;
}

.login-footer {
  text-align: center;
  color: #666;
  font-size: 14px;
  margin-top: 8px;
}

.login-footer a {
  color: #1677ff;
  text-decoration: none;
  font-weight: 500;
  margin-left: 4px;
}
</style>
