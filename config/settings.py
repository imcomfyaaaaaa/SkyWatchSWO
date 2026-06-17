import os
from dotenv import load_dotenv

load_dotenv()

# Meta Graph API Credentials
# Used for Instagram publishing
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# City Configuration (Open-Meteo requires latitude and longitude)
CITIES = {
    "London": {"lat": 42.9836, "lon": -81.2497},
    "St. Thomas": {"lat": 42.7788, "lon": -81.1827},
    "Woodstock": {"lat": 43.1315, "lon": -80.7472},
    "Sarnia": {"lat": 42.9746, "lon": -82.4066},
    "Chatham": {"lat": 42.4048, "lon": -82.1910},
    "Windsor": {"lat": 42.3149, "lon": -83.0364},
    "Kitchener": {"lat": 43.4516, "lon": -80.4925},
    "Cambridge": {"lat": 43.3616, "lon": -80.3144},
    "Brantford": {"lat": 43.1408, "lon": -80.2632},
    "Stratford": {"lat": 43.3699, "lon": -80.9822}
}

# Output Directory for generated images
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Instagram requires images to be hosted on a public URL.
# When running on a VPS, serve the OUTPUT_DIR via Nginx or Apache, and set this URL.
PUBLIC_IMAGE_BASE_URL = os.getenv("PUBLIC_IMAGE_BASE_URL", "https://your-vps-domain.com/output")
