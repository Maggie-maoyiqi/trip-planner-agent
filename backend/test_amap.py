# backend/test_amap.py
import httpx
import asyncio

async def test_amap_key():
    """测试高德地图 API Key 是否有效"""
    
    # 替换成你的 API Key（就是 .env 里填的那个）
    api_key = "4050ca7113fc39bfaf4d66fc80be1b93"
    
    # 测试最简单的接口 - IP定位
    url = "https://restapi.amap.com/v3/ip"
    params = {
        "key": api_key,
        "output": "json"
    }
    
    print("正在测试高德地图 API Key...")
    print(f"使用 Key: {api_key}")
    print("-" * 50)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        data = response.json()
        
        print(f"返回状态: {data.get('status')}")
        print(f"返回信息: {data.get('info')}")
        print(f"返回数据: {data}")
        
        if data.get('status') == '1':
            print("\n✅ API Key 有效！")
            print(f"IP位置: {data.get('province')} {data.get('city')}")
        else:
            print(f"\n❌ API Key 无效")
            print(f"错误码 {data.get('infocode')}: {data.get('info')}")
            
            # 常见错误码说明
            if data.get('infocode') == '10009':
                print("\n错误码 10009 说明：")
                print("1. Key 类型不正确（可能创建时选错了类型）")
                print("2. Key 未开通 Web 服务")
                print("3. Key 已过期或被禁用")
                print("4. Key 需要绑定 IP 白名单")

if __name__ == "__main__":
    asyncio.run(test_amap_key())