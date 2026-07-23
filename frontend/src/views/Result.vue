<template>
  <div class="result-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <a-button class="back-button" size="large" @click="goBack">
        ← 返回首页
      </a-button>
      <a-space size="middle">
        <a-button v-if="!editMode" type="primary" @click="handleSavePlan" :loading="saving">
          📌 保存行程
        </a-button>
        <a-button v-if="!editMode" @click="toggleEditMode" type="default">
          ✏️ 编辑行程
        </a-button>
        <a-button v-else @click="saveChanges" type="primary">
          💾 保存修改
        </a-button>
        <a-button v-if="editMode" @click="cancelEdit" type="default">
          ❌ 取消编辑
        </a-button>

        <!-- 导出按钮 -->
        <a-dropdown v-if="!editMode">
          <template #overlay>
            <a-menu>
              <a-menu-item key="image" @click="exportAsImage">
                📷 导出为图片
              </a-menu-item>
              <a-menu-item key="pdf" @click="exportAsPDF">
                📄 导出为PDF
              </a-menu-item>
            </a-menu>
          </template>
          <a-button type="default">
            📥 导出行程 <DownOutlined />
          </a-button>
        </a-dropdown>
        
        <a-button v-if="!editMode" @click="showFeedbackPanel = !showFeedbackPanel" type="default" :class="{ 'is-active': showFeedbackPanel }">
          💬 反馈建议
        </a-button>
      </a-space>
    </div>

    <div v-if="tripPlan" class="content-wrapper">
      <!-- 侧边导航 -->
      <div class="side-nav">
        <a-affix :offset-top="80">
          <a-menu mode="inline" :selected-keys="[activeSection]" @click="scrollToSection">
            <a-menu-item key="overview">
              <span>📋 行程概览</span>
            </a-menu-item>
            <a-menu-item key="budget" v-if="tripPlan.budget">
              <span>💰 预算明细</span>
            </a-menu-item>
            <a-menu-item key="map">
              <span>📍 景点地图</span>
            </a-menu-item>
            <a-menu-item key="transportation" v-if="tripPlan.round_trip_transportation">
              <span>🚄 往返交通</span>
            </a-menu-item>
            <a-sub-menu key="days" title="📅 每日行程">
              <a-menu-item v-for="(day, index) in tripPlan.days" :key="`day-${index}`">
                第{{ day.day_index + 1 }}天
              </a-menu-item>
            </a-sub-menu>
            <a-menu-item key="weather" v-if="tripPlan.weather_info && tripPlan.weather_info.length > 0">
              <span>🌤️ 天气信息</span>
            </a-menu-item>
          </a-menu>
        </a-affix>
      </div>

      <!-- 主内容区 -->
      <div class="main-content">
        <!-- 顶部信息区:左侧概览+预算,右侧地图 -->
        <div class="top-info-section">
          <!-- 左侧:行程概览和预算明细 -->
          <div class="left-info">
            <!-- 行程概览 -->
            <a-card id="overview" :title="`${tripPlan.city}旅行计划`" :bordered="false" class="overview-card">
              <div class="overview-content">
                <div class="info-item">
                  <span class="info-label">📅 日期:</span>
                  <span class="info-value">{{ tripPlan.start_date }} 至 {{ tripPlan.end_date }}</span>
                </div>
                <div class="info-item">
                  <span class="info-label">💡 建议:</span>
                  <span class="info-value">{{ tripPlan.overall_suggestions }}</span>
                </div>
              </div>
            </a-card>

            <!-- 预算明细 -->
            <a-card id="budget" v-if="tripPlan.budget" title="💰 预算明细" :bordered="false" class="budget-card">
              <div class="budget-grid">
                <div class="budget-item">
                  <div class="budget-label">景点门票</div>
                  <div class="budget-value">¥{{ tripPlan.budget.total_attractions }}</div>
                </div>
                <div class="budget-item">
                  <div class="budget-label">酒店住宿</div>
                  <div class="budget-value">¥{{ tripPlan.budget.total_hotels }}</div>
                </div>
                <div class="budget-item">
                  <div class="budget-label">餐饮费用</div>
                  <div class="budget-value">¥{{ tripPlan.budget.total_meals }}</div>
                </div>
                <div class="budget-item">
                  <div class="budget-label">交通费用</div>
                  <div class="budget-value">¥{{ tripPlan.budget.total_transportation }}</div>
                </div>
              </div>
              <div class="budget-total">
                <span class="total-label">预估总费用</span>
                <span class="total-value">¥{{ tripPlan.budget.total }}</span>
              </div>
            </a-card>
          </div>

          <!-- 右侧:地图 -->
          <div class="right-map">
            <a-card id="map" title="📍 景点地图" :bordered="false" class="map-card">
              <div id="amap-container" style="width: 100%; height: 500px; position: relative;">
                <div id="amap-loading" style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:#999;text-align:center;z-index:10;">
                  <div style="font-size:48px;margin-bottom:12px;">🗺️</div>
                  <div style="font-size:16px;font-weight:500;">正在加载地图...</div>
                  <div style="font-size:13px;margin-top:8px;color:#666;">请稍候</div>
                </div>
              </div>
            </a-card>
          </div>
        </div>

        <!-- 往返交通信息 -->
        <a-card
          id="transportation"
          v-if="tripPlan.round_trip_transportation"
          title="🚄 往返交通信息"
          :bordered="false"
          class="transport-card"
        >
          <div class="transport-summary">
            <span class="transport-route">
              {{ tripPlan.round_trip_transportation.departure_city }}
              ↔ {{ tripPlan.round_trip_transportation.destination_city }}
            </span>
            <span class="transport-budget">
              往返交通预估: ¥{{ tripPlan.round_trip_transportation.total_transport_budget }}
            </span>
          </div>

          <!-- 预估提示 -->
          <a-alert
            type="warning"
            show-icon
            style="margin-bottom: 16px; background: #fffbe6; border-color: #ffe58f;"
          >
            <template #message>
              <span style="font-weight: 500;">⚠️ 价格信息为预估数据</span>
            </template>
            <template #description>
              <span style="font-size: 13px;">此价格为参考预估，实际票价请以12306官网或航空公司实时查询为准。</span>
            </template>
          </a-alert>

          <!-- 去程 -->
          <a-divider orientation="left">
            <span class="transport-label-out">🚀 去程 ({{ tripPlan.start_date }})</span>
          </a-divider>
          <a-table
            :data-source="tripPlan.round_trip_transportation.outbound"
            :pagination="false"
            size="small"
            class="transport-table"
          >
            <a-table-column title="类型" data-index="transport_type" :width="90">
              <template #default="{ record }">
                <a-tag :color="getTransportColor(record.transport_type)">
                  {{ getTransportLabel(record.transport_type) }}
                </a-tag>
              </template>
            </a-table-column>
            <a-table-column title="车次/航班" data-index="transport_name" :width="110" />
            <a-table-column title="出发" data-index="departure_time" :width="70" />
            <a-table-column title="到达" data-index="arrival_time" :width="70" />
            <a-table-column title="耗时" data-index="duration" :width="80" />
            <a-table-column title="出发站" data-index="departure_station" :ellipsis="true" />
            <a-table-column title="到达站" data-index="arrival_station" :ellipsis="true" />
            <a-table-column title="二等座/经济舱" :width="110">
              <template #default="{ record }">
                <span class="price-cell">¥{{ record.price_economy }}</span>
              </template>
            </a-table-column>
            <a-table-column title="一等座/商务舱" :width="110">
              <template #default="{ record }">
                <span v-if="record.price_business" class="price-cell">¥{{ record.price_business }}</span>
                <span v-else class="price-na">-</span>
              </template>
            </a-table-column>
            <a-table-column title="余票" data-index="seats_available" :width="80" />
          </a-table>

          <!-- 返程 -->
          <a-divider orientation="left" style="margin-top: 24px">
            <span class="transport-label-back">🏠 返程 ({{ tripPlan.end_date }})</span>
          </a-divider>
          <a-table
            :data-source="tripPlan.round_trip_transportation.return_trip"
            :pagination="false"
            size="small"
            class="transport-table"
          >
            <a-table-column title="类型" data-index="transport_type" :width="90">
              <template #default="{ record }">
                <a-tag :color="getTransportColor(record.transport_type)">
                  {{ getTransportLabel(record.transport_type) }}
                </a-tag>
              </template>
            </a-table-column>
            <a-table-column title="车次/航班" data-index="transport_name" :width="110" />
            <a-table-column title="出发" data-index="departure_time" :width="70" />
            <a-table-column title="到达" data-index="arrival_time" :width="70" />
            <a-table-column title="耗时" data-index="duration" :width="80" />
            <a-table-column title="出发站" data-index="departure_station" :ellipsis="true" />
            <a-table-column title="到达站" data-index="arrival_station" :ellipsis="true" />
            <a-table-column title="二等座/经济舱" :width="110">
              <template #default="{ record }">
                <span class="price-cell">¥{{ record.price_economy }}</span>
              </template>
            </a-table-column>
            <a-table-column title="一等座/商务舱" :width="110">
              <template #default="{ record }">
                <span v-if="record.price_business" class="price-cell">¥{{ record.price_business }}</span>
                <span v-else class="price-na">-</span>
              </template>
            </a-table-column>
            <a-table-column title="余票" data-index="seats_available" :width="80" />
          </a-table>
        </a-card>

        <!-- 每日行程:可折叠 -->
        <a-card title="📅 每日行程" :bordered="false" class="days-card">
          <a-collapse v-model:activeKey="activeDays" accordion>
            <a-collapse-panel
              v-for="(day, index) in tripPlan.days"
              :key="index"
              :id="`day-${index}`"
            >
              <template #header>
                <div class="day-header">
                  <span class="day-title">第{{ day.day_index + 1 }}天</span>
                  <span class="day-date">{{ day.date }}</span>
                </div>
              </template>

              <!-- 行程基本信息 -->
              <div class="day-info">
                <div class="info-row">
                  <span class="label">📝 行程描述:</span>
                  <span class="value">{{ day.description }}</span>
                </div>
                <div class="info-row">
                  <span class="label">🚗 交通方式:</span>
                  <span class="value">{{ day.transportation }}</span>
                </div>
                <div class="info-row">
                  <span class="label">🏨 住宿:</span>
                  <span class="value">{{ day.accommodation }}</span>
                </div>
              </div>

              <!-- 景点安排 -->
              <a-divider orientation="left">🎯 景点安排</a-divider>
              <a-list
                :data-source="day.attractions"
                :grid="{ gutter: 16, column: 2 }"
              >
                <template #renderItem="{ item, index }">
                  <a-list-item>
                    <a-card :title="item.name" size="small" class="attraction-card">
                      <!-- 编辑模式下的操作按钮 -->
                      <template #extra v-if="editMode">
                        <a-space>
                          <a-button
                            size="small"
                            @click="moveAttraction(day.day_index, index, 'up')"
                            :disabled="index === 0"
                          >
                            ↑
                          </a-button>
                          <a-button
                            size="small"
                            @click="moveAttraction(day.day_index, index, 'down')"
                            :disabled="index === day.attractions.length - 1"
                          >
                            ↓
                          </a-button>
                          <a-button
                            size="small"
                            danger
                            @click="deleteAttraction(day.day_index, index)"
                          >
                            🗑️
                          </a-button>
                        </a-space>
                      </template>

                      <!-- 景点图片 -->
                      <div class="attraction-image-wrapper">
                        <img
                          :src="getAttractionImage(item.name, index)"
                          :alt="item.name"
                          class="attraction-image"
                          @error="handleImageError"
                        />
                        <div class="attraction-badge">
                          <span class="badge-number">{{ index + 1 }}</span>
                        </div>
                        <div v-if="item.ticket_price" class="price-tag">
                          ¥{{ item.ticket_price }}
                        </div>
                      </div>

                      <!-- 编辑模式下可编辑的字段 -->
                      <div v-if="editMode">
                        <p><strong>地址:</strong></p>
                        <a-input v-model:value="item.address" size="small" style="margin-bottom: 8px" />

                        <p><strong>游览时长(分钟):</strong></p>
                        <a-input-number v-model:value="item.visit_duration" :min="10" :max="480" size="small" style="width: 100%; margin-bottom: 8px" />

                        <p><strong>描述:</strong></p>
                        <a-textarea v-model:value="item.description" :rows="2" size="small" style="margin-bottom: 8px" />
                      </div>

                      <!-- 查看模式 -->
                      <div v-else>
                        <p><strong>地址:</strong> {{ item.address }}</p>
                        <p><strong>游览时长:</strong> {{ item.visit_duration }}分钟</p>
                        <p><strong>描述:</strong> {{ item.description }}</p>
                        <p v-if="item.rating"><strong>评分:</strong> {{ item.rating }}⭐</p>
                      </div>
                    </a-card>
                  </a-list-item>
                </template>
              </a-list>

              <!-- 酒店推荐 -->
              <a-divider v-if="day.hotel" orientation="left">🏨 住宿推荐</a-divider>
              <a-card v-if="day.hotel" size="small" class="hotel-card">
                <template #title>
                  <span class="hotel-title">{{ day.hotel.name }}</span>
                </template>
                <a-descriptions :column="2" size="small">
                  <a-descriptions-item label="地址">{{ day.hotel.address }}</a-descriptions-item>
                  <a-descriptions-item label="类型">{{ day.hotel.type }}</a-descriptions-item>
                  <a-descriptions-item label="价格范围">{{ day.hotel.price_range }}</a-descriptions-item>
                  <a-descriptions-item label="评分">{{ day.hotel.rating }}⭐</a-descriptions-item>
                  <a-descriptions-item label="距离" :span="2">{{ day.hotel.distance }}</a-descriptions-item>
                </a-descriptions>
              </a-card>

              <!-- 餐饮安排 -->
              <a-divider orientation="left">🍽️ 餐饮安排</a-divider>
              <a-descriptions :column="1" bordered size="small">
                <a-descriptions-item
                  v-for="meal in day.meals"
                  :key="meal.type"
                  :label="getMealLabel(meal.type)"
                >
                  {{ meal.name }}
                  <span v-if="meal.description"> - {{ meal.description }}</span>
                </a-descriptions-item>
              </a-descriptions>
            </a-collapse-panel>
          </a-collapse>
        </a-card>

        <a-card id="weather" v-if="tripPlan.weather_info && tripPlan.weather_info.length > 0" title="天气信息" style="margin-top: 20px" :bordered="false">
        <a-list
          :data-source="tripPlan.weather_info"
          :grid="{ gutter: 16, column: 3 }"
        >
          <template #renderItem="{ item }">
            <a-list-item>
              <a-card size="small" class="weather-card">
                <div class="weather-date">{{ item.date }}</div>
                <div class="weather-info-row">
                  <span class="weather-icon">☀️</span>
                  <div>
                    <div class="weather-label">白天</div>
                    <div class="weather-value">{{ item.day_weather }} {{ item.day_temp }}°C</div>
                  </div>
                </div>
                <div class="weather-info-row">
                  <span class="weather-icon">🌙</span>
                  <div>
                    <div class="weather-label">夜间</div>
                    <div class="weather-value">{{ item.night_weather }} {{ item.night_temp }}°C</div>
                  </div>
                </div>
                <div class="weather-wind">
                  💨 {{ item.wind_direction }} {{ item.wind_power }}
                </div>
              </a-card>
            </a-list-item>
          </template>
        </a-list>
        </a-card>
      </div>

      <!-- 用户反馈面板 -->
      <a-card v-if="showFeedbackPanel" title="💬 用户反馈" :bordered="false" class="feedback-card">
        <div class="feedback-content">
          <!-- 评分区域 -->
          <div class="feedback-section">
            <div class="section-title">⭐ 评分</div>
            <div class="rating-stars">
              <a-button
                v-for="star in 5"
                :key="star"
                :type="star <= feedbackRating ? 'primary' : 'default'"
                size="large"
                @click="feedbackRating = star"
              >
                {{ star <= feedbackRating ? '★' : '☆' }}
              </a-button>
            </div>
          </div>

          <!-- 评论区域 -->
          <div class="feedback-section">
            <div class="section-title">📝 评论</div>
            <a-textarea
              v-model:value="feedbackComment"
              placeholder="请输入您对这次行程的评价或建议..."
              :rows="3"
              style="width: 100%"
            />
          </div>

          <!-- 调整请求区域 -->
          <div class="feedback-section">
            <div class="section-title">🔧 调整请求（LLM智能调整）</div>
            <a-textarea
              v-model:value="feedbackAdjustText"
              placeholder="告诉我们您想怎么调整，例如：'第一天太赶了，减少一个景点'、'把第二天的长城换成颐和园'、'预算减少500元'..."
              :rows="3"
              style="width: 100%"
            />
            <a-button
              v-if="feedbackAdjustText"
              type="primary"
              :loading="isAdjusting"
              @click="handleAdjustPlan"
              class="adjust-btn"
            >
              🚀 智能调整
            </a-button>
          </div>

          <!-- 提交按钮 -->
          <div class="feedback-actions">
            <a-button
              v-if="feedbackRating > 0 || feedbackComment"
              type="primary"
              @click="handleSubmitFeedback"
            >
              ✅ 提交反馈
            </a-button>
            <a-button @click="resetFeedback">
              🔄 重置
            </a-button>
          </div>
        </div>
      </a-card>
    </div>

    <a-empty v-else description="没有找到旅行计划数据">
      <template #image>
        <div style="font-size: 80px;">🗺️</div>
      </template>
      <template #description>
        <span style="color: #999;">暂无旅行计划数据,请先创建行程</span>
      </template>
      <a-button type="primary" @click="goBack">返回首页创建行程</a-button>
    </a-empty>

    <!-- 回到顶部按钮 -->
    <a-back-top :visibility-height="300">
      <div class="back-top-button">
        ↑
      </div>
    </a-back-top>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { DownOutlined } from '@ant-design/icons-vue'
