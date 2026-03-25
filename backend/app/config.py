import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    amap_api_key: str = os.getenv("AMAP_API_KEY")
    unsplash_access_key: str = os.getenv("UNSPLASH_ACCESS_KEY", "")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    app_name: str = "Travel Planner"
    app_version: str = "1.0.0"

settings = Settings()

# 验证必要的配置
def validate_settings():
    """检查必要的API密钥是否已配置"""
    errors = []
    if not settings.amap_api_key:
        errors.append("请在.env文件中设置 AMAP_API_KEY")
    if not settings.deepseek_api_key:
        errors.append("请在.env文件中设置 DEEPSEEK_API_KEY")
    
    if errors:
        raise ValueError("\n".join(errors))

# 调用验证
validate_settings()