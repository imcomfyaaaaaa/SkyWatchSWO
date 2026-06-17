import requests
import json
from config.settings import CITIES

def get_eccc_alerts(city_name):
    """
    Fetches active weather alerts for Ontario and checks if the city is in the affected area.
    """
    url = "https://api.weather.gc.ca/collections/weather-alerts/items?f=json&province=ON"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            for feat in data.get("features", []):
                props = feat.get("properties", {})
                area = props.get("feature_name_en", "").lower()
                status = props.get("status_en", "").lower()
                
                # Check if the alert is active and targets our city
                if status == "issued" and city_name.lower() in area:
                    return {
                        "alert_name": props.get("alert_name_en", "Severe Weather Alert").upper(),
                        "alert_text": props.get("alert_text_en", "")
                    }
    except Exception as e:
        print(f"Failed to fetch ECCC alerts: {e}")
    return None

def get_weather_data(city_name):
    """
    Fetches weather data for a specific city using Open-Meteo API.
    Returns current weather, UV index, next 3 hours forecast, and active alerts.
    """
    if city_name not in CITIES:
        raise ValueError(f"City {city_name} not found in configuration.")
    
    coords = CITIES[city_name]
    lat = coords["lat"]
    lon = coords["lon"]
    
    url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
           f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
           f"&hourly=temperature_2m,weather_code"
           f"&daily=uv_index_max"
           f"&timezone=America%2FToronto")
    
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    # Also fetch alerts
    alert_data = get_eccc_alerts(city_name)
    
    return parse_open_meteo_response(data, alert_data)

def parse_open_meteo_response(data, alert_data):
    """
    Parses the raw Open-Meteo JSON into a standardized format.
    """
    current = data.get("current", {})
    hourly = data.get("hourly", {})
    daily = data.get("daily", {})
    
    # Extract current weather
    current_temp = current.get("temperature_2m", 0)
    current_code = current.get("weather_code", 0)
    wind_speed = current.get("wind_speed_10m", 0)
    humidity = current.get("relative_humidity_2m", 0)
    
    # Extract UV Index
    uv_index = 0
    if "uv_index_max" in daily and len(daily["uv_index_max"]) > 0:
        uv_index = daily["uv_index_max"][0]
        if uv_index is None:
            uv_index = 0
    
    # Extract next 3 hours forecast
    current_time_str = current.get("time")
    
    next_3_hours = []
    if current_time_str and "time" in hourly:
        current_hour_str = current_time_str[:13] + ":00"
        
        if current_hour_str in hourly["time"]:
            current_idx = hourly["time"].index(current_hour_str)
            
            for i in range(1, 4):
                if current_idx + i < len(hourly["time"]):
                    hour_time = hourly["time"][current_idx + i]
                    hour_temp = hourly["temperature_2m"][current_idx + i]
                    hour_code = hourly["weather_code"][current_idx + i]
                    
                    hour_formatted = hour_time.split("T")[1]
                    hour_int = int(hour_formatted.split(":")[0])
                    ampm = "AM" if hour_int < 12 else "PM"
                    hour_12 = hour_int if hour_int <= 12 else hour_int - 12
                    if hour_12 == 0: hour_12 = 12
                    hour_12_str = f"{hour_12} {ampm}"
                    
                    next_3_hours.append({
                        "time": hour_12_str,
                        "temp": round(hour_temp),
                        "code": map_weather_code(hour_code)
                    })

    return {
        "current": {
            "temp": round(current_temp),
            "condition": map_weather_code(current_code),
            "wind": round(wind_speed),
            "humidity": round(humidity),
            "uv_index": round(uv_index, 1)
        },
        "forecast": next_3_hours,
        "alert": alert_data
    }

def map_weather_code(code):
    """
    Maps WMO weather codes to human-readable strings and icon filenames.
    """
    mapping = {
        0: ("Clear sky", "weather_clear_day.png"),
        1: ("Mainly clear", "weather_partly_cloudy_day.png"),
        2: ("Partly cloudy", "weather_partly_cloudy_day.png"),
        3: ("Overcast", "weather_cloudy.png"),
        45: ("Fog", "weather_fog.png"),
        48: ("Depositing rime fog", "weather_fog.png"),
        51: ("Light drizzle", "weather_rain.png"),
        53: ("Moderate drizzle", "weather_rain.png"),
        55: ("Dense drizzle", "weather_rain.png"),
        56: ("Light freezing drizzle", "weather_sleet.png"),
        57: ("Dense freezing drizzle", "weather_sleet.png"),
        61: ("Slight rain", "weather_rain.png"),
        63: ("Moderate rain", "weather_rain.png"),
        65: ("Heavy rain", "weather_rain.png"),
        66: ("Light freezing rain", "weather_sleet.png"),
        67: ("Heavy freezing rain", "weather_sleet.png"),
        71: ("Slight snow fall", "weather_snow.png"),
        73: ("Moderate snow fall", "weather_snow.png"),
        75: ("Heavy snow fall", "weather_snow.png"),
        77: ("Snow grains", "weather_snow.png"),
        80: ("Slight rain showers", "weather_rain.png"),
        81: ("Moderate rain showers", "weather_rain.png"),
        82: ("Violent rain showers", "weather_rain.png"),
        85: ("Slight snow showers", "weather_snow.png"),
        86: ("Heavy snow showers", "weather_snow.png"),
        95: ("Thunderstorm", "weather_thunderstorm.png"),
        96: ("Thunderstorm with slight hail", "weather_hail.png"),
        99: ("Thunderstorm with heavy hail", "weather_hail.png")
    }
    return mapping.get(code, ("Unknown", "weather_clear_day.png"))

if __name__ == "__main__":
    # Test fetch for London
    weather = get_weather_data("London")
    print(json.dumps(weather, indent=2))