import AMapLoader from '@amap/amap-jsapi-loader'
import html2canvas from 'html2canvas'
import jsPDF from 'jspdf'
import type { TripPlan } from '@/types'
import { savePlan, getPlanDetail, isLoggedIn, getCurrentUserInfo, type User, adjustPlan, submitFeedback, type FeedbackData } from '@/services/api'

const router = useRouter()
const route = useRoute()
const tripPlan = ref<TripPlan | null>(null)
const editMode = ref(false)
const originalPlan = ref<TripPlan | null>(null)
const attractionPhotos = ref<Record<string, string>>({})
const activeSection = ref('overview')
const activeDays = ref<number[]>([0])
const currentUser = ref<User | null>(null)
const saving = ref(false)
let map: any = null

// 反馈相关状态
const feedbackRating = ref(0)
const feedbackComment = ref('')
const feedbackAdjustText = ref('')
const showFeedbackPanel = ref(false)
const isAdjusting = ref(false)
const planId = ref(`plan_${Date.now()}`)

onMounted(async () => {
  currentUser.value = getCurrentUserInfo()

  // 优先从 URL 参数加载（从我的行程页面点击）
  const planId = route.query.planId
  if (planId && isLoggedIn()) {
    try {
      const result = await getPlanDetail(Number(planId))
      tripPlan.value = result.data
      sessionStorage.setItem('tripPlan', JSON.stringify(result.data))
      await nextTick()
      initMap()
      return
    } catch (e: any) {
      message.error('加载行程失败')
    }
  }

  // 从 sessionStorage 加载
  const data = sessionStorage.getItem('tripPlan')
  if (data) {
    tripPlan.value = JSON.parse(data)
    await nextTick()
    initMap()
  }
})

