import os
import json
import subprocess
import concurrent.futures
from datetime import datetime
from config.settings import CITIES
from data.weather_client import get_weather_data
from graphics.generator import create_weather_image
from instagram.publisher import upload_carousel, upload_stories

STATE_FILE = os.path.join(os.path.dirname(__file__), "data", "active_alerts.json")

def load_alert_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_alert_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def process_city(city, alert_state):
    print(f"Fetching weather data for {city}...")
    try:
        weather_data = get_weather_data(city)
        print(f"Generating image for {city}...")
        image_path = create_weather_image(city, weather_data)
        
        filename = os.path.basename(image_path)
        
        city_alert_name = None
        city_alert_post = None
        
        if weather_data.get("alert"):
            alert_name = weather_data['alert']['alert_name']
            city_alert_name = alert_name
            
            if alert_state.get(city) == alert_name:
                print(f"Alert '{alert_name}' for {city} is already active and posted. Skipping duplicate post to conserve API rate limits.")
            else:
                print(f"Generating dedicated ALERT image for {city}...")
                from graphics.generator import create_alert_image, format_alert_text
                alert_image_path = create_alert_image(city, weather_data["alert"])
                alert_filename = os.path.basename(alert_image_path)
                
                raw_alert_text = weather_data["alert"].get("alert_text", "")
                formatted_summary = "\n".join(format_alert_text(raw_alert_text))
                
                if len(formatted_summary) > 2000:
                    formatted_summary = formatted_summary[:1997] + "..."
                
                alert_caption = f"⚠️ WEATHER ALERT for {city}: {alert_name} ⚠️\n\n{formatted_summary}\n\n🤖 This is an automated post.\n#OntarioWeather #SkyWatchSWO #ONstorm #{city.replace(' ', '')}ON"
                city_alert_post = (city, alert_filename, alert_caption)
                
        return {
            "city": city,
            "filename": filename,
            "alert_name": city_alert_name,
            "alert_post": city_alert_post
        }
    except Exception as e:
        print(f"Error processing {city}: {e}")
        return None

def main():
    print(f"--- SkyWatchSWO Auto-Poster ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ---")
    
    generated_images = []
    alerts_to_publish = []
    alert_state = load_alert_state()
    current_alerts = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda c: process_city(c, alert_state), CITIES.keys()))
        
    for result in results:
        if result:
            generated_images.append(result["filename"])
            if result["alert_name"]:
                current_alerts[result["city"]] = result["alert_name"]
            if result["alert_post"]:
                alerts_to_publish.append(result["alert_post"])

    # Maximum 10 images in an Instagram Carousel
    if len(generated_images) > 10:
        print("Warning: More than 10 images generated. Truncating to 10 for Carousel.")
        generated_images = generated_images[:10]

    # Save the updated alert state to disk
    save_alert_state(current_alerts)

    # ---------------------------------------------------------
    # GITHUB ACTIONS INTEGRATION
    # The Facebook Graph API requires a public URL to download the images.
    # When running on GitHub Actions, we MUST push the generated images to the 
    # repository FIRST so that raw.githubusercontent.com serves the fresh images!
    # ---------------------------------------------------------
    if os.getenv("GITHUB_ACTIONS") == "true":
        print("\n[GitHub Actions] Pushing generated images to GitHub to activate public URLs...")
        subprocess.run(["git", "config", "--global", "user.name", "github-actions[bot]"])
        subprocess.run(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"])
        subprocess.run(["git", "add", "-f", "output/", "data/active_alerts.json"])
        subprocess.run(["git", "commit", "-m", "🤖 Auto-update weather graphics and state [skip ci]"])
        subprocess.run(["git", "push"])
        print("[GitHub Actions] Push complete! Images are now public.\n")

    # ---------------------------------------------------------
    # PUBLISHING TO INSTAGRAM
    # ---------------------------------------------------------
    for city, filename, caption in alerts_to_publish:
        print(f"Proceeding to upload independent ALERT STORY for {city}...")
        upload_stories([filename])

    if generated_images:
        print("Proceeding to Instagram upload for Daily Regional Stories...")
        upload_stories(generated_images)
        print("\nImages generated successfully.")
    else:
        print("No images were generated.")

if __name__ == "__main__":
    main()
