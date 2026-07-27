import os
import textwrap
import re
from PIL import Image, ImageDraw, ImageFont
from config.settings import OUTPUT_DIR
from datetime import datetime

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
WIDTH, HEIGHT = 1080, 1920

# ---- Color Gradients ----

def get_gradient_colors(condition_name):
    cond = condition_name.lower()
    hour = datetime.now().hour
    is_night = hour < 6 or hour >= 20

    if "clear" in cond or "sunny" in cond:
        if is_night:
            return (15, 23, 42), (30, 41, 89), (49, 46, 129)
        else:
            return (14, 116, 244), (56, 161, 245), (120, 200, 255)
    elif "cloud" in cond or "overcast" in cond:
        return (30, 41, 59), (51, 65, 85), (100, 116, 139)
    elif "rain" in cond or "sleet" in cond or "drizzle" in cond:
        return (15, 23, 42), (30, 58, 114), (42, 82, 152)
    elif "snow" in cond:
        return (51, 65, 85), (100, 116, 139), (148, 163, 184)
    elif "thunder" in cond:
        return (10, 15, 30), (23, 30, 60), (45, 35, 75)
    elif "fog" in cond:
        return (40, 50, 60), (70, 80, 90), (110, 120, 130)
    else:
        return (15, 23, 42), (30, 41, 89), (49, 46, 129)