const goBack = () => {
  router.push('/')
}

// 提交反馈
async function handleSubmitFeedback() {
  if (!tripPlan.value) return
  
  const feedbackData: FeedbackData = {
    plan_id: planId.value,
    feedback_type: feedbackRating.value > 0 ? 'rating' : 'comment'
  }
  
  if (feedbackRating.value > 0) {
    feedbackData.rating = feedbackRating.value
  }
  
  if (feedbackComment.value) {
    feedbackData.comment = feedbackComment.value
    feedbackData.feedback_type = 'comment'
  }
  
  try {
    const result = await submitFeedback(feedbackData)
    if (result.success) {
      message.success('反馈提交成功！')
      resetFeedback()
    } else {
      message.error(result.message || '提交失败')
    }
  } catch (e: any) {
    console.error('反馈提交失败:', e)
    const errorMsg = e?.response?.data?.detail || e?.detail || '提交失败，请检查网络连接'
    message.error(errorMsg)
  }
}

// 智能调整计划
async function handleAdjustPlan() {
  if (!tripPlan.value || !feedbackAdjustText.value) return
  
  isAdjusting.value = true
  
  try {
    const result = await adjustPlan(planId.value, tripPlan.value, feedbackAdjustText.value)
    
    if (result.success && result.data) {
      tripPlan.value = result.data
      sessionStorage.setItem('tripPlan', JSON.stringify(result.data))
      message.success('计划调整成功！')
      
      // 重新初始化地图
      if (map) {
        map.destroy()
      }
      nextTick(() => {
        initMap()
      })
      
      // 记录调整反馈
      await submitFeedback({
        plan_id: planId.value,
        feedback_type: 'adjust_request',
        comment: feedbackAdjustText.value,
        adjust_type: 'llm_adjustment'
      })
      
      feedbackAdjustText.value = ''
    } else {
      message.warning(result.message || '调整结果可能不完整')
    }
  } catch (e: any) {
    message.error(e.detail || '调整失败，请重试')
  } finally {
    isAdjusting.value = false
  }
}

