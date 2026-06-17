import os
import textwrap
from PIL import Image, ImageDraw, ImageFont
from config.settings import OUTPUT_DIR
from datetime import datetime

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

def draw_vertical_gradient(img, color_top, color_bottom):
    draw = ImageDraw.Draw(img)
    width, height = img.size
    for y in range(height):
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * y / height)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * y / height)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

def get_gradient_for_condition(condition_name):
    cond = condition_name.lower()
    if "clear" in cond:
        return (41, 128, 185), (109, 213, 250)
    elif "cloud" in cond or "fog" in cond or "overcast" in cond:
        return (59, 65, 70), (107, 123, 140)
    elif "rain" in cond or "sleet" in cond or "drizzle" in cond:
        return (30, 60, 114), (42, 82, 152)
    elif "snow" in cond:
        return (131, 164, 212), (182, 251, 255)
    elif "thunder" in cond:
        return (20, 30, 48), (36, 59, 85)
    return (20, 30, 48), (36, 59, 85)

import re

def draw_rounded_rect(img, rect, radius, color):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(rect, radius, fill=color)
    img.alpha_composite(overlay)

def format_alert_text(text):
    text = text.replace("Please continue to monitor alerts and forecasts issued by Environment Canada.", "")
    text = text.replace("To report severe weather, send an email to ONstorm@ec.gc.ca or post reports on X using #ONStorm.", "")
    text = text.replace("\n", " ")
    
    text = re.sub(r"(?i)\bwhat:", r"\nWHAT:", text)
    text = re.sub(r"(?i)\bwhen:", r"\nWHEN:", text)
    text = re.sub(r"(?i)\bwhere:", r"\nWHERE:", text)
    text = re.sub(r"(?i)\badditional information:", r"\nINFO:", text)
    
    out = []
    parts = [p.strip() for p in text.split('\n') if p.strip()]
    for p in parts:
        p = re.sub(r" +", " ", p)
        if p.startswith("WHAT:"):
            out.append("• " + p)
        elif p.startswith("WHEN:"):
            out.append("• " + p)
        elif p.startswith("WHERE:"):
            pass
        elif p.startswith("INFO:"):
            out.append("• " + p)
        else:
            out.append(p)
    return out

def get_alert_tier(alert_name):
    name = alert_name.lower()
    if "tornado" in name or "hurricane" in name or "extreme" in name:
        return "red"
    elif "warning" in name:
        return "orange"
    elif "watch" in name or "advisory" in name:
        return "yellow"
    else:
        return "blue"

def draw_alert_symbol(draw, x, y, size, tier, font_path):
    r = size // 2
    try:
        font_excl = ImageFont.truetype(font_path, int(size * 0.8))
    except:
        font_excl = ImageFont.load_default()

    if tier == "red":
        outer_points = [(x, y - r - 15), (x - r - 15, y + r), (x + r + 15, y + r)]
        inner_points = [(x, y - r), (x - r, y + r - 8), (x + r, y + r - 8)]
        draw.polygon(outer_points, fill=(255, 30, 30))
        draw.polygon(inner_points, fill=(255, 255, 255))
        draw.text((x, y + 15), "!", font=font_excl, fill=(255, 30, 30), anchor="mm")

    elif tier == "orange":
        outer_points = [(x, y - r - 15), (x + r + 15, y), (x, y + r + 15), (x - r - 15, y)]
        inner_points = [(x, y - r), (x + r, y), (x, y + r), (x - r, y)]
        draw.polygon(outer_points, fill=(255, 120, 0))
        draw.polygon(inner_points, fill=(0, 0, 0))
        draw.text((x, y), "!", font=font_excl, fill=(255, 120, 0), anchor="mm")

    elif tier == "yellow":
        draw.ellipse((x - r - 15, y - r - 15, x + r + 15, y + r + 15), fill=(255, 215, 0))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(0, 0, 0))
        draw.text((x, y), "!", font=font_excl, fill=(255, 215, 0), anchor="mm")

    else: # Blue
        draw.ellipse((x - r - 15, y - r - 15, x + r + 15, y + r + 15), fill=(50, 150, 255))
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(0, 0, 0))
        draw.text((x, y), "!", font=font_excl, fill=(50, 150, 255), anchor="mm")


