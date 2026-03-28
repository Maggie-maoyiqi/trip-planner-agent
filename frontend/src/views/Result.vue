<!-- frontend/src/views/Result.vue -->
<template>
  <div v-if="plan" class="result">

    <!-- 侧边导航 -->
    <nav class="sidenav">
      <a href="#overview" @click.prevent="scrollTo('overview')">行程概览</a>
      <a href="#budget" @click.prevent="scrollTo('budget')">预算明细</a>
      <a href="#weather" @click.prevent="scrollTo('weather')">天气</a>
      <a href="#map" @click.prevent="scrollTo('map')">地图</a>
      <a href="#itinerary" @click.prevent="scrollTo('itinerary')">每日行程</a>
    </nav>

    <div class="main">

      <!-- 概览 -->
      <section id="overview" class="card">
        <h2>{{ plan.city }} · {{ plan.days.length }}天行程</h2>
        <p class="dates">{{ plan.start_date }} → {{ plan.end_date }}</p>
        <p class="suggestion">{{ plan.overall_suggestions }}</p>
        <div class="export-btns">
          <button @click="exportPng">导出图片</button>
          <button @click="exportPdf">导出 PDF</button>
        </div>
      </section>

      <!-- 预算 -->
      <section id="budget" class="card">
        <h3>预算明细</h3>
        <div v-if="plan.budget" class="budget-grid">
          <div class="budget-item">
            <span class="budget-label">景点门票</span>
            <span class="budget-value">¥{{ plan.budget.total_attractions }}</span>
          </div>
          <div class="budget-item">
            <span class="budget-label">酒店住宿</span>
            <span class="budget-value">¥{{ plan.budget.total_hotels }}</span>
          </div>
          <div class="budget-item">
            <span class="budget-label">餐饮费用</span>
            <span class="budget-value">¥{{ plan.budget.total_meals }}</span>
          </div>
          <div class="budget-item">
            <span class="budget-label">交通费用</span>
            <span class="budget-value">¥{{ plan.budget.total_transportation }}</span>
          </div>
          <div class="budget-item total">
            <span class="budget-label">预估总费用</span>
            <span class="budget-value">¥{{ plan.budget.total }}</span>
          </div>
        </div>
      </section>

      <!-- 天气 -->
      <section id="weather" class="card">
        <h3>旅行期间天气</h3>
        <div class="weather-row">
          <div
            v-for="w in plan.weather_info.slice(0, plan.days.length)"
            :key="w.date"
            class="weather-card"
          >
            <div class="weather-date">{{ w.date }}</div>
            <div class="weather-main">{{ w.day_weather }}</div>
            <div class="weather-temp">{{ w.night_temp }}° ~ {{ w.day_temp }}°</div>
            <div class="weather-wind">{{ w.wind_direction }}风 {{ w.wind_power }}级</div>
          </div>
        </div>
      </section>

      <!-- 地图 -->
      <section id="map" class="card">
        <h3>行程地图</h3>
        <MapView :days="plan.days" />
      </section>

      <!-- 每日行程 -->
      <section id="itinerary">
        <DayPlanCard
          v-for="day in plan.days"
          :key="day.day_index"
          :day="day"
          @add-attraction="onAddAttraction"
          @remove-attraction="onRemoveAttraction"
        />
      </section>

    </div>
  </div>

  <div v-else class="empty">
    <p>没有找到行程数据，<a @click="$router.push('/')">返回重新规划</a></p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import type { TripPlan } from '../types'
import MapView from '../components/MapView.vue'
import DayPlanCard from '../components/DayPlanCard.vue'

const router = useRouter()
const plan = ref<TripPlan | null>(null)

onMounted(() => {
  const raw = sessionStorage.getItem('tripPlan')
  if (raw) {
    plan.value = JSON.parse(raw)
  }
})

function scrollTo(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}

