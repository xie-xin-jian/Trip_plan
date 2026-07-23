"""高德地图MCP服务封装"""

import re
from typing import List, Dict, Any, Optional
from hello_agents.tools import MCPTool
from ..config import get_settings
from ..models.schemas import Location, POIInfo, WeatherInfo

# 全局MCP工具实例
_amap_mcp_tool = None


def get_amap_mcp_tool() -> MCPTool:
    """
    获取高德地图MCP工具实例(单例模式)
    
    Returns:
        MCPTool实例
    """
    global _amap_mcp_tool
    
    if _amap_mcp_tool is None:
        settings = get_settings()
        
        if not settings.amap_api_key:
            raise ValueError("高德地图API Key未配置,请在.env文件中设置AMAP_API_KEY")
        
        # 创建MCP工具
        _amap_mcp_tool = MCPTool(
            name="amap",
            description="高德地图服务,支持POI搜索、路线规划、天气查询等功能",
            server_command=["uvx", "amap-mcp-server"],
            env={"AMAP_MAPS_API_KEY": settings.amap_api_key},
            auto_expand=True  # 自动展开为独立工具
        )
        
        print(f"✅ 高德地图MCP工具初始化成功")
        print(f"   工具数量: {len(_amap_mcp_tool._available_tools)}")
        
        # 打印可用工具列表
        if _amap_mcp_tool._available_tools:
            print("   可用工具:")
            for tool in _amap_mcp_tool._available_tools[:5]:  # 只打印前5个
                print(f"     - {tool.get('name', 'unknown')}")
            if len(_amap_mcp_tool._available_tools) > 5:
                print(f"     ... 还有 {len(_amap_mcp_tool._available_tools) - 5} 个工具")
    
    return _amap_mcp_tool


