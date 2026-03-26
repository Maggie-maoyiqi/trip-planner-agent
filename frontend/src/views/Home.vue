<template>
    <div class="home-container">
      <div class="page-header">
        <h1 class="page-title">✈️ 智能旅行助手</h1>
        <p class="page-subtitle">基于AI的个性化旅行规划</p>
      </div>
      
      <div class="form-card">
        <form @submit.prevent="handleSubmit">
          <!-- 目的地城市 -->
          <div class="form-item">
            <label>目的地城市 *</label>
            <input 
              v-model="formData.city" 
              type="text" 
              placeholder="如：北京、上海、澳门"
              required
            />
          </div>
  
          <!-- 日期选择 -->
          <div class="form-row">
            <div class="form-item">
              <label>开始日期 *</label>
              <input v-model="formData.start_date" type="date" required />
            </div>
            <div class="form-item">
              <label>结束日期 *</label>
              <input v-model="formData.end_date" type="date" required />
            </div>
          </div>
  
          <!-- 旅行天数 -->
          <div class="form-item">
            <label>旅行天数</label>
            <input 
              v-model.number="formData.days" 
              type="number" 
              min="1" 
              max="30"
            />
          </div>
  
          <!-- 旅行偏好 -->
          <div class="form-item">
            <label>旅行偏好</label>
            <select v-model="formData.preferences">
              <option value="历史文化">历史文化</option>
              <option value="自然风光">自然风光</option>
              <option value="美食购物">美食购物</option>
              <option value="休闲度假">休闲度假</option>
            </select>
          </div>
  
          <!-- 预算等级 -->
          <div class="form-item">
            <label>预算等级</label>
            <select v-model="formData.budget">
              <option value="经济">经济型</option>
              <option value="中等">中等</option>
              <option value="豪华">豪华型</option>
            </select>
          </div>
  
          <!-- 交通方式 -->
          <div class="form-item">
            <label>交通方式</label>
            <select v-model="formData.transportation">
              <option value="公共交通">公共交通</option>
              <option value="出租车">出租车</option>
              <option value="自驾">自驾</option>
            </select>
          </div>
  
          <!-- 住宿类型 -->
          <div class="form-item">
            <label>住宿类型</label>
            <select v-model="formData.accommodation">
              <option value="经济型酒店">经济型酒店</option>
              <option value="舒适型酒店">舒适型酒店</option>
              <option value="豪华酒店">豪华酒店</option>
              <option value="民宿">民宿</option>
            </select>
          </div>
  
          <!-- 提交按钮 -->
          <button type="submit" :disabled="loading" class="submit-btn">
            {{ loading ? '规划中...' : '开始规划' }}
          </button>
  
          <!-- 加载进度条 -->
          <div v-if="loading" class="loading-section">
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: loadingProgress + '%' }"></div>
            </div>
            <p class="loading-status">{{ loadingStatus }}</p>
          </div>
        </form>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { ref } from 'vue';
  import { useRouter } from 'vue-router';
  import { generateTripPlan } from '../services/api';
  import type { TripPlanRequest } from '../types';
  
  const router = useRouter();
  
  // 表单数据
  const formData = ref<TripPlanRequest>({
    city: '',
    start_date: '',
    end_date: '',
    days: 3,
    preferences: '历史文化',
    budget: '中等',
    transportation: '公共交通',
    accommodation: '经济型酒店'
  });
  
  // 加载状态
  const loading = ref(false);
  const loadingProgress = ref(0);
  const loadingStatus = ref('');
  
  // 提交表单
  const handleSubmit = async () => {
    loading.value = true;
    loadingProgress.value = 0;
    
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (loadingProgress.value < 90) {
        loadingProgress.value += 10;
        if (loadingProgress.value <= 30) {
          loadingStatus.value = '🔍 正在搜索景点...';
        } else if (loadingProgress.value <= 50) {
          loadingStatus.value = '🌤️ 正在查询天气...';
        } else if (loadingProgress.value <= 70) {
          loadingStatus.value = '🏨 正在推荐酒店...';
        } else {
          loadingStatus.value = '📋 正在生成行程计划...';
        }
      }
    }, 500);
    
    try {
      const response = await generateTripPlan(formData.value);
      clearInterval(progressInterval);
      loadingProgress.value = 100;
      loadingStatus.value = '✅ 完成！';
      
      // 跳转到结果页面
      setTimeout(() => {
        router.push({ name: 'result', state: { tripPlan: response } });
      }, 500);
      
    } catch (error) {
      clearInterval(progressInterval);
      alert('生成计划失败，请重试');
      console.error(error);
      loading.value = false;
    }
  };
  </script>
  
  <style scoped>
  .home-container {
    min-height: 100vh;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 40px 20px;
  }
  
  .page-header {
    text-align: center;
    color: white;
    margin-bottom: 40px;
  }
  
  .page-title {
    font-size: 2.5rem;
    margin-bottom: 10px;
  }
  
  .page-subtitle {
    font-size: 1.1rem;
    opacity: 0.9;
  }
  
  .form-card {
    max-width: 600px;
    margin: 0 auto;
    background: white;
    border-radius: 16px;
    padding: 40px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.1);
  }
  
  .form-item {
    margin-bottom: 20px;
  }
  
  .form-item label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: #333;
  }
  
  .form-item input,
  .form-item select {
    width: 100%;
    padding: 10px 12px;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 16px;
    transition: border-color 0.3s;
  }
  
  .form-item input:focus,
  .form-item select:focus {
    outline: none;
    border-color: #667eea;
  }
  
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
  }
  
  .submit-btn {
    width: 100%;
    padding: 12px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 18px;
    font-weight: 500;
    cursor: pointer;
    transition: transform 0.2s;
  }
  
  .submit-btn:hover:not(:disabled) {
    transform: translateY(-2px);
  }
  
  .submit-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .loading-section {
    margin-top: 20px;
  }
  
  .progress-bar {
    width: 100%;
    height: 8px;
    background: #f0f0f0;
    border-radius: 4px;
    overflow: hidden;
  }
  
  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #667eea, #764ba2);
    transition: width 0.3s;
  }
  
  .loading-status {
    text-align: center;
    margin-top: 12px;
    color: #666;
  }
  </style>