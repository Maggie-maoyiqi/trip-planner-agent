<template>
    <div class="result-container">
      <div class="result-header">
        <h1>{{ tripPlan?.city }} 旅行计划</h1>
        <p>{{ tripPlan?.start_date }} 至 {{ tripPlan?.end_date }}</p>
        <button @click="goBack" class="back-btn">← 返回</button>
      </div>
  
      <div class="result-content">
        <!-- 总体建议 -->
        <div class="section">
          <h2>💡 总体建议</h2>
          <p>{{ tripPlan?.overall_suggestions }}</p>
        </div>
  
        <!-- 预算信息 -->
        <div v-if="tripPlan?.budget" class="section">
          <h2>💰 预算明细</h2>
          <div class="budget-grid">
            <div class="budget-item">
              <span>景点门票</span>
              <strong>{{ tripPlan.budget.total_attractions }} 元</strong>
            </div>
            <div class="budget-item">
              <span>酒店住宿</span>
              <strong>{{ tripPlan.budget.total_hotels }} 元</strong>
            </div>
            <div class="budget-item">
              <span>餐饮费用</span>
              <strong>{{ tripPlan.budget.total_meals }} 元</strong>
            </div>
            <div class="budget-item">
              <span>交通费用</span>
              <strong>{{ tripPlan.budget.total_transportation }} 元</strong>
            </div>
            <div class="budget-total">
              <span>总计</span>
              <strong>{{ tripPlan.budget.total }} 元</strong>
            </div>
          </div>
        </div>
  
        <!-- 天气信息 -->
        <div v-if="tripPlan?.weather_info?.length" class="section">
          <h2>🌤️ 天气信息</h2>
          <div class="weather-grid">
            <div v-for="weather in tripPlan.weather_info" :key="weather.date" class="weather-card">
              <div class="weather-date">{{ weather.date }}</div>
              <div>白天：{{ weather.day_weather }} {{ weather.day_temp }}°C</div>
              <div>夜间：{{ weather.night_weather }} {{ weather.night_temp }}°C</div>
              <div>{{ weather.wind_direction }} {{ weather.wind_power }}</div>
            </div>
          </div>
        </div>
  
        <!-- 每日行程 -->
        <div v-for="day in tripPlan?.days" :key="day.day_index" class="section">
          <h2>📅 {{ day.date }}</h2>
          <p><strong>交通：</strong>{{ day.transportation }}</p>
          <p><strong>住宿：</strong>{{ day.accommodation }}</p>
          
          <h3>景点安排</h3>
          <div class="attractions-list">
            <div v-for="(attraction, idx) in day.attractions" :key="idx" class="attraction-card">
              <div class="attraction-number">{{ idx + 1 }}</div>
              <div class="attraction-info">
                <div class="attraction-name">{{ attraction.name }}</div>
                <div class="attraction-address">{{ attraction.address }}</div>
                <div class="attraction-duration">建议游览：{{ attraction.visit_duration }} 分钟</div>
                <div class="attraction-price">门票：{{ attraction.ticket_price }} 元</div>
                <p class="attraction-desc">{{ attraction.description }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref, onMounted } from 'vue';
  import { useRouter } from 'vue-router';
  import type { TripPlan } from '../types';
  
  const router = useRouter();
  const tripPlan = ref<TripPlan | null>(null);
  
  onMounted(() => {
    // 从路由 state 中获取数据
    const state = history.state;
    if (state && state.tripPlan) {
      tripPlan.value = state.tripPlan;
    } else {
      // 如果没有数据，返回首页
      router.push('/');
    }
  });
  
  const goBack = () => {
    router.push('/');
  };
  </script>
  
  <style scoped>
  .result-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 40px 20px;
  }
  
  .result-header {
    text-align: center;
    margin-bottom: 40px;
    position: relative;
  }
  
  .result-header h1 {
    font-size: 2rem;
    color: #333;
    margin-bottom: 10px;
  }
  
  .back-btn {
    position: absolute;
    left: 0;
    top: 0;
    padding: 8px 16px;
    background: #f0f0f0;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
  }
  
  .back-btn:hover {
    background: #e0e0e0;
  }
  
  .section {
    background: white;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
  
  .section h2 {
    margin-top: 0;
    margin-bottom: 20px;
    color: #667eea;
  }
  
  .budget-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  
  .budget-item, .budget-total {
    display: flex;
    justify-content: space-between;
    padding: 12px;
    background: #f8f9fa;
    border-radius: 8px;
  }
  
  .budget-total {
    grid-column: span 2;
    background: #667eea;
    color: white;
    font-size: 18px;
  }
  
  .weather-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
  }
  
  .weather-card {
    padding: 16px;
    background: #f8f9fa;
    border-radius: 8px;
    text-align: center;
  }
  
  .weather-date {
    font-weight: bold;
    font-size: 18px;
    margin-bottom: 8px;
  }
  
  .attractions-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  .attraction-card {
    display: flex;
    gap: 16px;
    padding: 16px;
    background: #f8f9fa;
    border-radius: 8px;
  }
  
  .attraction-number {
    width: 40px;
    height: 40px;
    background: #667eea;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 18px;
    flex-shrink: 0;
  }
  
  .attraction-info {
    flex: 1;
  }
  
  .attraction-name {
    font-size: 18px;
    font-weight: bold;
    margin-bottom: 8px;
  }
  
  .attraction-address {
    color: #666;
    font-size: 14px;
    margin-bottom: 4px;
  }
  
  .attraction-duration, .attraction-price {
    font-size: 14px;
    color: #888;
    margin-bottom: 4px;
  }
  
  .attraction-desc {
    margin-top: 8px;
    color: #555;
  }
  </style>