// 重置反馈
function resetFeedback() {
  feedbackRating.value = 0
  feedbackComment.value = ''
  feedbackAdjustText.value = ''
}

// 保存行程
async function handleSavePlan() {
  if (!isLoggedIn()) {
    Modal.confirm({
      title: '需要登录',
      content: '保存行程需要先登录账号',
      okText: '去登录',
      cancelText: '取消',
      onOk: () => router.push('/login')
    })
    return
  }

  if (!tripPlan.value) return

  const title = `${tripPlan.value.city}之旅`
  saving.value = true
  try {
    await savePlan(title, tripPlan.value)
    message.success('行程保存成功！可在"我的行程"中查看')
  } catch (e: any) {
    message.error(e.detail || '保存失败，请重试')
  } finally {
    saving.value = false
  }
}

// 滚动到指定区域
const scrollToSection = ({ key }: { key: string }) => {
  activeSection.value = key
  const element = document.getElementById(key)
  if (element) {
    element.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

// 切换编辑模式
const toggleEditMode = () => {
  editMode.value = true
  // 保存原始数据用于取消编辑
  originalPlan.value = JSON.parse(JSON.stringify(tripPlan.value))
  message.info('进入编辑模式')
}

// 保存修改
const saveChanges = () => {
  editMode.value = false
  // 更新sessionStorage
  if (tripPlan.value) {
    sessionStorage.setItem('tripPlan', JSON.stringify(tripPlan.value))
  }
  message.success('修改已保存')

  // 重新初始化地图以反映更改
  if (map) {
    map.destroy()
  }
  nextTick(() => {
    initMap()
  })
}

// 取消编辑
const cancelEdit = () => {
  if (originalPlan.value) {
    tripPlan.value = JSON.parse(JSON.stringify(originalPlan.value))
  }
  editMode.value = false
  message.info('已取消编辑')
}

// 删除景点
const deleteAttraction = (dayIndex: number, attrIndex: number) => {
  if (!tripPlan.value) return

  const day = tripPlan.value.days[dayIndex]
  if (day.attractions.length <= 1) {
    message.warning('每天至少需要保留一个景点')
    return
  }

  day.attractions.splice(attrIndex, 1)
  message.success('景点已删除')
}

// 移动景点顺序
const moveAttraction = (dayIndex: number, attrIndex: number, direction: 'up' | 'down') => {
  if (!tripPlan.value) return

  const day = tripPlan.value.days[dayIndex]
  const attractions = day.attractions

  if (direction === 'up' && attrIndex > 0) {
    [attractions[attrIndex], attractions[attrIndex - 1]] = [attractions[attrIndex - 1], attractions[attrIndex]]
  } else if (direction === 'down' && attrIndex < attractions.length - 1) {
    [attractions[attrIndex], attractions[attrIndex + 1]] = [attractions[attrIndex + 1], attractions[attrIndex]]
  }
}

const getMealLabel = (type: string): string => {
  const labels: Record<string, string> = {
    breakfast: '早餐',
    lunch: '午餐',
    dinner: '晚餐',
    snack: '小吃'
  }
  return labels[type] || type
}

// 交通类型辅助函数
const getTransportLabel = (type: string): string => {
  const labels: Record<string, string> = {
    flight: '飞机',
    high_speed_rail: '高铁',
    train: '火车',
    bus: '大巴'
  }
  return labels[type] || type
}

const getTransportColor = (type: string): string => {
  const colors: Record<string, string> = {
    flight: 'blue',
    high_speed_rail: 'green',
    train: 'orange',
    bus: 'purple'
  }
  return colors[type] || 'default'
}

// 获取景点图片
const getAttractionImage = (name: string, index: number): string => {
  // 如果已加载真实图片,返回真实图片
  if (attractionPhotos.value[name]) {
    return attractionPhotos.value[name]
  }

  // 返回一个纯色占位图(避免跨域问题)
  const colors = [
    { start: '#667eea', end: '#764ba2' },
    { start: '#f093fb', end: '#f5576c' },
    { start: '#4facfe', end: '#00f2fe' },
    { start: '#43e97b', end: '#38f9d7' },
    { start: '#fa709a', end: '#fee140' }
  ]
  const colorIndex = index % colors.length
  const { start, end } = colors[colorIndex]

  // 使用base64编码避免中文问题
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">
    <defs>
      <linearGradient id="grad${index}" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" style="stop-color:${start};stop-opacity:1" />
        <stop offset="100%" style="stop-color:${end};stop-opacity:1" />
      </linearGradient>
    </defs>
    <rect width="400" height="300" fill="url(#grad${index})"/>
    <text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="white">${name}</text>
  </svg>`

  return `data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(svg)))}`
}

// 图片加载失败时的处理
const handleImageError = (event: Event) => {
  const img = event.target as HTMLImageElement
  // 使用灰色占位图
  img.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="400" height="300"%3E%3Crect width="400" height="300" fill="%23f0f0f0"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="18" fill="%23999"%3E图片加载失败%3C/text%3E%3C/svg%3E'
}



// 导出为图片
const exportAsImage = async () => {
  try {
    message.loading({ content: '正在生成图片...', key: 'export', duration: 0 })

    const element = document.querySelector('.main-content') as HTMLElement
    if (!element) {
      throw new Error('未找到内容元素')
    }

    // 创建一个独立的容器
    const exportContainer = document.createElement('div')
    exportContainer.style.width = element.offsetWidth + 'px'
    exportContainer.style.backgroundColor = '#f5f7fa'
    exportContainer.style.padding = '20px'

    // 复制所有内容
    exportContainer.innerHTML = element.innerHTML

    // 处理地图截图
    const mapContainer = document.getElementById('amap-container')
    if (mapContainer && map) {
      const mapCanvas = mapContainer.querySelector('canvas')
      if (mapCanvas) {
        const mapSnapshot = mapCanvas.toDataURL('image/png')
        const exportMapContainer = exportContainer.querySelector('#amap-container')
        if (exportMapContainer) {
          exportMapContainer.innerHTML = `<img src="${mapSnapshot}" style="width:100%;height:100%;object-fit:cover;" />`
        }
      }
    }

    // 移除所有ant-card类,替换为纯div
    const cards = exportContainer.querySelectorAll('.ant-card')
    cards.forEach((card) => {
      const cardEl = card as HTMLElement
      try {
        cardEl.className = '' // 移除所有类
        cardEl.style.setProperty('background-color', '#ffffff')
        cardEl.style.setProperty('border-radius', '12px')
        cardEl.style.setProperty('box-shadow', '0 4px 12px rgba(0, 0, 0, 0.1)')
        cardEl.style.setProperty('margin-bottom', '20px')
        cardEl.style.setProperty('overflow', 'hidden')
      } catch (err) {
        console.error('设置卡片样式失败:', err)
      }
    })

    // 处理卡片头部
    const cardHeads = exportContainer.querySelectorAll('.ant-card-head')
    cardHeads.forEach((head) => {
      const headEl = head as HTMLElement
      try {
        headEl.style.setProperty('background-color', '#667eea')
        headEl.style.setProperty('color', '#ffffff')
        headEl.style.setProperty('padding', '16px 24px')
        headEl.style.setProperty('font-size', '18px')
        headEl.style.setProperty('font-weight', '600')
      } catch (err) {
        console.error('设置卡片头部样式失败:', err)
      }
    })

    // 处理卡片内容
    const cardBodies = exportContainer.querySelectorAll('.ant-card-body')
    cardBodies.forEach((body) => {
      const bodyEl = body as HTMLElement
      bodyEl.style.setProperty('background-color', '#ffffff')
      bodyEl.style.setProperty('padding', '24px')
    })

    // 处理酒店卡片头部
    const hotelCards = exportContainer.querySelectorAll('.hotel-card')
    hotelCards.forEach((card) => {
      const head = card.querySelector('.ant-card-head') as HTMLElement
      if (head) {
        head.style.setProperty('background-color', '#1976d2')
      }
      (card as HTMLElement).style.setProperty('background-color', '#e3f2fd')
    })

    // 处理天气卡片
    const weatherCards = exportContainer.querySelectorAll('.weather-card')
    weatherCards.forEach((card) => {
      (card as HTMLElement).style.setProperty('background-color', '#e0f7fa')
    })

    // 处理预算总计
    const budgetTotal = exportContainer.querySelector('.budget-total')
    if (budgetTotal) {
      const el = budgetTotal as HTMLElement
      el.style.setProperty('background-color', '#667eea')
      el.style.setProperty('color', '#ffffff')
      el.style.setProperty('padding', '20px')
      el.style.setProperty('border-radius', '12px')
      el.style.setProperty('margin-bottom', '20px')
    }

    // 处理预算项
    const budgetItems = exportContainer.querySelectorAll('.budget-item')
    budgetItems.forEach((item) => {
      const el = item as HTMLElement
      el.style.setProperty('background-color', '#f5f7fa')
      el.style.setProperty('padding', '16px')
      el.style.setProperty('border-radius', '8px')
      el.style.setProperty('margin-bottom', '12px')
    })

    // 添加到body(隐藏)
    exportContainer.style.position = 'absolute'
    exportContainer.style.left = '-9999px'
    document.body.appendChild(exportContainer)

    const canvas = await html2canvas(exportContainer, {
      backgroundColor: '#f5f7fa',
      scale: 2,
      logging: false,
      useCORS: true,
      allowTaint: true
    })

    // 移除容器
    document.body.removeChild(exportContainer)

    // 转换为图片并下载
    const link = document.createElement('a')
    link.download = `旅行计划_${tripPlan.value?.city}_${new Date().getTime()}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()

    message.success({ content: '图片导出成功!', key: 'export' })
  } catch (error: any) {
    console.error('导出图片失败:', error)
    message.error({ content: `导出图片失败: ${error.message}`, key: 'export' })
  }
}

