<!-- frontend/src/views/Home.vue -->
<template>
  <div class="home">
    <div class="hero">
      <h1>智能旅行规划助手</h1>
      <p>输入目的地和偏好，AI 自动规划景点、酒店、餐厅</p>
    </div>

    <div class="form-card">
      <div class="form-grid">
        <!-- 目的地 -->
        <div class="field full">
          <label>目的地城市</label>
          <input v-model="form.city" placeholder="如：北京、上海、成都" />
        </div>

        <!-- 日期 -->
        <div class="field">
          <label>出发日期</label>
          <input v-model="form.start_date" type="date" />
        </div>
        <div class="field">
          <label>返回日期</label>
          <input v-model="form.end_date" type="date" />
        </div>

        <!-- 天数 -->
        <div class="field">
          <label>行程天数</label>
          <input v-model.number="form.days" type="number" min="1" max="14" />
        </div>

        <!-- 偏好 -->
        <div class="field">
          <label>游玩偏好</label>
          <select v-model="form.preferences">
            <option value="历史文化 古迹">历史文化</option>
            <option value="自然风光 公园">自然风光</option>
            <option value="美食 小吃">美食探索</option>
            <option value="博物馆 展览">博物馆展览</option>
            <option value="景点 旅游">综合游览</option>
          </select>
        </div>

        <!-- 交通 -->
        <div class="field">
          <label>出行方式</label>
          <select v-model="form.transportation">
            <option>飞机</option>
            <option>高铁</option>
            <option>自驾</option>
            <option>公交</option>
          </select>
        </div>

        <!-- 住宿 -->
        <div class="field">
          <label>住宿类型</label>
          <select v-model="form.accommodation">
            <option>豪华</option>
            <option>舒适</option>
            <option>经济</option>
            <option>民宿</option>
            <option>青年旅舍</option>
          </select>
        </div>

        <!-- 预算 -->
        <div class="field">
          <label>预算水平</label>
          <select v-model="form.budget">
            <option>经济</option>
            <option>中等</option>
            <option>豪华</option>
          </select>
        </div>

        <!-- 游玩强度 -->
        <div class="field">
          <label>游玩强度</label>
          <select v-model="form.intensity">
            <option value="2">轻松（每天2景点）</option>
            <option value="3">正常（每天3景点）</option>
            <option value="4">紧凑（每天4景点）</option>
          </select>
        </div>
      </div>

      <button class="submit-btn" :disabled="loading" @click="submit">
        {{ loading ? '规划中...' : '开始规划' }}
      </button>

      <!-- 进度条 -->
      <div v-if="loading" class="progress-wrap">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: progress + '%' }" />
        </div>
        <p class="progress-status">{{ statusText }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { streamTripPlan } from '../services/api'
import type { TripPlanRequest } from '../types'

const router = useRouter()
const loading = ref(false)
const progress = ref(0)
const statusText = ref('')

const form = reactive({
  city: '',
  start_date: '',
  end_date: '',
  days: 3,
  preferences: '景点 旅游',
  budget: '中等',
  transportation: '公交',
  accommodation: '舒适',
  intensity: '3',
})

function submit() {
  if (!form.city) return alert('请输入目的地城市')
  if (!form.start_date || !form.end_date) return alert('请选择出发和返回日期')

  loading.value = true
  progress.value = 0
  statusText.value = '准备中...'

  const request: TripPlanRequest = {
    city: form.city,
    start_date: form.start_date,
    end_date: form.end_date,
    days: form.days,
    preferences: form.preferences,
    budget: form.budget,
    transportation: form.transportation,
    accommodation: form.accommodation,
  }

  streamTripPlan(
    request,
    (p) => {
      progress.value = Math.max(progress.value, p.progress)
      statusText.value = p.status
    },
    (plan) => {
      loading.value = false
      sessionStorage.setItem('tripPlan', JSON.stringify(plan))
      router.push('/result')
    },
    (err) => {
      loading.value = false
      alert(`规划失败：${err.message}`)
    },
  )
}
</script>

<style scoped>
.home {
  max-width: 760px;
  margin: 0 auto;
  padding: 40px 20px;
}
.hero {
  text-align: center;
  margin-bottom: 32px;
}
.hero h1 {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 8px;
}
.hero p {
  color: #666;
  font-size: 15px;
}
.form-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 32px;
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 24px;
}
.field { display: flex; flex-direction: column; gap: 6px; }
.field.full { grid-column: 1 / -1; }
label { font-size: 13px; color: #555; font-weight: 500; }
input, select {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color .2s;
}
input:focus, select:focus { border-color: #534AB7; }
.submit-btn {
  width: 100%;
  padding: 12px;
  background: #534AB7;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  cursor: pointer;
  transition: background .2s;
}
.submit-btn:hover:not(:disabled) { background: #3C3489; }
.submit-btn:disabled { background: #aaa; cursor: not-allowed; }
.progress-wrap { margin-top: 16px; }
.progress-bar {
  height: 6px;
  background: #eee;
  border-radius: 3px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: #534AB7;
  border-radius: 3px;
  transition: width .4s ease;
}
.progress-status {
  text-align: center;
  font-size: 13px;
  color: #666;
  margin-top: 8px;
}
</style>