def draw_3stop_gradient(img, color1, color2, color3):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    h_mid = h // 2

    for y in range(h_mid):
        t = y / h_mid
        r = int(color1[0] + (color2[0] - color1[0]) * t)
        g = int(color1[1] + (color2[1] - color1[1]) * t)
        b = int(color1[2] + (color2[2] - color1[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    for y in range(h_mid, h):
        t = (y - h_mid) / (h - h_mid)
        r = int(color2[0] + (color3[0] - color2[0]) * t)
        g = int(color2[1] + (color3[1] - color2[1]) * t)
        b = int(color3[2] + (color2[2] - color3[2]) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

def draw_rounded_rect_with_border(img, rect, radius, fill_color, border_color=None, border_width=1):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(rect, radius, fill=fill_color, outline=border_color, width=border_width)
    img.alpha_composite(overlay)

def load_fonts():
    fonts = {}
    font_path_bold = os.path.join(ASSETS_DIR, "Roboto-Bold.ttf")
    font_path_reg = os.path.join(ASSETS_DIR, "Roboto-Regular.ttf")

    def get_font(path, size):
        try:
            return ImageFont.truetype(path, size)
        except IOError:
            return ImageFont.load_default()

    fonts["temp_hero"] = get_font(font_path_bold, 210)
    fonts["city_title"] = get_font(font_path_bold, 92)
    fonts["alert_header"] = get_font(font_path_bold, 58)
    fonts["alert_subtitle"] = get_font(font_path_bold, 44)
    fonts["cond_subtitle"] = get_font(font_path_bold, 48)
    fonts["card_value"] = get_font(font_path_bold, 42)
    fonts["card_label"] = get_font(font_path_bold, 26)
    fonts["forecast_temp"] = get_font(font_path_bold, 52)
    fonts["forecast_time"] = get_font(font_path_reg, 34)
    fonts["body"] = get_font(font_path_reg, 38)
    fonts["header"] = get_font(font_path_reg, 34)
    fonts["footer"] = get_font(font_path_reg, 28)

    return fonts

def add_watermark(image):
    try:
        logo_path = os.path.join(ASSETS_DIR, "SkyWatchlgo.png")
        logo_img = Image.open(logo_path).convert("RGBA")
        logo_img = logo_img.resize((540, 540), Image.Resampling.LANCZOS)
        alpha = logo_img.split()[3]
        alpha = alpha.point(lambda p: int(p * 0.05))
        logo_img.putalpha(alpha)
        image.paste(logo_img, ((WIDTH - 540) // 2, (HEIGHT - 540) // 2), logo_img)
    except Exception:
        pass

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
    return "blue"

def draw_alert_symbol_vector(draw, x, y, size, tier, font):
    r = size // 2
    if tier == "red":
        pts_outer = [(x, y - r - 10), (x - r - 12, y + r + 5), (x + r + 12, y + r + 5)]
        pts_inner = [(x, y - r + 8), (x - r + 2, y + r - 3), (x + r - 2, y + r - 3)]
        draw.polygon(pts_outer, fill=(239, 68, 68))
        draw.polygon(pts_inner, fill=(255, 255, 255))
        draw.text((x, y + 10), "!", font=font, fill=(239, 68, 68), anchor="mm")
    elif tier == "orange":
        pts_outer = [(x, y - r - 10), (x + r + 10, y), (x, y + r + 10), (x - r - 10, y)]
        pts_inner = [(x, y - r + 5), (x + r - 5, y), (x, y + r - 5), (x - r + 5, y)]
        draw.polygon(pts_outer, fill=(245, 158, 11))
        draw.polygon(pts_inner, fill=(15, 23, 42))
        draw.text((x, y), "!", font=font, fill=(245, 158, 11), anchor="mm")
    else:
        fill = (234, 179, 8) if tier == "yellow" else (59, 130, 246)
        draw.ellipse((x - r - 10, y - r - 10, x + r + 10, y + r + 10), fill=fill)
        draw.ellipse((x - r + 5, y - r + 5, x + r - 5, y + r - 5), fill=(15, 23, 42))
        draw.text((x, y), "!", font=font, fill=fill, anchor="mm")


# ---- Main Image Generation Functions ----

def create_weather_image(city_name, weather_data):
    current = weather_data.get("current", {})
    condition, icon_filename = current.get("condition", ("Unknown", ""))
    temp = current.get("temp", "--")
    wind_val = current.get("wind", "--")
    humidity_val = current.get("humidity", "--")
    uv_val = current.get("uv_index", "--")
    forecast = weather_data.get("forecast", [])

    # 1. Background Gradient
    c1, c2, c3 = get_gradient_colors(condition)
    image = Image.new("RGBA", (WIDTH, HEIGHT))
    draw_3stop_gradient(image, c1, c2, c3)
    add_watermark(image)

    fonts = load_fonts()
    draw = ImageDraw.Draw(image)

    # 2. Header (Y = 160)
    ts = datetime.now().strftime("%b %d, %I:%M %p").upper()
    header_str = f"SKYWATCH SWO  •  {ts}"
    draw.text((WIDTH // 2, 160), header_str, font=fonts["header"], fill=(255, 255, 255, 200), anchor="mm")

    # 3. City Name (Y = 240)
    draw.text((WIDTH // 2, 240), city_name.upper(), font=fonts["city_title"], fill=(255, 255, 255, 255), anchor="mm")

    # 4. Main Weather Icon (Y = 320 to 520)
    icon_size = 200
    try:
        icon_path = os.path.join(ASSETS_DIR, "weather_icons", icon_filename)
        icon_img = Image.open(icon_path).convert("RGBA")
        icon_img = icon_img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
        image.paste(icon_img, ((WIDTH - icon_size) // 2, 320), icon_img)
    except Exception:
        pass

    # 5. Temperature (Y = 600)
    draw.text((WIDTH // 2, 600), f"{temp}°", font=fonts["temp_hero"], fill=(255, 255, 255, 255), anchor="mm")

    # 6. Condition Text (Y = 715)
    draw.text((WIDTH // 2, 715), condition.upper(), font=fonts["cond_subtitle"], fill=(255, 255, 255, 230), anchor="mm")

    # 7. High / Low line (Y = 770)
    temps = [h.get("temp") for h in forecast if h.get("temp") is not None]
    if temps:
        hi, lo = max(temps), min(temps)
        hl_str = f"HIGH {hi}°   •   LOW {lo}°"
        draw.text((WIDTH // 2, 770), hl_str, font=fonts["body"], fill=(255, 255, 255, 180), anchor="mm")

    # 8. Metrics Card (Glassmorphism) (Y = 825 to 1005)
    card_rect = (80, 825, 1000, 1005)
    draw_rounded_rect_with_border(image, card_rect, radius=28, fill_color=(255, 255, 255, 25), border_color=(255, 255, 255, 45), border_width=1)

    # Metrics 3 columns
    col_y_label = 865
    col_y_val = 935

    # Column 1: Wind
    draw.text((233, col_y_label), "WIND", font=fonts["card_label"], fill=(255, 255, 255, 180), anchor="mm")
    draw.text((233, col_y_val), f"{wind_val} km/h", font=fonts["card_value"], fill=(255, 255, 255, 255), anchor="mm")

    # Divider 1
    draw.line([(386, 855), (386, 975)], fill=(255, 255, 255, 40), width=1)

    # Column 2: Humidity
    draw.text((540, col_y_label), "HUMIDITY", font=fonts["card_label"], fill=(255, 255, 255, 180), anchor="mm")
    draw.text((540, col_y_val), f"{humidity_val}%", font=fonts["card_value"], fill=(255, 255, 255, 255), anchor="mm")

    # Divider 2
    draw.line([(693, 855), (693, 975)], fill=(255, 255, 255, 40), width=1)

    # Column 3: UV Index
    draw.text((847, col_y_label), "UV INDEX", font=fonts["card_label"], fill=(255, 255, 255, 180), anchor="mm")
    draw.text((847, col_y_val), f"{uv_val}", font=fonts["card_value"], fill=(255, 255, 255, 255), anchor="mm")

    # 9. Forecast Section Header (Y = 1060)
    draw.text((WIDTH // 2, 1060), "3-HOUR FORECAST", font=fonts["card_label"], fill=(255, 255, 255, 190), anchor="mm")

    # 10. Forecast 3 Cards (Y = 1100 to 1390)
    card_w = 270
    card_h = 290
    card_gap = 30
    start_x = (WIDTH - (3 * card_w + 2 * card_gap)) // 2
    card_y1 = 1100
    card_y2 = 1390

    for i, hour_data in enumerate(forecast[:3]):
        cx = start_x + i * (card_w + card_gap) + card_w // 2
        bx1 = start_x + i * (card_w + card_gap)
        bx2 = bx1 + card_w

        draw_rounded_rect_with_border(image, (bx1, card_y1, bx2, card_y2), radius=24, fill_color=(255, 255, 255, 22), border_color=(255, 255, 255, 35), border_width=1)

        # Time
        t = hour_data.get("time", "")
        draw.text((cx, card_y1 + 35), t, font=fonts["forecast_time"], fill=(255, 255, 255, 220), anchor="mm")

        # Inner divider line
        draw.line([(bx1 + 30, card_y1 + 65), (bx2 - 30, card_y1 + 65)], fill=(255, 255, 255, 30), width=1)

        # Icon
        _, f_icon = hour_data.get("code", ("", ""))
        try:
            fic_path = os.path.join(ASSETS_DIR, "weather_icons", f_icon)
            fic_img = Image.open(fic_path).convert("RGBA")
            fic_img = fic_img.resize((90, 90), Image.Resampling.LANCZOS)
            image.paste(fic_img, (cx - 45, card_y1 + 85), fic_img)
        except Exception:
            pass

        # Temp
        f_temp = hour_data.get("temp", "")
        draw.text((cx, card_y1 + 230), f"{f_temp}°", font=fonts["forecast_temp"], fill=(255, 255, 255, 255), anchor="mm")

    # 11. Alert Badge (if alert present) (Y = 1440 to 1530)
    alert = weather_data.get("alert")
    if alert:
        alert_name = alert.get("alert_name", "").upper()
        draw_rounded_rect_with_border(image, (80, 1440, 1000, 1530), radius=22, fill_color=(239, 68, 68, 180), border_color=(255, 255, 255, 80), border_width=1)
        draw.text((WIDTH // 2, 1485), f"ALERT: {alert_name}", font=fonts["body"], fill=(255, 255, 255, 255), anchor="mm")

    # 12. Footer (Y = 1720)
    draw.text((WIDTH // 2, 1720), "SKYWATCH SOUTHWESTERN ONTARIO", font=fonts["footer"], fill=(255, 255, 255, 140), anchor="mm")

    final_image = image.convert("RGB")
    output_path = os.path.join(OUTPUT_DIR, f"{city_name.lower().replace(' ', '_')}.png")
    final_image.save(output_path)
    return output_path


def create_alert_image(city_name, alert_data):
    alert_name = alert_data.get("alert_name", "SEVERE WEATHER").upper()
    tier = get_alert_tier(alert_name)

    if tier == "red":
        c1, c2, c3 = (153, 27, 27), (127, 29, 29), (88, 28, 28)
    elif tier == "orange":
        c1, c2, c3 = (180, 83, 9), (146, 64, 14), (120, 53, 15)
    elif tier == "yellow":
        c1, c2, c3 = (161, 98, 7), (133, 77, 14), (113, 63, 18)
    else:
        c1, c2, c3 = (30, 58, 138), (30, 64, 175), (29, 78, 216)

    image = Image.new("RGBA", (WIDTH, HEIGHT))
    draw_3stop_gradient(image, c1, c2, c3)
    add_watermark(image)

    fonts = load_fonts()
    draw = ImageDraw.Draw(image)

    # 1. Header (Y = 150)
    ts = datetime.now().strftime("%b %d, %I:%M %p").upper()
    draw.text((WIDTH // 2, 150), f"SKYWATCH SWO  •  {ts}", font=fonts["header"], fill=(255, 255, 255, 200), anchor="mm")

    # 2. Alert Symbol Vector (Y = 240)
    draw_alert_symbol_vector(draw, WIDTH // 2, 240, 100, tier, fonts["cond_subtitle"])

    # 3. "WEATHER ALERT" (Y = 320)
    draw.text((WIDTH // 2, 320), "WEATHER ALERT", font=fonts["alert_header"], fill=(255, 255, 255, 255), anchor="mm")

    # 4. City Name (Y = 390)
    draw.text((WIDTH // 2, 390), city_name.upper(), font=fonts["city_title"], fill=(255, 255, 255, 230), anchor="mm")

    # 5. Alert Name (Y = 480)
    wrapped_name = textwrap.fill(alert_name, width=22)
    draw.text((WIDTH // 2, 480), wrapped_name, font=fonts["alert_subtitle"], fill=(255, 255, 255, 255), anchor="ma", align="center")

    # 6. Alert Details Card (Y = 620 to 1640)
    card_rect = (70, 620, 1010, 1640)
    draw_rounded_rect_with_border(image, card_rect, radius=32, fill_color=(0, 0, 0, 120), border_color=(255, 255, 255, 40), border_width=1)

    alert_text = alert_data.get("alert_text", "Please monitor local forecasts.")
    paragraphs = format_alert_text(alert_text)

    lines = []
    for para in paragraphs:
        for line in textwrap.wrap(para, width=44):
            lines.append(line)

    if len(lines) > 21:
        lines = lines[:21]
        lines[-1] = lines[-1] + "..."

    y_text = 660
    for line in lines:
        draw.text((110, y_text), line, font=fonts["body"], fill=(255, 255, 255, 235), anchor="la")
        y_text += 44

    # 7. Footer (Y = 1720)
    draw.text((WIDTH // 2, 1720), "SKYWATCH SOUTHWESTERN ONTARIO", font=fonts["footer"], fill=(255, 255, 255, 140), anchor="mm")

    final_image = image.convert("RGB")
    output_path = os.path.join(OUTPUT_DIR, f"{city_name.lower().replace(' ', '_')}_alert.png")
    final_image.save(output_path)
    return output_path
