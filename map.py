import json
import os
import sys
import folium

def read_jsonl(file_path):
    """
    Reads a JSONL file and returns a list of building data.

    Parameters:
        file_path (str): Path to the JSONL file.

    Returns:
        list: List of building data.
    """
    buildings = []
    with open(file_path, 'r') as f:
        for line in f:
            building = json.loads(line)
            buildings.append(building)
    return buildings

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python map.py <jsonl_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    buildings = read_jsonl(file_path)

    # Create a map centered around a specific location
    m = folium.Map(location=[40.739, -73.996], zoom_start=15)

    # Add markers for each building
    for building in buildings:
        lat = building['lat']
        lon = building['lon']
        popup_text = f"ID: {building['id']}<br>Street: {building.get('addr_street', 'N/A')}<br>Height: {building.get('height', 'N/A')}<br>Type: {building.get('building_type', 'N/A')}"
        folium.Marker([lat, lon], popup=popup_text).add_to(m)

    # Save the map as an HTML file in a specific directory based on the JSONL file name
    map_dir = 'Maps'  # Directory to store maps
    jsonl_filename = os.path.basename(file_path).split('.')[0]  # Extract file name without extension
    if not os.path.exists(map_dir):
        os.makedirs(map_dir)  # Create directory if it does not exist
    map_path = os.path.join(map_dir, f"{jsonl_filename}_map.html")
    m.save(map_path)

    print(f"Map has been saved to '{map_path}'")
