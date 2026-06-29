import requests
import time
from config.settings import IG_ACCOUNT_ID, ACCESS_TOKEN, PUBLIC_IMAGE_BASE_URL

GRAPH_URL = "https://graph.facebook.com/v19.0"

def upload_carousel(image_filenames, caption):
    """
    Uploads a list of images as a Carousel post to Instagram via the Graph API.
    
    1. Create a container for each image.
    2. Create a carousel container grouping the image containers.
    3. Publish the carousel container.
    """
    if not IG_ACCOUNT_ID or not ACCESS_TOKEN:
        print("Error: IG_ACCOUNT_ID or ACCESS_TOKEN not set.")
        return

    # Step 1: Create media containers for each image
    container_ids = []
    for filename in image_filenames:
        public_url = f"{PUBLIC_IMAGE_BASE_URL.rstrip('/')}/{filename}"
        print(f"Creating container for: {public_url}")
        
        url = f"{GRAPH_URL}/{IG_ACCOUNT_ID}/media"
        payload = {
            "image_url": public_url,
            "is_carousel_item": "true",
            "access_token": ACCESS_TOKEN
        }
        
        response = requests.post(url, data=payload, timeout=10)
        res_data = response.json()
        
        if "id" in res_data:
            container_ids.append(res_data["id"])
        else:
            print(f"Error creating container for {filename}: {res_data}")
            raise Exception(f"Failed to create Carousel Container for {filename}: {res_data}")
            
    # Wait a few seconds for Facebook to process the media
    time.sleep(5)
    
    # Step 2: Create the Carousel Container
    print("Creating carousel container...")
    url = f"{GRAPH_URL}/{IG_ACCOUNT_ID}/media"
    payload = {
        "media_type": "CAROUSEL",
        "children": ",".join(container_ids),
        "caption": caption,
        "access_token": ACCESS_TOKEN
    }
    
    response = requests.post(url, data=payload, timeout=10)
    res_data = response.json()
    
    if "id" not in res_data:
        print(f"Error creating carousel container: {res_data}")
        raise Exception(f"Failed to create Carousel: {res_data}")
        
    carousel_id = res_data["id"]
    
    # Wait again
    time.sleep(5)
    
    # Step 3: Publish the Carousel
    print("Publishing carousel to Instagram...")
    url = f"{GRAPH_URL}/{IG_ACCOUNT_ID}/media_publish"
    payload = {
        "creation_id": carousel_id,
        "access_token": ACCESS_TOKEN
    }
    
    response = requests.post(url, data=payload, timeout=10)
    res_data = response.json()
    
    if "id" in res_data:
        print(f"Successfully published carousel! IG Media ID: {res_data['id']}")
    else:
        print(f"Error publishing carousel: {res_data}")
        raise Exception(f"Failed to publish Carousel: {res_data}")

def upload_stories(image_filenames):
    """
    Uploads a list of images as independent Instagram Stories.
    """
    if not IG_ACCOUNT_ID or not ACCESS_TOKEN:
        print("Error: IG_ACCOUNT_ID or ACCESS_TOKEN not set.")
        return

    for filename in image_filenames:
        public_url = f"{PUBLIC_IMAGE_BASE_URL.rstrip('/')}/{filename}"
        print(f"Creating Story container for: {public_url}")
        
        url = f"{GRAPH_URL}/{IG_ACCOUNT_ID}/media"
        payload = {
            "image_url": public_url,
            "media_type": "STORIES",
            "access_token": ACCESS_TOKEN
        }
        
        response = requests.post(url, data=payload, timeout=10)
        res_data = response.json()
        
        if "id" not in res_data:
            print(f"Error creating Story container for {filename}: {res_data}")
            raise Exception(f"Failed to create Story container for {filename}: {res_data}")
            
        creation_id = res_data["id"]
        
        # Wait a few seconds for Facebook to process the media
        time.sleep(5)
        
        print(f"Publishing Story...")
        publish_url = f"{GRAPH_URL}/{IG_ACCOUNT_ID}/media_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": ACCESS_TOKEN
        }
        
        pub_response = requests.post(publish_url, data=publish_payload, timeout=10)
        pub_data = pub_response.json()
        
        if "id" in pub_data:
            print(f"Successfully published Story! IG Media ID: {pub_data['id']}")
        else:
            print(f"Error publishing Story: {pub_data}")
            raise Exception(f"Failed to publish Instagram Story: {pub_data}")
        
        # Wait before posting the next story to avoid rate limits
        time.sleep(3)

