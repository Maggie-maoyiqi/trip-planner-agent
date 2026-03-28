<template>
  <div ref="mapContainer" class="map-container" :style="{ height: `${height}px` }" />
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import type { Attraction, DayPlan, MealRecommendation, RouteSegment } from '../types'

const props = withDefaults(defineProps<{
  days?: DayPlan[]
  day?: DayPlan
  height?: number
}>(), {
  days: () => [],
  day: undefined,
  height: 480,
})

const mapContainer = ref<HTMLElement | null>(null)
const AMAP_KEY = import.meta.env.VITE_AMAP_JS_KEY || ''
const DAY_COLORS = ['#534AB7', '#0F6E56', '#D85A30', '#185FA5', '#854F0B', '#993556', '#3B6D11']

const normalizedDays = computed(() => props.day ? [props.day] : props.days)

let map: any = null

onMounted(async () => {
  await loadAmapScript()
  initMap()
})

watch(normalizedDays, () => {
  if (!map) return
  map.clearMap()
  plotDays()
}, { deep: true })

function loadAmapScript(): Promise<void> {
  return new Promise((resolve) => {
    if ((window as any).AMap) {
      resolve()
      return
    }
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
  const rawPoints: Array<{ longitude: number; latitude: number }> = []

  normalizedDays.value.forEach((day: DayPlan, dayIdx: number) => {
    const color = DAY_COLORS[dayIdx % DAY_COLORS.length]

    if (day.hotel) {
      const { longitude, latitude } = day.hotel.location
      if (longitude && latitude) {
        addMarker(
          AMap,
          longitude,
          latitude,
          `[酒店] ${day.hotel.name}`,
          `<div class="map-label hotel-label">住</div>`,
          `酒店：${day.hotel.name}<br/>${day.hotel.address}`,
        )
        allPoints.push(new AMap.LngLat(longitude, latitude))
        rawPoints.push({ longitude, latitude })
      }
    }

    day.meals.forEach((meal: MealRecommendation) => {
      const { longitude, latitude } = meal.location
      if (!longitude || !latitude) return
      addMarker(
        AMap,
        longitude,
        latitude,
        `[${meal.meal_type}] ${meal.name}`,
        `<div class="map-label meal-label">${meal.meal_type.slice(0, 1)}</div>`,
        `${meal.meal_type}：${meal.name}<br/>人均约 ¥${meal.estimated_cost_per_person}`,
      )
      allPoints.push(new AMap.LngLat(longitude, latitude))
      rawPoints.push({ longitude, latitude })
    })

    day.attractions.forEach((attr: Attraction, index: number) => {
      const { longitude, latitude } = attr.location
      if (!longitude || !latitude) return
      addMarker(
        AMap,
        longitude,
        latitude,
        attr.name,
        `<div class="map-label attraction-label" style="background:${color}">${index + 1}</div>`,
        `${attr.name}<br/>门票 ¥${attr.ticket_price} · ${attr.visit_duration} 分钟`,
      )
      allPoints.push(new AMap.LngLat(longitude, latitude))
      rawPoints.push({ longitude, latitude })
    })

    day.route_segments.forEach((segment: RouteSegment) => {
      if (!segment.polyline.length) return
      const path = segment.polyline.map((point) => new AMap.LngLat(point.longitude, point.latitude))
      const polyline = new AMap.Polyline({
        path,
        strokeColor: color,
        strokeWeight: props.day ? 5 : 4,
        strokeOpacity: 0.85,
        showDir: true,
        lineJoin: 'round',
      })
      map.add(polyline)
    })
  })

  if (rawPoints.length) {
    const center = computeCenter(rawPoints)
    map.setCenter(new AMap.LngLat(center.longitude, center.latitude))
  }

  if (allPoints.length) {
    map.setFitView()
  }
}

function computeCenter(points: Array<{ longitude: number; latitude: number }>) {
  const total = points.reduce(
    (acc, point) => {
      acc.longitude += point.longitude
      acc.latitude += point.latitude
      return acc
    },
    { longitude: 0, latitude: 0 },
  )

  return {
    longitude: total.longitude / points.length,
    latitude: total.latitude / points.length,
  }
}

function addMarker(AMap: any, lng: number, lat: number, title: string, label: string, content: string) {
  const marker = new AMap.Marker({
    position: new AMap.LngLat(lng, lat),
    title,
    label: {
      content: label,
      direction: 'top',
    },
  })
  const infoWindow = new AMap.InfoWindow({
    content: `<div style="padding:8px 10px;font-size:12px;line-height:1.6">${content}</div>`,
    offset: new AMap.Pixel(0, -30),
  })
  marker.on('click', () => infoWindow.open(map, marker.getPosition()))
  map.add(marker)
}
</script>

<style scoped>
.map-container {
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
}
</style>

<style>
.map-label {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.18);
}

.hotel-label {
  background: #1a936f;
}

.meal-label {
  background: #ff8c42;
}

.attraction-label {
  background: #534ab7;
}
</style>
