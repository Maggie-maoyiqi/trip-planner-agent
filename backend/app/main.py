from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="一个基于AI的旅行规划应用，提供个性化的旅行建议和行程规划服务。",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/")
async def root():
    """根路径，用于测试服务是否正常运行"""
    return {
        "message": f"欢迎使用 {settings.app_name}！",
        "version": settings.app_version,
        "status": "running"
    }
@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}