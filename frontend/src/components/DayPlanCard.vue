<template>
  <div class="day-card card">
    <div class="day-header">
      <div>
        <h3>{{ day.date }}</h3>
        <p class="day-desc">{{ day.description }}</p>
      </div>
      <span v-if="day.weather_note" class="weather-badge">{{ day.weather_note }}</span>
    </div>

    <div class="tips-row">
      <div class="tip-card">
        <div class="tip-title">穿衣建议</div>
        <div class="tip-body">{{ day.clothing_recommendation || '按当天温度灵活增减衣物。' }}</div>
      </div>
      <div v-if="day.hotel" class="tip-card">
        <div class="tip-title">今晚住宿</div>
        <div class="tip-body">{{ day.hotel.name }} · ¥{{ day.hotel.price_per_night }}/晚</div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">当天地图</div>
      <MapView :day="day" :height="340" />
    </div>

    <div class="section">
      <div class="section-title">时段安排</div>
      <div v-for="(item, index) in day.schedule" :key="`${item.time_slot}-${index}`" class="schedule-row">
        <div class="schedule-time">
          <div>{{ item.time_slot }}</div>
          <small>{{ item.start_time }} - {{ item.end_time }}</small>
        </div>
        <div class="schedule-main">
          <div class="item-name">{{ item.title }}</div>
          <div class="item-sub">
            {{ item.note || '按当前位置就近衔接下一站。' }}
          </div>
        </div>
        <div class="schedule-cost" v-if="item.estimated_cost">¥{{ item.estimated_cost }}</div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">景点安排</div>
      <div v-for="(attr, idx) in day.attractions" :key="idx" class="attraction-row">
        <img v-if="attr.image_url" :src="attr.image_url" class="thumb" />
        <div class="attraction-info">
          <div class="item-name">
            {{ idx + 1 }}. {{ attr.name }}
            <span v-if="attr.is_indoor" class="badge indoor">室内</span>
          </div>
          <div class="item-sub">{{ attr.address }}</div>
          <div class="item-sub">
            门票 ¥{{ attr.ticket_price }} · 建议游览 {{ attr.visit_duration }} 分钟
            <span v-if="attr.best_visit_time"> · 适合 {{ attr.best_visit_time }}</span>
          </div>
          <div class="item-desc">{{ attr.llm_reason || attr.description }}</div>
        </div>
        <button class="remove-btn" @click="$emit('remove-attraction', day.day_index, idx)">
          删除
        </button>
      </div>

      <div class="add-row">
        <input v-model="newAttrName" placeholder="添加景点名称..." @keyup.enter="addAttraction" />
        <button @click="addAttraction">添加</button>
      </div>
    </div>

    <div class="section">
      <div class="section-title">餐饮推荐</div>
      <div v-for="meal in day.meals" :key="meal.meal_type" class="meal-row">
        <span class="meal-type">{{ meal.meal_type }}</span>
        <div class="meal-main">
          <div class="item-name">{{ meal.name }}</div>
          <div class="item-sub">{{ meal.suggestion }}</div>
        </div>
        <div class="meal-cost">¥{{ meal.estimated_cost_per_person }}/人</div>
      </div>
    </div>

    <div class="section" v-if="day.route_segments.length">
      <div class="section-title">交通衔接</div>
      <div v-for="(segment, index) in day.route_segments" :key="index" class="route-row">
        <div class="route-main">
          <div class="item-name">{{ segment.from_name }} → {{ segment.to_name }}</div>
          <div class="item-sub">{{ segment.mode }} · {{ segment.duration_minutes }} 分钟 · {{ segment.distance_km }} km</div>
          <div class="item-desc">{{ segment.instruction || '已通过高德规划通勤路线。' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { DayPlan } from '../types'
import MapView from './MapView.vue'

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
  border-radius: 18px;
  padding: 24px;
  margin-bottom: 20px;
}

.day-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 18px;
}

.day-header h3 {
  font-size: 21px;
  margin-bottom: 6px;
}

.day-desc {
  font-size: 14px;
  color: #61707d;
  line-height: 1.7;
}

.weather-badge {
  font-size: 12px;
  padding: 7px 10px;
  border-radius: 999px;
  background: #fff3cd;
  color: #856404;
  flex-shrink: 0;
}

.tips-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.tip-card {
  background: linear-gradient(135deg, #f6f8fc, #eef4ff);
  border-radius: 14px;
  padding: 14px 16px;
}

.tip-title {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #5e6d7c;
  margin-bottom: 6px;
}

.tip-body {
  font-size: 14px;
  line-height: 1.7;
  color: #203040;
}

.section {
  margin-bottom: 22px;
}

.section-title {
  font-size: 13px;
  font-weight: 700;
  color: #534ab7;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.schedule-row,
.hotel-row,
.attraction-row,
.meal-row,
.route-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px;
  background: #f8fafc;
  border-radius: 12px;
  margin-bottom: 8px;
}

.schedule-time {
  width: 92px;
  flex-shrink: 0;
  font-weight: 700;
  color: #203040;
}

.schedule-time small {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  color: #7b8794;
}

.schedule-main,
.attraction-info,
.meal-main,
.route-main {
  flex: 1;
}

.schedule-cost,
.meal-cost {
  color: #0f6e56;
  font-weight: 700;
  white-space: nowrap;
}

.thumb {
  width: 72px;
  height: 72px;
  object-fit: cover;
  border-radius: 10px;
  flex-shrink: 0;
}

.item-name {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 4px;
  color: #203040;
}

.item-sub {
  font-size: 12px;
  color: #62717f;
  line-height: 1.6;
}

.item-desc {
  font-size: 12px;
  color: #7b8794;
  line-height: 1.7;
  margin-top: 4px;
}

.badge {
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 999px;
  margin-left: 6px;
  vertical-align: middle;
}

.indoor {
  background: #dff6ed;
  color: #0f6e56;
}

.remove-btn {
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid #f3b1b1;
  background: transparent;
  color: #a32d2d;
  cursor: pointer;
  font-size: 12px;
  flex-shrink: 0;
}

.add-row {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.add-row input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #d7dde4;
  border-radius: 10px;
  font-size: 13px;
  outline: none;
}

.add-row button {
  padding: 10px 16px;
  background: #534ab7;
  color: #fff;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 13px;
}

.meal-type {
  width: 44px;
  font-size: 12px;
  color: #534ab7;
  font-weight: 700;
  flex-shrink: 0;
  padding-top: 2px;
}

@media (max-width: 768px) {
  .tips-row {
    grid-template-columns: 1fr;
  }

  .day-header,
  .schedule-row,
  .attraction-row,
  .meal-row,
  .route-row {
    flex-direction: column;
  }

  .schedule-time {
    width: auto;
  }
}
</style>