// 导出为PDF
const exportAsPDF = async () => {
  try {
    message.loading({ content: '正在生成PDF...', key: 'export', duration: 0 })

    const element = document.querySelector('.main-content') as HTMLElement
    if (!element) {
      throw new Error('未找到内容元素')
    }

    // 创建一个独立的容器
    const exportContainer = document.createElement('div')
    exportContainer.style.width = element.offsetWidth + 'px'
    exportContainer.style.backgroundColor = '#f5f7fa'
    exportContainer.style.padding = '20px'

    // 复制所有内容
    exportContainer.innerHTML = element.innerHTML

    // 处理地图截图
    const mapContainer = document.getElementById('amap-container')
    if (mapContainer && map) {
      const mapCanvas = mapContainer.querySelector('canvas')
      if (mapCanvas) {
        const mapSnapshot = mapCanvas.toDataURL('image/png')
        const exportMapContainer = exportContainer.querySelector('#amap-container')
        if (exportMapContainer) {
          exportMapContainer.innerHTML = `<img src="${mapSnapshot}" style="width:100%;height:100%;object-fit:cover;" />`
        }
      }
    }

    // 移除所有ant-card类,替换为纯div
    const cards = exportContainer.querySelectorAll('.ant-card')
    cards.forEach((card) => {
      const cardEl = card as HTMLElement
      try {
        cardEl.className = ''
        cardEl.style.setProperty('background-color', '#ffffff')
        cardEl.style.setProperty('border-radius', '12px')
        cardEl.style.setProperty('box-shadow', '0 4px 12px rgba(0, 0, 0, 0.1)')
        cardEl.style.setProperty('margin-bottom', '20px')
        cardEl.style.setProperty('overflow', 'hidden')
      } catch (err) {
        console.error('设置卡片样式失败:', err)
      }
    })

    // 处理卡片头部
    const cardHeads = exportContainer.querySelectorAll('.ant-card-head')
    cardHeads.forEach((head) => {
      const headEl = head as HTMLElement
      try {
        headEl.style.setProperty('background-color', '#667eea')
        headEl.style.setProperty('color', '#ffffff')
        headEl.style.setProperty('padding', '16px 24px')
        headEl.style.setProperty('font-size', '18px')
        headEl.style.setProperty('font-weight', '600')
      } catch (err) {
        console.error('设置卡片头部样式失败:', err)
      }
    })

    // 处理卡片内容
    const cardBodies = exportContainer.querySelectorAll('.ant-card-body')
    cardBodies.forEach((body) => {
      const bodyEl = body as HTMLElement
      bodyEl.style.setProperty('background-color', '#ffffff')
      bodyEl.style.setProperty('padding', '24px')
    })

    // 处理酒店卡片头部
    const hotelCards = exportContainer.querySelectorAll('.hotel-card')
    hotelCards.forEach((card) => {
      const head = card.querySelector('.ant-card-head') as HTMLElement
      if (head) {
        head.style.setProperty('background-color', '#1976d2')
      }
      (card as HTMLElement).style.setProperty('background-color', '#e3f2fd')
    })

    // 处理天气卡片
    const weatherCards = exportContainer.querySelectorAll('.weather-card')
    weatherCards.forEach((card) => {
      (card as HTMLElement).style.setProperty('background-color', '#e0f7fa')
    })

    // 处理预算总计
    const budgetTotal = exportContainer.querySelector('.budget-total')
    if (budgetTotal) {
      const el = budgetTotal as HTMLElement
      el.style.setProperty('background-color', '#667eea')
      el.style.setProperty('color', '#ffffff')
      el.style.setProperty('padding', '20px')
      el.style.setProperty('border-radius', '12px')
      el.style.setProperty('margin-bottom', '20px')
    }

    // 处理预算项
    const budgetItems = exportContainer.querySelectorAll('.budget-item')
    budgetItems.forEach((item) => {
      const el = item as HTMLElement
      el.style.setProperty('background-color', '#f5f7fa')
      el.style.setProperty('padding', '16px')
      el.style.setProperty('border-radius', '8px')
      el.style.setProperty('margin-bottom', '12px')
    })

    // 添加到body(隐藏)
    exportContainer.style.position = 'absolute'
    exportContainer.style.left = '-9999px'
    document.body.appendChild(exportContainer)

    const canvas = await html2canvas(exportContainer, {
      backgroundColor: '#f5f7fa',
      scale: 2,
      logging: false,
      useCORS: true,
      allowTaint: true
    })

    // 移除容器
    document.body.removeChild(exportContainer)

    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF({
      orientation: 'portrait',
      unit: 'mm',
      format: 'a4'
    })

    const imgWidth = 210 // A4宽度(mm)
    const imgHeight = (canvas.height * imgWidth) / canvas.width

    // 如果内容高度超过一页,分页处理
    let heightLeft = imgHeight
    let position = 0

    pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
    heightLeft -= 297 // A4高度

    while (heightLeft > 0) {
      position = heightLeft - imgHeight
      pdf.addPage()
      pdf.addImage(imgData, 'PNG', 0, position, imgWidth, imgHeight)
      heightLeft -= 297
    }

    pdf.save(`旅行计划_${tripPlan.value?.city}_${new Date().getTime()}.pdf`)

    message.success({ content: 'PDF导出成功!', key: 'export' })
  } catch (error: any) {
    console.error('导出PDF失败:', error)
    message.error({ content: `导出PDF失败: ${error.message}`, key: 'export' })
  }
}

