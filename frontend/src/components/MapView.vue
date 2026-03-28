<!-- frontend/src/components/MapView.vue -->
<template>
  <div ref="mapContainer" class="map-container" />
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import type { DayPlan, MealRecommendation, Attraction } from '../types'

const props = defineProps<{ days: DayPlan[] }>()
const mapContainer = ref<HTMLElement | null>(null)

// 高德地图 JS API key（在 .env 里配置 VITE_AMAP_JS_KEY）
const AMAP_KEY = import.meta.env.VITE_AMAP_JS_KEY || ''

// 每天一个颜色
const DAY_COLORS = ['#534AB7', '#0F6E56', '#D85A30', '#185FA5', '#854F0B', '#993556', '#3B6D11']

let map: any = null

onMounted(async () => {
  await loadAmapScript()
  initMap()
})

watch(() => props.days, () => {
  if (map) {
    map.clearMap()
    plotDays()
  }
}, { deep: true })

function loadAmapScript(): Promise<void> {
  return new Promise((resolve) => {
    if ((window as any).AMap) { resolve(); return }
    const script = document.createElement('script')
    script.src = `https://webapi.amap.com/maps?v=2.0&key=${AMAP_KEY}`
    script.onload = () => resolve()
    document.head.appendChild(script)
  })
}

function initMap() {
  const AMap = (window as any).AMap
  map = new AMap.Map(mapContainer.value, {
    zoom: 12,
    resizeEnable: true,
  })
  plotDays()
}

function plotDays() {
  const AMap = (window as any).AMap
  const allPoints: any[] = []

  props.days.forEach((day: DayPlan, dayIdx: number) => {
    const color = DAY_COLORS[dayIdx % DAY_COLORS.length]
    const dayPoints: [number, number][] = []

    // 标注酒店
    if (day.hotel && day.hotel.location.longitude !== 0) {
      const { longitude: lng, latitude: lat } = day.hotel.location
      const marker = new AMap.Marker({
        position: new AMap.LngLat(lng, lat),
        title: `[住宿] ${day.hotel.name}`,
        icon: new AMap.Icon({
          size: new AMap.Size(24, 24),
          image: 'https://webapi.amap.com/theme/v1.3/markers/n/mark_b.png',
          imageSize: new AMap.Size(24, 24),
        }),
      })
      marker.setLabel({ content: `<div style="font-size:11px;white-space:nowrap">${day.hotel.name}</div>`, direction: 'top' })
      map.add(marker)
      allPoints.push(new AMap.LngLat(lng, lat))
    }

    // 标注餐厅
    day.meals.forEach((meal: MealRecommendation) => {
      if (meal.location.longitude === 0) return
      const { longitude: lng, latitude: lat } = meal.location
      const marker = new AMap.Marker({
        position: new AMap.LngLat(lng, lat),
        title: `[${meal.meal_type}] ${meal.name}`,
      })
      map.add(marker)
    })

    // 标注景点 + 编号
    day.attractions.forEach((attr: Attraction, attrIdx: number) => {
      if (attr.location.longitude === 0) return
      const { longitude: lng, latitude: lat } = attr.location

      const marker = new AMap.Marker({
        position: new AMap.LngLat(lng, lat),
        title: attr.name,
        label: {
          content: `<div style="
            background:${color};
            color:#fff;
            border-radius:50%;
            width:22px;height:22px;
            display:flex;align-items:center;justify-content:center;
            font-size:12px;font-weight:600;
          ">${attrIdx + 1}</div>`,
          direction: 'top',
        },
      })

      // 点击弹出信息窗
      const infoWindow = new AMap.InfoWindow({
        content: `
          <div style="padding:8px;min-width:180px">
            <div style="font-weight:600;margin-bottom:4px">${attr.name}</div>
            <div style="font-size:12px;color:#666">${attr.address}</div>
            <div style="font-size:12px;margin-top:4px">门票：¥${attr.ticket_price}</div>
            <div style="font-size:12px">游览：${attr.visit_duration}分钟</div>
            ${attr.is_indoor ? '<div style="font-size:11px;color:#0F6E56;margin-top:4px">室内景点</div>' : ''}
          </div>
        `,
        offset: new AMap.Pixel(0, -30),
      })
      marker.on('click', () => infoWindow.open(map, marker.getPosition()))

      map.add(marker)
      dayPoints.push([lng, lat])
      allPoints.push(new AMap.LngLat(lng, lat))
    })

    // 画路线（折线连接当天景点）
    if (dayPoints.length > 1) {
      const polyline = new AMap.Polyline({
        path: dayPoints.map(([lng, lat]) => new AMap.LngLat(lng, lat)),
        strokeColor: color,
        strokeWeight: 3,
        strokeOpacity: 0.8,
        strokeStyle: 'solid',
        lineJoin: 'round',
      })
      map.add(polyline)
    }
  })

  // 自动缩放到所有标记点
  if (allPoints.length > 0) {
    map.setFitView()
  }
}
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 480px;
  border-radius: 8px;
  overflow: hidden;
}
</style>