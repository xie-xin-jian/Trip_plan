<template>
  <div class="my-plans-wrapper">
    <div class="page-header">
      <router-link to="/" class="logo-link">
        <h1>🌍 HelloAgents智能旅行助手</h1>
      </router-link>
      <div class="header-actions">
        <router-link to="/" class="nav-link">返回首页</router-link>
      </div>
    </div>

    <div class="content">
      <h2 class="page-title">📋 我的行程</h2>

      <div v-if="loading" class="loading-state">
        <a-spin size="large" tip="加载中...">
          <div style="padding: 50px;"></div>
        </a-spin>
      </div>

      <div v-else-if="plans.length === 0" class="empty-state">
        <div class="empty-icon">🗺️</div>
        <h3>暂无保存的行程</h3>
        <p>去首页创建并保存你的第一个旅行计划吧！</p>
        <a-button type="primary" size="large" @click="router.push('/')">
          创建行程
        </a-button>
      </div>

      <div v-else class="plans-list">
        <div
          v-for="plan in plans"
          :key="plan.id"
          class="plan-card"
          @click="viewPlan(plan.id)"
        >
          <div class="plan-icon">📌</div>
          <div class="plan-info">
            <h3 class="plan-title">{{ plan.title }}</h3>
            <p class="plan-date">创建于 {{ formatDate(plan.created_at) }}</p>
          </div>
          <div class="plan-actions" @click.stop>
            <a-button type="primary" size="small" @click="viewPlan(plan.id)">
              查看
            </a-button>
            <a-popconfirm
              title="确定要删除这个行程吗？"
              ok-text="删除"
              cancel-text="取消"
              @confirm="handleDelete(plan.id)"
            >
              <a-button danger size="small">删除</a-button>
            </a-popconfirm>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { getUserPlans, deletePlan, isLoggedIn } from '../services/api'

const router = useRouter()
const loading = ref(false)
const plans = ref<Array<{ id: number; title: string; created_at: string }>>([])

onMounted(async () => {
  if (!isLoggedIn()) {
    message.warning('请先登录')
    router.push('/login')
    return
  }
  await loadPlans()
})

async function loadPlans() {
  loading.value = true
  try {
    const result = await getUserPlans()
    plans.value = result.plans || []
  } catch (e: any) {
    message.error('加载行程失败')
  } finally {
    loading.value = false
  }
}

function viewPlan(planId: number) {
  router.push(`/result?planId=${planId}`)
}

async function handleDelete(planId: number) {
  try {
    await deletePlan(planId)
    message.success('删除成功')
    plans.value = plans.value.filter(p => p.id !== planId)
  } catch (e: any) {
    message.error('删除失败')
  }
}

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch {
    return dateStr
  }
}
</script>

<style scoped>
.my-plans-wrapper {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0 0 40px 0;
}

.page-header {
  background: rgba(0, 0, 0, 0.15);
  padding: 20px 40px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo-link {
  text-decoration: none;
  color: white;
}

.logo-link h1 {
  font-size: 22px;
  margin: 0;
}

.nav-link {
  color: white;
  text-decoration: none;
  font-size: 14px;
  padding: 8px 16px;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.15);
  transition: background 0.2s;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.25);
}

.content {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px 20px;
}

.page-title {
  color: white;
  font-size: 28px;
  margin: 0 0 30px 0;
  text-align: center;
}

.loading-state, .empty-state {
  background: white;
  border-radius: 16px;
  padding: 60px 40px;
  text-align: center;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-state h3 {
  color: #333;
  margin: 0 0 8px 0;
  font-size: 20px;
}

.empty-state p {
  color: #666;
  margin: 0 0 24px 0;
}

.plans-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.plan-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.plan-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.plan-icon {
  font-size: 36px;
  flex-shrink: 0;
}

.plan-info {
  flex: 1;
}

.plan-title {
  margin: 0 0 6px 0;
  font-size: 18px;
  color: #333;
}

.plan-date {
  margin: 0;
  color: #888;
  font-size: 14px;
}

.plan-actions {
  display: flex;
  gap: 10px;
}
</style>