// ====== 地图核心：通过高德API动态搜索城市和景点真实坐标 ======

// 用高德地理编码获取城市中心坐标
const geocodeCity = (AMap: any, cityName: string): Promise<[number, number] | null> => {
  return new Promise((resolve) => {
    const geocoder = new AMap.Geocoder({ city: '全国' })
    geocoder.getLocation(cityName, (status: string, result: any) => {
      if (status === 'complete' && result.info === 'OK') {
        const geocodes = result.geocodes
        if (geocodes && geocodes.length > 0) {
          const loc = geocodes[0].location
          console.log('[Map] Geocoded city:', cityName, '->', [loc.lng, loc.lat])
          resolve([loc.lng, loc.lat])
          return
        }
      }
      console.warn('[Map] Geocode failed for city:', cityName, status)
      resolve(null)
    })
  })
}

// 用高德POI搜索获取景点的真实坐标
const searchPoiLocation = (AMap: any, keyword: string, city: string): Promise<{ lng: number, lat: number, address: string } | null> => {
  return new Promise((resolve) => {
    const placeSearch = new AMap.PlaceSearch({
      city: city,
      citylimit: true,
      pageSize: 1
    })
    placeSearch.search(keyword, (status: string, result: any) => {
      if (status === 'complete' && result.info === 'OK') {
        const pois = result.poiList?.pois
        if (pois && pois.length > 0) {
          const poi = pois[0]
          resolve({
            lng: poi.location.lng,
            lat: poi.location.lat,
            address: poi.pname + poi.cityname + poi.adname + (poi.address || '')
          })
          return
        }
      }
      resolve(null)
    })
  })
}

