# 本地假天气服务示例，不依赖外部 API。


def get_fake_weather(city: str) -> dict:
    normalized_city = city.strip().lower()
    alias = {
        "北京": "beijing",
        "上海": "shanghai",
        "广州": "guangzhou",
        "深圳": "shenzhen",
    }
    normalized_city = alias.get(normalized_city, normalized_city)

    weather_data = {
        "beijing": {"city": "北京", "condition": "晴", "temperature_c": 26, "humidity": 35},
        "shanghai": {"city": "上海", "condition": "多云", "temperature_c": 24, "humidity": 58},
        "guangzhou": {"city": "广州", "condition": "小雨", "temperature_c": 29, "humidity": 78},
        "shenzhen": {"city": "深圳", "condition": "阵雨", "temperature_c": 28, "humidity": 74},
    }

    return weather_data.get(
        normalized_city,
        {"city": city.strip(), "condition": "未知", "temperature_c": 25, "humidity": 50},
    )
