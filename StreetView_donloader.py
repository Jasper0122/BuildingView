import json
import os
import sys
import requests
from tqdm import tqdm

def download_street_views(jsonl_path, api_key):
    """
    Downloads Google Street View images based on locations from a JSONL file.

    Parameters:
        jsonl_path (str): Path to the JSONL file containing locations.
        api_key (str): Google Maps API key.
    """
    # Create subfolder based on JSONL filename
    base_folder = "GoogleStreetViewImages"
    jsonl_filename = os.path.basename(jsonl_path).split('.')[0]
    save_folder = os.path.join(base_folder, jsonl_filename)
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    base_url = "https://maps.googleapis.com/maps/api/streetview"
    params = {
        'size': '600x300',
        'radius': 30,
        'key': api_key
    }

    # Read JSONL file
    with open(jsonl_path, 'r') as file:
        locations = [json.loads(line) for line in file]

    pbar = tqdm(total=len(locations), desc="Downloading Street Views")
    for location in locations:
        # Set API call parameters
        params['location'] = f"{location['lat']},{location['lon']}"

        # Send request to Google Street View API
        response = requests.get(base_url, params=params, stream=True)

        if response.status_code == 200:
            image_path = os.path.join(save_folder, f"{location['id']}.jpg")
            with open(image_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"\nImage saved for Location {location['id']} - {image_path}")
        else:
            print(f"\nFailed to fetch image for location {location['id']}. Status code: {response.status_code}")

        pbar.update(1)
    pbar.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python StreetView_downloader.py <jsonl_path> <api_key>")
        sys.exit(1)

    jsonl_path = sys.argv[1]
    api_key = sys.argv[2]

    download_street_views(jsonl_path, api_key)