// 初始化地图
const initMap = async () => {
  await nextTick()
  await new Promise(resolve => setTimeout(resolve, 200))

  const container = document.getElementById('amap-container')
  const loadingEl = document.getElementById('amap-loading')
  if (!container) {
    console.warn('[Map] Container not found')
    return
  }

  const amapKey = import.meta.env.VITE_AMAP_WEB_JS_KEY
  const amapSecurityCode = import.meta.env.VITE_AMAP_SECURITY_CODE

  console.log('[Map] Key:', amapKey ? amapKey.substring(0, 10) + '...' : 'EMPTY')
  console.log('[Map] Security Code:', amapSecurityCode ? amapSecurityCode.substring(0, 8) + '...' : 'EMPTY')

  if (!amapKey) {
    if (loadingEl) loadingEl.remove()
    container.innerHTML = `<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:#999;text-align:center;padding:20px;">
      <div style="font-size:48px;margin-bottom:16px;">⚠️</div>
      <div style="font-size:16px;font-weight:500;margin-bottom:8px;">地图无法加载</div>
      <div style="font-size:14px;">未配置高德地图JS API Key</div>
      <div style="font-size:12px;margin-top:12px;color:#999;">请在 .env 文件中配置 VITE_AMAP_WEB_JS_KEY</div>
    </div>`
    return
  }

  try {
    console.log('[Map] Starting AMapLoader...')

    // 配置安全密钥（高德2.0版本必需）
    if (amapSecurityCode) {
      ;(window as any)._AMapSecurityConfig = {
        securityJsCode: amapSecurityCode
      }
      console.log('[Map] Security code configured')
    } else {
      console.warn('[Map] Warning: No security code configured')
    }

    const AMap = await AMapLoader.load({
      key: amapKey,
      version: '2.0',
      plugins: ['AMap.Geocoder', 'AMap.PlaceSearch', 'AMap.Marker', 'AMap.Polyline', 'AMap.InfoWindow']
    })

    console.log('[Map] AMap SDK loaded successfully')

    // 清除加载状态
    if (loadingEl) loadingEl.remove()

    const destCity = tripPlan.value?.city || '北京'
    console.log('[Map] Target city:', destCity)

    const cityCenter = await geocodeCity(AMap, destCity)
    const center: [number, number] = cityCenter || [116.397128, 39.916527]
    console.log('[Map] Center:', center)

    map = new AMap.Map('amap-container', {
      zoom: 12,
      center: center,
      viewMode: '3D',
      resizeEnable: true
    })

    console.log('[Map] Map instance created')

    if (!tripPlan.value) return

    interface AttrWithCoords {
      name: string
      address: string
      description: string
      visit_duration: number
      dayIndex: number
      attrIndex: number
      lng: number
      lat: number
    }

    const locatedAttractions: AttrWithCoords[] = []
    const searchPromises: Promise<void>[] = []

    tripPlan.value.days.forEach((day, dayIndex) => {
      day.attractions.forEach((attraction, attrIndex) => {
        const promise = searchPoiLocation(AMap, attraction.name, destCity).then(poiResult => {
          if (poiResult) {
            locatedAttractions.push({
              name: attraction.name,
              address: poiResult.address || attraction.address,
              description: attraction.description,
              visit_duration: attraction.visit_duration,
              dayIndex,
              attrIndex,
              lng: poiResult.lng,
              lat: poiResult.lat
            })
          } else {
            const offset = (locatedAttractions.length + attrIndex) * 0.008
            const angle = (locatedAttractions.length + attrIndex) * 1.3
            locatedAttractions.push({
              name: attraction.name,
              address: attraction.address,
              description: attraction.description,
              visit_duration: attraction.visit_duration,
              dayIndex,
              attrIndex,
              lng: center[0] + Math.cos(angle) * offset,
              lat: center[1] + Math.sin(angle) * offset
            })
          }
        })
        searchPromises.push(promise)
      })
    })

    await Promise.all(searchPromises)

    const markers: any[] = []
    locatedAttractions.forEach((attr, index) => {
      const marker = new AMap.Marker({
        position: [attr.lng, attr.lat],
        title: attr.name,
        label: {
          content: `<div style="background:#4CAF50;color:white;padding:3px 7px;border-radius:4px;font-size:11px;">${index + 1}</div>`,
          offset: new AMap.Pixel(0, -30)
        }
      })

      const infoWindow = new AMap.InfoWindow({
        content: `
          <div style="padding:10px;min-width:160px;">
            <h4 style="margin:0 0 6px 0;color:#333;">${attr.name}</h4>
            <p style="margin:3px 0;font-size:12px;"><strong>地址:</strong> ${attr.address}</p>
            <p style="margin:3px 0;font-size:12px;"><strong>游览:</strong> ${attr.visit_duration}分钟</p>
            <p style="margin:3px 0;font-size:12px;color:#999;">${attr.description}</p>
            <p style="margin:3px 0;font-size:11px;color:#1890ff;">第${attr.dayIndex + 1}天 · 景点${attr.attrIndex + 1}</p>
          </div>
        `,
        offset: new AMap.Pixel(0, -30)
      })

      marker.on('click', () => {
        infoWindow.open(map, marker.getPosition())
      })

      markers.push(marker)
    })

    map.add(markers)

    const dayGroups: Map<number, AttrWithCoords[]> = new Map()
    locatedAttractions.forEach(attr => {
      if (!dayGroups.has(attr.dayIndex)) dayGroups.set(attr.dayIndex, [])
      dayGroups.get(attr.dayIndex)!.push(attr)
    })

    dayGroups.forEach((dayAttrs) => {
      if (dayAttrs.length >= 2) {
        const path = dayAttrs.map(a => [a.lng, a.lat])
        const polyline = new AMap.Polyline({
          path: path,
          strokeColor: '#1890ff',
          strokeWeight: 4,
          strokeOpacity: 0.7,
          strokeStyle: 'solid',
          showDir: true
        })
        map.add(polyline)
      }
    })

    if (markers.length > 0) {
      map.setFitView(markers, false, [60, 60, 60, 60])
    }

    console.log('[Map] Map ready with', markers.length, 'markers')
  } catch (error: any) {
    console.error('[Map] Init failed:', error?.message || error)
    container.innerHTML = `<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;color:#999;text-align:center;padding:20px;">
      <div style="font-size:48px;margin-bottom:16px;">🗺️</div>
      <div style="font-size:16px;font-weight:500;margin-bottom:8px;">地图加载失败</div>
      <div style="font-size:14px;color:#666;">错误信息: ${error?.message || '未知错误'}</div>
      <div style="font-size:13px;color:#999;margin-top:12px;">请检查网络连接或高德地图API Key配置</div>
    </div>`
  }
}

</script>

<style scoped>
.result-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding: 40px 20px;
}

.page-header {
  max-width: 1200px;
  margin: 0 auto 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  animation: fadeInDown 0.6s ease-out;
}

.back-button {
  border-radius: 8px;
  font-weight: 500;
}

/* 内容布局 */
.content-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  gap: 24px;
}

.side-nav {
  width: 240px;
  flex-shrink: 0;
}

.side-nav :deep(.ant-menu) {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  background: white;
}