def create_weather_image(city_name, weather_data):
    width, height = 1080, 1350
    
    current = weather_data.get("current", {})
    condition, icon = current.get("condition", ("Unknown", ""))
    alert = weather_data.get("alert")
    
    # Generate background
    color_top, color_bottom = get_gradient_for_condition(condition)
        
    image = Image.new("RGBA", (width, height))
    draw_vertical_gradient(image, color_top, color_bottom)
    
    # Load Fonts
    try:
        font_huge = ImageFont.truetype(os.path.join(ASSETS_DIR, "Roboto-Bold.ttf"), 220)
        font_large = ImageFont.truetype(os.path.join(ASSETS_DIR, "Roboto-Bold.ttf"), 100)
        font_bold_medium = ImageFont.truetype(os.path.join(ASSETS_DIR, "Roboto-Bold.ttf"), 60)
        font_medium = ImageFont.truetype(os.path.join(ASSETS_DIR, "Roboto-Regular.ttf"), 50)
        font_small = ImageFont.truetype(os.path.join(ASSETS_DIR, "Roboto-Regular.ttf"), 40)
        font_xs = ImageFont.truetype(os.path.join(ASSETS_DIR, "Roboto-Bold.ttf"), 30)
    except IOError:
        font_huge = font_large = font_medium = font_small = font_bold_medium = font_xs = ImageFont.load_default()

    draw = ImageDraw.Draw(image)

    # 0. Background Watermark Logo
    try:
        logo_path = os.path.join(ASSETS_DIR, "SkyWatchlgo.png")
        logo_img = Image.open(logo_path).convert("RGBA")
        logo_img = logo_img.resize((800, 800), Image.Resampling.LANCZOS)
        
        # Reduce opacity to 8% for a subtle watermark
        alpha = logo_img.split()[3]
        alpha = alpha.point(lambda p: p * 0.08)
        logo_img.putalpha(alpha)
        
        image.paste(logo_img, ((width - 800) // 2, (height - 800) // 2), logo_img)
    except Exception:
        pass

    # 1. Main Header (City & Brand & Time)
    current_time_str = datetime.now().strftime("%b %d, %I:%M %p").upper()
    header_text = f"SKYWATCH SWO  •  {current_time_str}"
    draw.text((width // 2, 80), header_text, font=font_small, fill=(255, 255, 255, 200), anchor="mm")
    draw.text((width // 2, 160), city_name.upper(), font=font_large, fill=(255, 255, 255), anchor="mm")
    
    # 2. Main Weather Icon
    try:
        icon_path = os.path.join(ASSETS_DIR, "weather_icons", icon)
        icon_img = Image.open(icon_path).convert("RGBA")
        icon_img = icon_img.resize((240, 240), Image.Resampling.LANCZOS)
        image.paste(icon_img, ((width - 240) // 2, 240), icon_img)
    except Exception:
        pass

    # 3. Temperature & Condition
    temp = current.get("temp", "--")
    draw.text((width // 2, 570), f"{temp}°", font=font_huge, fill=(255, 255, 255), anchor="mm")
    draw.text((width // 2, 720), condition.upper(), font=font_bold_medium, fill=(255, 255, 255, 230), anchor="mm")

    # 4. Details Card (Glassmorphism)
    wind = current.get("wind", "--")
    humidity = current.get("humidity", "--")
    uv_index = current.get("uv_index", "--")
    
    draw_rounded_rect(image, (100, 810, 980, 910), 30, (255, 255, 255, 40))
    
    # Draw Wind, UV, and Humidity distributed evenly
    draw.text((250, 860), f"Wind: {wind} km/h", font=font_small, fill=(255, 255, 255), anchor="mm")
    draw.text((540, 860), f"UV Index: {uv_index}", font=font_small, fill=(255, 255, 255), anchor="mm")
    draw.text((830, 860), f"Humidity: {humidity}%", font=font_small, fill=(255, 255, 255), anchor="mm")

    # 5. Forecast Header
    draw.text((width // 2, 980), "NEXT 3 HOURS", font=font_small, fill=(255, 255, 255, 200), anchor="mm")
    
    # 6. Forecast Cards
    forecast = weather_data.get("forecast", [])
    x_centers = [230, 540, 850]
    
    for i, hour_data in enumerate(forecast[:3]):
        xc = x_centers[i]
        
        # Card Background
        draw_rounded_rect(image, (xc - 130, 1020, xc + 130, 1250), 30, (255, 255, 255, 40))
        
        t = hour_data.get("time", "")
        f_temp = hour_data.get("temp", "")
        _, f_icon = hour_data.get("code", ("", ""))
        
        # Time
        draw.text((xc, 1070), t, font=font_small, fill=(255, 255, 255, 230), anchor="mm")
        
        # Icon
        try:
            f_icon_path = os.path.join(ASSETS_DIR, "weather_icons", f_icon)
            f_icon_img = Image.open(f_icon_path).convert("RGBA")
            f_icon_img = f_icon_img.resize((80, 80), Image.Resampling.LANCZOS)
            image.paste(f_icon_img, (xc - 40, 1100), f_icon_img)
        except Exception:
            pass
        
        # Temp
        draw.text((xc, 1210), f"{f_temp}°", font=font_medium, fill=(255, 255, 255), anchor="mm")

    final_image = image.convert("RGB")
    output_path = os.path.join(OUTPUT_DIR, f"{city_name.lower().replace(' ', '_')}.png")
    final_image.save(output_path)
    return output_path

def create_alert_image(city_name, alert_data):
    width, height = 1080, 1350
    
    alert_name = alert_data.get("alert_name", "SEVERE WEATHER").upper()
    tier = get_alert_tier(alert_name)

    if tier == "red":
        color_top, color_bottom = (120, 0, 0), (200, 10, 10)
    elif tier == "orange":
        color_top, color_bottom = (140, 50, 0), (220, 80, 10)
    elif tier == "yellow":
        color_top, color_bottom = (120, 100, 0), (180, 150, 10)
    else: # Blue
        color_top, color_bottom = (10, 30, 100), (20, 60, 160)
        
    image = Image.new("RGBA", (width, height))
    draw_vertical_gradient(image, color_top, color_bottom)
    
    try:
        font_huge = ImageFont.truetype(os.path.join(ASSETS_DIR, "Roboto-Bold.ttf"), 100)
        font_large = ImageFont.truetype(os.path.join(ASSETS_DIR, "Roboto-Bold.ttf"), 80)
        font_medium = ImageFont.truetype(os.path.join(ASSETS_DIR, "Roboto-Regular.ttf"), 32)
        font_small = ImageFont.truetype(os.path.join(ASSETS_DIR, "Roboto-Regular.ttf"), 40)
    except IOError:
        font_huge = font_large = font_medium = font_small = ImageFont.load_default()

    draw = ImageDraw.Draw(image)

    # Background Watermark Logo
    try:
        logo_path = os.path.join(ASSETS_DIR, "SkyWatchlgo.png")
        logo_img = Image.open(logo_path).convert("RGBA")
        logo_img = logo_img.resize((800, 800), Image.Resampling.LANCZOS)
        
        alpha = logo_img.split()[3]
        alpha = alpha.point(lambda p: p * 0.08)
        logo_img.putalpha(alpha)
        
        image.paste(logo_img, ((width - 800) // 2, (height - 800) // 2), logo_img)
    except Exception:
        pass

    current_time_str = datetime.now().strftime("%b %d, %I:%M %p").upper()
    header_text = f"SKYWATCH SWO  •  {current_time_str}"
    draw.text((width // 2, 80), header_text, font=font_small, fill=(255, 255, 255, 200), anchor="mm")
    
    font_path_bold = os.path.join(ASSETS_DIR, "Roboto-Bold.ttf")
    draw_alert_symbol(draw, width // 2, 220, 130, tier, font_path_bold)
    
    draw.text((width // 2, 360), "WEATHER ALERT", font=font_huge, fill=(255, 255, 255), anchor="mm")
    draw.text((width // 2, 450), city_name.upper(), font=font_large, fill=(255, 255, 255, 220), anchor="mm")
    
    wrapped_name = textwrap.fill(alert_name, width=22)
    draw.text((width // 2, 570), wrapped_name, font=font_large, fill=(255, 255, 255), anchor="ma", align="center")
    
    draw_rounded_rect(image, (80, 720, 1000, 1300), 30, (0, 0, 0, 100))
    
    alert_text = alert_data.get("alert_text", "Please monitor local forecasts.")
    formatted_paragraphs = format_alert_text(alert_text)
    
    lines = []
    for para in formatted_paragraphs:
        for line in textwrap.wrap(para, width=62):
            lines.append(line)
    
    if len(lines) > 15:
        lines = lines[:15]
        lines[-1] = lines[-1] + "..."
    
    y_text = 730
    for line in lines:
        draw.text((110, y_text), line, font=font_medium, fill=(255, 255, 255), anchor="la", align="left")
        y_text += 38

    final_image = image.convert("RGB")
    output_path = os.path.join(OUTPUT_DIR, f"{city_name.lower().replace(' ', '_')}_alert.png")
    final_image.save(output_path)
    return output_path

if __name__ == "__main__":
    sample_data = {
      "current": {
        "temp": 24,
        "condition": ("Thunderstorm", "weather_thunderstorm.png"),
        "wind": 15,
        "humidity": 62,
        "uv_index": 6.4
      },
      "alert": {
          "alert_name": "SEVERE THUNDERSTORM WARNING"
      },
      "forecast": [
        {"time": "1 PM", "temp": 24, "code": ("Thunderstorm", "weather_thunderstorm.png")},
        {"time": "2 PM", "temp": 25, "code": ("Clear sky", "weather_clear_day.png")},
        {"time": "3 PM", "temp": 25, "code": ("Clear sky", "weather_clear_day.png")}
      ]
    }
    path = create_alert_image("London", sample_data["alert"])
    print(f"Test alert image generated at {path}")
