<!-- frontend/src/components/DayPlanCard.vue -->
<template>
    <div class="day-card card">
  
      <!-- 天标题 + 天气提示 -->
      <div class="day-header">
        <h3>{{ day.date }}</h3>
        <span v-if="day.weather_note" class="weather-badge">{{ day.weather_note }}</span>
      </div>
      <p class="day-desc">{{ day.description }}</p>
  
      <!-- 酒店 -->
      <div v-if="day.hotel" class="section">
        <div class="section-title">今晚住宿</div>
        <div class="hotel-row">
          <img v-if="day.hotel.image_url" :src="day.hotel.image_url" class="thumb" />
          <div>
            <div class="item-name">{{ day.hotel.name }}</div>
            <div class="item-sub">{{ day.hotel.address }}</div>
            <div class="item-sub">
              ¥{{ day.hotel.price_per_night }}/晚 · 距景点 {{ day.hotel.dist_to_attractions_km }} km
            </div>
          </div>
        </div>
      </div>
  
      <!-- 景点列表 -->
      <div class="section">
        <div class="section-title">景点安排</div>
        <div
          v-for="(attr, idx) in day.attractions"
          :key="idx"
          class="attraction-row"
        >
          <img v-if="attr.image_url" :src="attr.image_url" class="thumb" />
          <div class="attraction-info">
            <div class="item-name">
              {{ attr.name }}
              <span v-if="attr.is_indoor" class="badge indoor">室内</span>
            </div>
            <div class="item-sub">{{ attr.address }}</div>
            <div class="item-sub">
              门票 ¥{{ attr.ticket_price }} · 建议游览 {{ attr.visit_duration }} 分钟
            </div>
            <div class="item-desc">{{ attr.description }}</div>
          </div>
          <button class="remove-btn" @click="$emit('remove-attraction', day.day_index, idx)">
            删除
          </button>
        </div>
  
        <!-- 添加景点 -->
        <div class="add-row">
          <input
            v-model="newAttrName"
            placeholder="添加景点名称..."
            @keyup.enter="addAttraction"
          />
          <button @click="addAttraction">添加</button>
        </div>
      </div>
  
      <!-- 餐厅推荐 -->
      <div class="section">
        <div class="section-title">餐饮推荐</div>
        <div v-for="meal in day.meals" :key="meal.meal_type" class="meal-row">
          <span class="meal-type">{{ meal.meal_type }}</span>
          <div>
            <div class="item-name">{{ meal.name }}</div>
            <div class="item-sub">{{ meal.suggestion }}</div>
          </div>
        </div>
      </div>
  
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue'
  import type { DayPlan } from '../types'
  
  const props = defineProps<{ day: DayPlan }>()
  const emit = defineEmits<{
    (e: 'add-attraction', dayIndex: number, name: string): void
    (e: 'remove-attraction', dayIndex: number, attrIndex: number): void
  }>()
  
  const newAttrName = ref('')
  
  function addAttraction() {
    if (!newAttrName.value.trim()) return
    emit('add-attraction', props.day.day_index, newAttrName.value.trim())
    newAttrName.value = ''
  }
  </script>
  
  <style scoped>
  .day-card {
    background: #fff;
    border: 1px solid #e8e8e8;
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 20px;
  }
  .day-header { display: flex; align-items: center; gap: 12px; margin-bottom: 6px; }
  .day-header h3 { font-size: 18px; }
  .weather-badge {
    font-size: 12px;
    padding: 3px 8px;
    border-radius: 12px;
    background: #fff3cd;
    color: #856404;
  }
  .day-desc { font-size: 13px; color: #888; margin-bottom: 16px; }
  
  .section { margin-bottom: 20px; }
  .section-title {
    font-size: 13px;
    font-weight: 600;
    color: #534AB7;
    margin-bottom: 10px;
    text-transform: uppercase;
    letter-spacing: .5px;
  }
  
  .hotel-row, .attraction-row {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    padding: 10px;
    background: #f8f8f8;
    border-radius: 8px;
    margin-bottom: 8px;
  }
  .attraction-row { position: relative; }
  .attraction-info { flex: 1; }
  
  .thumb {
    width: 64px;
    height: 64px;
    object-fit: cover;
    border-radius: 6px;
    flex-shrink: 0;
  }
  .item-name { font-size: 14px; font-weight: 500; margin-bottom: 3px; }
  .item-sub { font-size: 12px; color: #888; margin-bottom: 2px; }
  .item-desc { font-size: 12px; color: #aaa; margin-top: 4px; }
  
  .badge {
    font-size: 11px;
    padding: 2px 6px;
    border-radius: 4px;
    margin-left: 6px;
    vertical-align: middle;
  }
  .indoor { background: #e1f5ee; color: #0f6e56; }
  
  .remove-btn {
    padding: 4px 10px;
    border-radius: 6px;
    border: 1px solid #f09595;
    background: transparent;
    color: #a32d2d;
    cursor: pointer;
    font-size: 12px;
    flex-shrink: 0;
  }
  .remove-btn:hover { background: #fcebeb; }
  
  .add-row { display: flex; gap: 8px; margin-top: 8px; }
  .add-row input {
    flex: 1;
    padding: 7px 12px;
    border: 1px solid #ddd;
    border-radius: 6px;
    font-size: 13px;
    outline: none;
  }
  .add-row input:focus { border-color: #534AB7; }
  .add-row button {
    padding: 7px 16px;
    background: #534AB7;
    color: #fff;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
  }
  
  .meal-row {
    display: flex;
    gap: 12px;
    align-items: flex-start;
    padding: 8px 10px;
    background: #f8f8f8;
    border-radius: 8px;
    margin-bottom: 6px;
  }
  .meal-type {
    width: 36px;
    font-size: 12px;
    color: #534AB7;
    font-weight: 600;
    flex-shrink: 0;
    padding-top: 2px;
  }
  </style>