.side-nav :deep(.ant-menu-item) {
  margin: 4px 8px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.side-nav :deep(.ant-menu-item-selected) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.side-nav :deep(.ant-menu-item:hover) {
  background: rgba(102, 126, 234, 0.1);
}

.main-content {
  flex: 1;
  min-width: 0;
}

/* 景点图片样式 */
.attraction-image-wrapper {
  position: relative;
  margin-bottom: 12px;
  border-radius: 8px;
  overflow: hidden;
}

.attraction-image {
  width: 100%;
  height: 200px;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.attraction-image-wrapper:hover .attraction-image {
  transform: scale(1.05);
}

.attraction-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.badge-number {
  font-size: 18px;
}

.price-tag {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(255, 77, 79, 0.9);
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-weight: bold;
  font-size: 14px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* 天气卡片样式 */
.weather-card {
  background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%);
  border: none !important;
  transition: all 0.3s ease;
}

.weather-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
}

.weather-date {
  font-size: 16px;
  font-weight: bold;
  color: #00796b;
  margin-bottom: 12px;
  text-align: center;
}

.weather-info-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.weather-icon {
  font-size: 24px;
}

.weather-label {
  font-size: 12px;
  color: #666;
}

.weather-value {
  font-size: 16px;
  font-weight: 600;
  color: #00796b;
}

.weather-wind {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(0, 121, 107, 0.2);
  text-align: center;
  color: #00796b;
  font-size: 14px;
}

/* 反馈面板样式 */
.feedback-card {
  margin-top: 24px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border: 2px solid #dee2e6;
}

.feedback-card :deep(.ant-card-head) {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.feedback-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.feedback-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.rating-stars {
  display: flex;
  gap: 8px;
}

.rating-stars :deep(.ant-btn) {
  font-size: 28px;
  border-radius: 50%;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
}

.rating-stars :deep(.ant-btn-primary) {
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  border-color: #fbbf24;
}

.rating-stars :deep(.ant-btn-default) {
  background: #f3f4f6;
  border-color: #d1d5db;
}

.adjust-btn {
  margin-top: 12px;
}

.feedback-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  padding-top: 12px;
  border-top: 1px solid #dee2e6;
}

.is-active {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border-color: #10b981;
}

/* 回到顶部按钮 */
.back-top-button {
  width: 50px;
  height: 50px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  font-weight: bold;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-top-button:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
}

/* 酒店卡片样式 */
.hotel-card {
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border: none !important;
}

.hotel-card :deep(.ant-card-head) {
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
}

.hotel-title {
  color: white !important;
  font-weight: 600;
}

/* 顶部信息区布局 */
.top-info-section {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.left-info {
  flex: 0 0 400px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.right-map {
  flex: 1;
}

/* 行程概览卡片 */
.overview-card {
  height: fit-content;
}

.overview-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 14px;
  font-weight: 600;
  color: #666;
}

.info-value {
  font-size: 15px;
  color: #333;
  line-height: 1.6;
}

/* 预算卡片 */
.budget-card {
  height: fit-content;
}

.budget-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.budget-item {
  text-align: center;
  padding: 12px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.budget-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.budget-value {
  font-size: 20px;
  font-weight: 700;
  color: #1890ff;
}

.budget-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: white;
}

.total-label {
  font-size: 16px;
  font-weight: 600;
}

.total-value {
  font-size: 28px;
  font-weight: 700;
}

/* 地图卡片 */
.map-card {
  height: 100%;
  min-height: 500px;
}

.map-card :deep(.ant-card-body) {
  height: calc(100% - 57px);
  padding: 0;
}

/* 每日行程卡片 */
.days-card {
  margin-top: 20px;
}

.day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.day-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.day-date {
  font-size: 14px;
  color: #999;
}

.day-info {
  margin-bottom: 20px;
  padding: 16px;
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.info-row {
  display: flex;
  gap: 12px;
  margin-bottom: 8px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row .label {
  font-weight: 600;
  color: #666;
  min-width: 100px;
}

.info-row .value {
  color: #333;
  flex: 1;
}

/* 卡片样式优化 */
:deep(.ant-card) {
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  margin-bottom: 20px;
  transition: all 0.3s ease;
  animation: fadeInUp 0.6s ease-out;
}

:deep(.ant-card:hover) {
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

:deep(.ant-card-head) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white !important;
  border-radius: 12px 12px 0 0;
  font-weight: 600;
}

:deep(.ant-card-head-title) {
  color: white !important;
  font-size: 18px;
}

:deep(.ant-card-head-title span) {
  color: white !important;
}

/* Collapse样式 */
:deep(.ant-collapse) {
  border: none;
  background: transparent;
}

:deep(.ant-collapse-item) {
  margin-bottom: 16px;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  overflow: hidden;
}

:deep(.ant-collapse-header) {
  background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
  padding: 16px 20px !important;
  font-weight: 600;
}

:deep(.ant-collapse-content) {
  border-top: 1px solid #e8e8e8;
}

:deep(.ant-collapse-content-box) {
  padding: 20px;
}

/* 统计卡片样式 */
:deep(.ant-statistic-title) {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

:deep(.ant-statistic-content) {
  font-size: 24px;
  font-weight: 600;
  color: #1890ff;
}

/* 景点卡片样式 */
:deep(.ant-list-item) {
  transition: all 0.3s ease;
}

:deep(.ant-list-item:hover) {
  transform: scale(1.02);
}

/* 动画 */
@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 交通卡片样式 */
.transport-card {
  margin-top: 20px;
}

.transport-summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
  border-radius: 12px;
  margin-bottom: 8px;
}

.transport-route {
  font-size: 20px;
  font-weight: 700;
  color: #2e7d32;
}

.transport-budget {
  font-size: 16px;
  font-weight: 600;
  color: #1565c0;
  background: white;
  padding: 6px 16px;
  border-radius: 20px;
}

.transport-label-out {
  color: #1976d2;
  font-weight: 600;
  font-size: 15px;
}

.transport-label-back {
  color: #e65100;
  font-weight: 600;
  font-size: 15px;
}

.transport-table :deep(.ant-table) {
  border-radius: 8px;
  overflow: hidden;
}

.transport-table :deep(.ant-table-thead > tr > th) {
  background: #f0f5ff;
  font-weight: 600;
  font-size: 12px;
  padding: 8px 6px;
}

.transport-table :deep(.ant-table-tbody > tr > td) {
  font-size: 13px;
  padding: 6px;
}

.price-cell {
  color: #f5222d;
  font-weight: 600;
}

.price-na {
  color: #bbb;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .result-container {
    padding: 20px 10px;
  }

  .page-header {
    flex-direction: column;
    gap: 16px;
  }
}
</style>

