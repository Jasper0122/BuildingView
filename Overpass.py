import sys
import requests
import random
import time
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def fetch_bounding_box(city_name, country_name):
    """
    Fetches the bounding box for a given city name and country name using Nominatim API.

    Parameters:
        city_name (str): Name of the city to fetch the bounding box for.
        country_name (str): Name of the country to fetch the bounding box for.

    Returns:
        tuple: A tuple containing (south, west, north, east) coordinates defining the bounding box.
    """
    query = f"{city_name}, {country_name}"
    url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&polygon_geojson=1"
    headers = {
        "User-Agent": "YourAppName/1.0 (your-email@example.com)"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check if the request was successful
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bounding box: {e}")
        return None
    except ValueError as e:
        print(f"Error parsing JSON response for bounding box: {e}")
        print(f"Response content: {response.text}")
        return None

    if not data:
        raise ValueError(f"No bounding box found for city: {city_name} in country: {country_name}")

    bbox = data[0]['boundingbox']
    return float(bbox[0]), float(bbox[2]), float(bbox[1]), float(bbox[3])

def fetch_building_data(city_name, country_name, max_elements=100):
    """
    Fetches a random sample of building IDs and their coordinates from OpenStreetMap within a specified city, categorized by building types.

    Parameters:
        city_name (str): Name of the city to fetch the building data for.
        country_name (str): Name of the country to fetch the building data for.
        max_elements (int): Maximum number of building elements to fetch.

    Returns:
        dict: Dictionary containing lists of dictionaries with building IDs and their coordinates, categorized by building types.
    """
    # Fetch bounding box for the city
    bbox = fetch_bounding_box(city_name, country_name)
    if bbox is None:
        print(f"Failed to fetch bounding box for city: {city_name} in country: {country_name}")
        return None
    south, west, north, east = bbox

    # Overpass API query
    query = f"""
    [out:json][timeout:25];
    (
      way["building"]({south},{west},{north},{east});
    );
    out center;
    """
    try:
        response = requests.get("http://overpass-api.de/api/interpreter", params={'data': query})
        response.raise_for_status()  # Check if the request was successful
        data = response.json()
        print(f"Fetched {len(data['elements'])} buildings")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching building data: {e}")
        return None
    except ValueError as e:
        print(f"Error parsing JSON response for building data: {e}")
        print(f"Response content: {response.text}")
        return None

    # Extract building way IDs and their coordinates
    all_buildings = []
    for element in data['elements']:
        if element['type'] == 'way' and 'tags' in element and 'building' in element['tags'] and 'center' in element:
            building_info = {
                'id': element['id'],
                'lat': element['center']['lat'],
                'lon': element['center']['lon'],
                'type': element['tags']['building']
            }
            all_buildings.append(building_info)

    # Check if we have any buildings
    if not all_buildings:
        print("No buildings found")
        return None

    print(f"Total buildings extracted: {len(all_buildings)}")

    # Randomly sample buildings if more than max_elements are fetched
    if len(all_buildings) > max_elements:
        sampled_buildings = random.sample(all_buildings, max_elements)
    else:
        sampled_buildings = all_buildings

    def fetch_details(building):
        building_id = building['id']
        details_query = f"""
        [out:json][timeout:25];
        way({building_id});
        out body;
        >;
        out skel qt;
        """
        try:
            response = requests.get("http://overpass-api.de/api/interpreter", params={'data': details_query})
            response.raise_for_status()  # Check if the request was successful
            details_data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching details for building ID {building_id}: {e}")
            return building
        except ValueError as e:
            print(f"Error parsing JSON response for building ID {building_id}: {e}")
            print(f"Response content: {response.text}")
            return building

        # Extract address and height information
        if details_data['elements']:
            element = details_data['elements'][0]
            building['addr_street'] = element['tags'].get('addr:street', 'N/A')
            building['height'] = element['tags'].get('height', 'N/A')
        else:
            building['addr_street'] = 'N/A'
            building['height'] = 'N/A'
        return building

    # Fetch details for each sampled building in parallel
    building_data = {
        "yes": [],
        "house": [],
        "commercial": []
    }
    with ThreadPoolExecutor(max_workers=5) as executor:  # Reduce the number of concurrent requests
        futures = [executor.submit(fetch_details, building) for building in sampled_buildings]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Fetching building details"):
            building = future.result()
            building_type = building['type']
            building_info = {
                'id': building['id'],
                'lat': building['lat'],
                'lon': building['lon'],
                'addr_street': building['addr_street'],
                'height': building['height'],
                'building_type': building_type
            }
            if building_type == 'yes':
                building_data["yes"].append(building_info)
            elif building_type == 'house':
                building_data["house"].append(building_info)
            elif building_type == 'commercial':
                building_data["commercial"].append(building_info)
            time.sleep(0.5)  # Add a delay between requests to avoid hitting rate limits

    return building_data

def save_to_jsonl(data, city_name, country_name, max_elements):
    """
    Saves the building data to a JSONL file.

    Parameters:
        data (dict): The building data to save.
        city_name (str): Name of the city.
        country_name (str): Name of the country.
        max_elements (int): Maximum number of building elements.
    """
    filename = f"Data/{city_name}_{country_name}_{max_elements}.jsonl"
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        for btype, buildings in data.items():
            for building in buildings:
                json.dump(building, f, ensure_ascii=False)
                f.write('\n')
    print(f"Data saved to {filename}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python building_data_fetcher.py <city_name> <country_name> <max_elements>")
        sys.exit(1)

    city_name = sys.argv[1]
    country_name = sys.argv[2]
    max_elements = int(sys.argv[3])

    building_data = fetch_building_data(city_name, country_name, max_elements)
    if building_data:
        save_to_jsonl(building_data, city_name, country_name, max_elements)
