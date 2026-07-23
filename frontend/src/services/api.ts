import axios from 'axios'
import type { TripFormData, TripPlanResponse } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器：添加 token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('trip_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('响应错误:', error.response?.status, error.message)
    return Promise.reject(error)
  }
)

// ===== 旅行计划相关 =====
export async function generateTripPlan(formData: TripFormData): Promise<TripPlanResponse> {
  const response = await apiClient.post<TripPlanResponse>('/api/trip/plan', formData)
  return response.data
}

export async function savePlan(title: string, planData: any): Promise<any> {
  const response = await apiClient.post('/api/trip/save', {
    title,
    plan_data: planData
  })
  return response.data
}

export async function getUserPlans(): Promise<any> {
  const response = await apiClient.get('/api/trip/plans')
  return response.data
}

export async function getPlanDetail(planId: number): Promise<any> {
  const response = await apiClient.get(`/api/trip/plan/${planId}`)
  return response.data
}

export async function deletePlan(planId: number): Promise<any> {
  const response = await apiClient.delete(`/api/trip/plan/${planId}`)
  return response.data
}

// LangGraph 版本生成计划
export async function generateTripPlanLangGraph(formData: TripFormData): Promise<TripPlanResponse> {
  const response = await apiClient.post<TripPlanResponse>('/api/trip/plan/langgraph', formData)
  return response.data
}

// 调整旅行计划（LLM驱动）
export async function adjustPlan(planId: string, originalPlan: any, feedback: string): Promise<TripPlanResponse> {
  const response = await apiClient.post<TripPlanResponse>('/api/trip/plan/langgraph/adjust', {
    plan_id: planId,
    original_plan: originalPlan,
    feedback: feedback
  })
  return response.data
}

// 提交用户反馈
export interface FeedbackData {
  plan_id: string
  feedback_type: 'positive' | 'negative' | 'rating' | 'comment' | 'adjust_request'
  rating?: number
  comment?: string
  adjust_type?: string
}

export async function submitFeedback(data: FeedbackData): Promise<any> {
  const response = await apiClient.post('/api/trip/feedback', data)
  return response.data
}

// ===== 认证相关 =====
export interface LoginData {
  email: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
}

export interface User {
  id: number
  username: string
  email: string
  created_at: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export async function login(data: LoginData): Promise<AuthResponse> {
  try {
    const response = await apiClient.post<AuthResponse>('/api/auth/login', data)
    return response.data
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw { detail: error.response.data.detail }
    }
    throw error
  }
}

export async function register(data: RegisterData): Promise<AuthResponse> {
  try {
    const response = await apiClient.post<AuthResponse>('/api/auth/register', data)
    return response.data
  } catch (error: any) {
    if (error.response?.data?.detail) {
      throw { detail: error.response.data.detail }
    }
    throw error
  }
}

export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>('/api/auth/me')
  return response.data
}

// 工具函数
export function isLoggedIn(): boolean {
  return !!localStorage.getItem('trip_token')
}

export function getCurrentUserInfo(): User | null {
  const userStr = localStorage.getItem('trip_user')
  if (userStr) {
    try {
      return JSON.parse(userStr)
    } catch {
      return null
    }
  }
  return null
}

export function logout(): void {
  localStorage.removeItem('trip_token')
  localStorage.removeItem('trip_user')
}

export async function healthCheck(): Promise<any> {
  const response = await apiClient.get('/health')
  return response.data
}

export default apiClient