function onAddAttraction(dayIndex: number, name: string) {
  if (!plan.value) return
  plan.value.days[dayIndex].attractions.push({
    name,
    address: '',
    location: { longitude: 0, latitude: 0 },
    visit_duration: 120,
    description: '',
    ticket_price: 0,
    is_indoor: false,
    typecode: '',
  })
}

function onRemoveAttraction(dayIndex: number, attrIndex: number) {
  if (!plan.value) return
  plan.value.days[dayIndex].attractions.splice(attrIndex, 1)
}

async function exportPng() {
  const { default: html2canvas } = await import('html2canvas')
  const el = document.querySelector('.main') as HTMLElement
  const canvas = await html2canvas(el, { scale: 2, useCORS: true })
  const link = document.createElement('a')
  link.download = `${plan.value?.city}行程.png`
  link.href = canvas.toDataURL('image/png')
  link.click()
}

async function exportPdf() {
  const { default: html2canvas } = await import('html2canvas')
  const { jsPDF } = await import('jspdf')
  const el = document.querySelector('.main') as HTMLElement
  const canvas = await html2canvas(el, { scale: 2, useCORS: true })
  const imgData = canvas.toDataURL('image/png')
  const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' })
  const pageWidth = pdf.internal.pageSize.getWidth()
  const pageHeight = pdf.internal.pageSize.getHeight()
  const imgWidth = pageWidth
  const imgHeight = (canvas.height * pageWidth) / canvas.width
  let y = 0
  let remaining = imgHeight
  while (remaining > 0) {
    pdf.addImage(imgData, 'PNG', 0, y, imgWidth, imgHeight)
    remaining -= pageHeight
    y -= pageHeight
    if (remaining > 0) pdf.addPage()
  }
  pdf.save(`${plan.value?.city}行程.pdf`)
}
</script>

<style scoped>
.result { display: flex; min-height: 100vh; }

.sidenav {
  position: sticky;
  top: 20px;
  width: 120px;
  height: fit-content;
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 16px 0;
  flex-shrink: 0;
}
.sidenav a {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: #555;
  text-decoration: none;
  cursor: pointer;
  transition: background .15s, color .15s;
}
.sidenav a:hover { background: #f0effe; color: #534AB7; }

.main {
  flex: 1;
  padding: 24px 32px;
  max-width: 860px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 24px;
}
.card h2 { font-size: 22px; margin-bottom: 4px; }
.card h3 { font-size: 17px; margin-bottom: 16px; }
.dates { color: #888; font-size: 14px; margin-bottom: 10px; }
.suggestion { color: #555; font-size: 14px; line-height: 1.7; }

.export-btns { display: flex; gap: 10px; margin-top: 16px; }
.export-btns button {
  padding: 7px 18px;
  border-radius: 6px;
  border: 1px solid #534AB7;
  background: transparent;
  color: #534AB7;
  cursor: pointer;
  font-size: 13px;
  transition: background .15s;
}
.export-btns button:hover { background: #f0effe; }

.budget-grid { display: flex; flex-direction: column; gap: 10px; }
.budget-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #f8f8f8;
  border-radius: 8px;
  font-size: 14px;
}
.budget-item.total {
  background: #f0effe;
  font-weight: 600;
}
.budget-value { font-weight: 500; color: #534AB7; }

.weather-row { display: flex; gap: 12px; flex-wrap: wrap; }
.weather-card {
  flex: 1;
  min-width: 100px;
  padding: 12px;
  border-radius: 8px;
  background: #f0f7ff;
  text-align: center;
  font-size: 13px;
}
.weather-date { color: #888; margin-bottom: 4px; }
.weather-main { font-weight: 500; margin-bottom: 4px; }
.weather-temp { color: #378ADD; }
.weather-wind { color: #888; font-size: 12px; margin-top: 2px; }

.empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 60vh;
  font-size: 16px;
  color: #888;
}
.empty a { color: #534AB7; cursor: pointer; }
</style>