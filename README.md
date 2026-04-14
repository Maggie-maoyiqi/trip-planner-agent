# 🗺️ Trip Planner Agent —— AI 智能旅行规划助手

基于 AI Agent 的旅行规划应用，通过多个专业智能体协同工作，为用户生成个性化的旅行行程，涵盖景点推荐、酒店、餐饮、天气等多维度信息。

---

## 📌 当前已知问题

1. 酒店、交通、饮食缺乏具体推荐，导致预算估算不准确
2. 景点门票数据存在虚假信息
3. Agent 智能路线规划尚未实现
4. 导出 PDF、地图位置标注、行程编辑等功能尚未完成
5. 旅行选项较少（如旅行风格、酒店风格），灵活分天规划有待完善

---

## ✨ 功能特性

- **多 Agent 协同**：规划 Agent、景点 Agent、酒店 Agent、餐厅 Agent、天气 Agent 分工协作
- **个性化行程**：根据目的地、出行天数、预算、旅行风格生成定制化行程
- **实时地图集成**：接入高德地图 API，展示景点、酒店位置
- **图片展示**：通过 Unsplash API 自动获取景点配图
- **天气查询**：出行前获取目的地天气信息
- **前后端分离**：Vue 3 前端 + FastAPI 后端

---

## 🛠️ 技术栈

### 后端
| 技术 | 说明 |
|------|------|
| FastAPI | 高性能 Python Web 框架 |
| LangChain | AI Agent 编排框架 |
| DeepSeek API | 大语言模型（LLM）服务 |
| 高德地图 API | 地理位置与地图服务 |
| Unsplash API | 景点图片服务 |
| Uvicorn | ASGI 服务器 |

### 前端
| 技术 | 说明 |
|------|------|
| Vue 3 | 前端框架 |
| TypeScript | 类型安全 |
| Vite | 构建工具 |
| Vue Router | 前端路由 |

---

## 📁 项目结构

```
trip-planner-agent/
├── backend/
│   ├── app/
│   │   ├── agents/              # AI Agent 模块
│   │   │   ├── attraction_agent.py   # 景点推荐 Agent
│   │   │   ├── hotel_agent.py        # 酒店推荐 Agent
│   │   │   ├── planner_agent.py      # 行程规划 Agent
│   │   │   ├── restaurant_agent.py   # 餐厅推荐 Agent
│   │   │   ├── trip_planner.py       # 旅行规划主控
│   │   │   └── weather_agent.py      # 天气查询 Agent
│   │   ├── api/
│   │   │   └── routes/          # API 路由
│   │   ├── services/            # 外部服务封装
│   │   │   ├── amap_service.py       # 高德地图服务
│   │   │   ├── llm_service.py        # LLM 服务
│   │   │   └── unsplash_service.py   # Unsplash 图片服务
│   │   ├── models/              # 数据模型
│   │   ├── config.py            # 应用配置
│   │   └── main.py              # 应用入口
│   ├── requirements.txt
│   └── run.py
└── frontend/
    ├── src/
    │   ├── views/
    │   │   ├── Home.vue         # 首页（行程输入）
    │   │   └── Result.vue       # 行程结果展示
    │   ├── components/
    │   │   ├── DayPlanCard.vue  # 每日行程卡片
    │   │   └── MapView.vue      # 地图组件
    │   ├── services/            # 前端 API 调用
    │   ├── types/               # TypeScript 类型定义
    │   └── router/              # 路由配置
    ├── package.json
    └── vite.config.ts
```

---

## 🚀 快速开始

### 前置条件

- Python 3.10+
- Node.js 18+
- 高德地图 API Key（[申请地址](https://lbs.amap.com/)）
- DeepSeek API Key（[申请地址](https://platform.deepseek.com/)）
- Unsplash Access Key（可选，[申请地址](https://unsplash.com/developers)）

### 1. 克隆项目

```bash
git clone <仓库地址>
cd trip-planner-agent
```

### 2. 配置环境变量

在 `backend/` 目录下创建 `.env` 文件：

```env
AMAP_API_KEY=你的高德地图API密钥
DEEPSEEK_API_KEY=你的DeepSeek API密钥
UNSPLASH_ACCESS_KEY=你的Unsplash密钥（可选）
```

### 3. 启动后端

```bash
cd backend
pip install -r requirements.txt
python run.py
```

后端默认运行在 `http://localhost:8000`

### 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`

---

## 📡 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 服务状态检查 |
| GET | `/health` | 健康检查 |
| POST | `/api/trip/plan` | 生成旅行计划 |

**请求示例（生成旅行计划）：**

```json
{
  "destination": "成都",
  "days": 3,
  "budget": 3000,
  "travel_style": "休闲"
}
```

---

## 🔧 开发计划

- [ ] 完善酒店、餐饮的具体推荐与预算计算
- [ ] 修复景点门票数据准确性问题
- [ ] 实现 Agent 智能路线优化
- [ ] 支持导出 PDF 行程单
- [ ] 集成地图位置标注与导航
- [ ] 支持行程在线编辑
- [ ] 增加旅行风格、酒店偏好等更多自定义选项
- [ ] 灵活的多日行程分配

---

## 📄 许可证

本项目仅供学习与研究使用。
