# backend/app/services/unsplash_service.py
import httpx
from typing import List, Dict, Any, Optional
from app.config import settings

class UnsplashService:
    """Unsplash 图片服务"""
    
    def __init__(self):
        self.access_key = settings.unsplash_access_key
        self.base_url = "https://api.unsplash.com"
    
    async def search_photos(self, query: str, per_page: int = 10) -> List[Dict[str, Any]]:
        """
        搜索图片
        
        Args:
            query: 搜索关键词
            per_page: 返回图片数量
        
        Returns:
            图片信息列表
        """
        if not self.access_key:
            return []
        
        url = f"{self.base_url}/search/photos"
        headers = {
            "Authorization": f"Client-ID {self.access_key}"
        }
        params = {
            "query": query,
            "per_page": per_page
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                data = response.json()
                
                results = data.get("results", [])
                photos = []
                for result in results:
                    photos.append({
                        "url": result.get("urls", {}).get("regular", ""),
                        "description": result.get("description", "") or result.get("alt_description", ""),
                        "photographer": result.get("user", {}).get("name", ""),
                        "photographer_url": result.get("user", {}).get("links", {}).get("html", "")
                    })
                
                return photos
        except Exception as e:
            print(f"Unsplash 搜索失败: {e}")
            return []
    
    async def get_photo_url(self, query: str) -> Optional[str]:
        """获取单张图片 URL"""
        photos = await self.search_photos(query, per_page=1)
        return photos[0].get("url") if photos else None

# 创建全局实例
unsplash_service = UnsplashService()