class AmapService:
    """高德地图服务封装类"""
    
    def __init__(self):
        """初始化服务"""
        self.mcp_tool = get_amap_mcp_tool()
    
    def search_poi(self, keywords: str, city: str, citylimit: bool = True) -> List[Dict]:
        """
        搜索POI
        
        Args:
            keywords: 搜索关键词
            city: 城市
            citylimit: 是否限制在城市范围内
            
        Returns:
            POI信息列表
        """
        try:
            # 调用MCP工具
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": "maps_text_search",
                "arguments": {
                    "keywords": keywords,
                    "city": city,
                    "citylimit": str(citylimit).lower()
                }
            })
            
            # 解析结果
            print(f"POI搜索结果: {result[:500]}...")  # 打印前500字符
            
            # 尝试解析JSON
            import json
            try:
                # 从结果中提取JSON
                json_match = re.search(r'\[.*\]|\{.*\}', result, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and data.get("pois"):
                        return data["pois"]
            except:
                pass
            
            return []
            
        except Exception as e:
            print(f"❌ POI搜索失败: {str(e)}")
            return []
    
    def search_transit(self, origin: str, destination: str) -> List[Dict]:
        """
        搜索城际交通（模拟实现，返回示例数据）
        
        由于高德地图API主要提供本地路线规划，不直接支持跨城交通查询，
        此方法返回模拟的交通选项供演示使用。
        
        Args:
            origin: 出发城市
            destination: 目的城市
            
        Returns:
            交通选项列表
        """
        try:
            print(f"[交通] 搜索: {origin} -> {destination}")
            
            # 返回模拟的高铁/火车选项
            # 在实际生产环境中，应该调用12306或其他交通API
            mock_transit = [
                {
                    "transport_type": "high_speed_rail",
                    "transport_name": f"G{100 + hash(origin) % 100}",
                    "departure_time": "08:30",
                    "arrival_time": "11:45",
                    "duration": "3h15m",
                    "departure_station": f"{origin}站",
                    "arrival_station": f"{destination}站",
                    "price_economy": 200 + (hash(destination) % 200),
                    "seats_available": "有票"
                },
                {
                    "transport_type": "high_speed_rail",
                    "transport_name": f"G{200 + hash(origin) % 100}",
                    "departure_time": "14:00",
                    "arrival_time": "17:30",
                    "duration": "3h30m",
                    "departure_station": f"{origin}站",
                    "arrival_station": f"{destination}站",
                    "price_economy": 220 + (hash(destination) % 200),
                    "seats_available": "有票"
                },
                {
                    "transport_type": "train",
                    "transport_name": f"K{500 + hash(origin) % 100}",
                    "departure_time": "20:00",
                    "arrival_time": "06:00",
                    "duration": "10h",
                    "departure_station": f"{origin}站",
                    "arrival_station": f"{destination}站",
                    "price_economy": 100 + (hash(destination) % 100),
                    "seats_available": "有票"
                }
            ]
            
            print(f"[交通] 找到 {len(mock_transit)} 个交通选项")
            return mock_transit
            
        except Exception as e:
            print(f"❌ 交通搜索失败: {str(e)}")
            return []
    
    def get_weather(self, city: str) -> List[WeatherInfo]:
        """
        查询天气（实时 + 未来4天预报）

        Args:
            city: 城市名称

        Returns:
            天气信息列表
        """
        try:
            import requests
            from ..config import get_settings
            settings = get_settings()
            api_key = settings.amap_api_key
            if not api_key:
                print("❌ 未配置高德地图API Key")
                return []

            # 步骤1: 地理编码获取城市adcode
            geocode_url = "https://restapi.amap.com/v3/geocode/geo"
            geocode_params = {"key": api_key, "address": city}
            geocode_resp = requests.get(geocode_url, params=geocode_params, timeout=10)
            geocode_data = geocode_resp.json()

            adcode = None
            if geocode_data.get("status") == "1" and geocode_data.get("geocodes"):
                adcode = geocode_data["geocodes"][0].get("adcode")

            if not adcode:
                print(f"❌ 无法获取 {city} 的adcode")
                return []

            print(f"[天气] {city} adcode: {adcode}")

            # 步骤2: 查询天气预报
            weather_url = "https://restapi.amap.com/v3/weather/weatherInfo"
            weather_params = {"key": api_key, "city": adcode, "extensions": "all"}
            weather_resp = requests.get(weather_url, params=weather_params, timeout=10)
            weather_data = weather_resp.json()

            if weather_data.get("status") != "1":
                print(f"❌ 天气查询失败: {weather_data.get('info', '未知错误')}")
                return []

            forecasts = weather_data.get("forecasts", [])
            if not forecasts:
                print(f"❌ 未获取到 {city} 的天气数据")
                return []

            # 步骤3: 解析天气预报
            result: List[WeatherInfo] = []
            for forecast in forecasts[0].get("casts", []):
                date = forecast.get("date", "")
                day_weather = forecast.get("dayweather", "晴")
                night_weather = forecast.get("nightweather", "晴")

                try:
                    day_temp = int(float(forecast.get("daytemp", "25")))
                    night_temp = int(float(forecast.get("nighttemp", "15")))
                except (ValueError, TypeError):
                    day_temp = 25
                    night_temp = 15

                wind_direction = forecast.get("daywind", "无持续风向")
                wind_power = forecast.get("daypower", "3级")
                if wind_power and "级" not in wind_power:
                    wind_power = f"{wind_power}级"

                result.append(WeatherInfo(
                    date=date,
                    day_weather=day_weather,
                    night_weather=night_weather,
                    day_temp=day_temp,
                    night_temp=night_temp,
                    wind_direction=wind_direction,
                    wind_power=wind_power
                ))

            print(f"✅ 成功获取 {city} 的天气数据: {len(result)} 天")
            for w in result[:2]:
                print(f"   {w.date}: {w.day_weather} {w.day_temp}°C / {w.night_weather} {w.night_temp}°C")
            return result

        except Exception as e:
            print(f"❌ 天气查询异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def plan_route(
        self,
        origin_address: str,
        destination_address: str,
        origin_city: Optional[str] = None,
        destination_city: Optional[str] = None,
        route_type: str = "walking"
    ) -> Dict[str, Any]:
        """
        规划路线
        
        Args:
            origin_address: 起点地址
            destination_address: 终点地址
            origin_city: 起点城市
            destination_city: 终点城市
            route_type: 路线类型 (walking/driving/transit)
            
        Returns:
            路线信息
        """
        try:
            # 根据路线类型选择工具
            tool_map = {
                "walking": "maps_direction_walking_by_address",
                "driving": "maps_direction_driving_by_address",
                "transit": "maps_direction_transit_integrated_by_address"
            }
            
            tool_name = tool_map.get(route_type, "maps_direction_walking_by_address")
            
            # 构建参数
            arguments = {
                "origin_address": origin_address,
                "destination_address": destination_address
            }
            
            # 公共交通需要城市参数
            if route_type == "transit":
                if origin_city:
                    arguments["origin_city"] = origin_city
                if destination_city:
                    arguments["destination_city"] = destination_city
            else:
                # 其他路线类型也可以提供城市参数提高准确性
                if origin_city:
                    arguments["origin_city"] = origin_city
                if destination_city:
                    arguments["destination_city"] = destination_city
            
            # 调用MCP工具
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": tool_name,
                "arguments": arguments
            })
            
            print(f"路线规划结果: {result[:200]}...")
            
            # TODO: 解析实际的路线数据
            return {}
            
        except Exception as e:
            print(f"❌ 路线规划失败: {str(e)}")
            return {}
    
    def geocode(self, address: str, city: Optional[str] = None) -> Optional[Location]:
        """
        地理编码(地址转坐标)

        Args:
            address: 地址
            city: 城市

        Returns:
            经纬度坐标
        """
        try:
            arguments = {"address": address}
            if city:
                arguments["city"] = city

            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": "maps_geo",
                "arguments": arguments
            })

            print(f"地理编码结果: {result[:200]}...")

            # TODO: 解析实际的坐标数据
            return None

        except Exception as e:
            print(f"❌ 地理编码失败: {str(e)}")
            return None

    def get_poi_detail(self, poi_id: str) -> Dict[str, Any]:
        """
        获取POI详情

        Args:
            poi_id: POI ID

        Returns:
            POI详情信息
        """
        try:
            result = self.mcp_tool.run({
                "action": "call_tool",
                "tool_name": "maps_search_detail",
                "arguments": {
                    "id": poi_id
                }
            })

            print(f"POI详情结果: {result[:200]}...")

            # 解析结果并提取图片
            import json
            import re

            # 尝试从结果中提取JSON
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data

            return {"raw": result}

        except Exception as e:
            print(f"❌ 获取POI详情失败: {str(e)}")
            return {}


# 创建全局服务实例
_amap_service = None


def get_amap_service() -> AmapService:
    """获取高德地图服务实例(单例模式)"""
    global _amap_service
    
    if _amap_service is None:
        _amap_service = AmapService()
    
    return _amap_service

