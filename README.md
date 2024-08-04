
# BuildingView: Constructing Urban Building Exteriors Database Using Street View Imagery and Multimodal Large Language Models

## Synopsis
The rapid expansion of geospatial data necessitates efficient and effective methods for searching and mining large data collections. Our project, BuildingView, aims to address this need by developing an automated tool that searches for and annotates urban building data based on city-specific inputs. Utilizing OpenStreetMap (OSM), Google StreetView, and ChatGPT APIs, BuildingView comprehensively constructs an Urban Building Exteriors Database, including building IDs, addresses, heights, coordinates, and detailed exterior descriptions.

## About this Python Package

### 0. Environment Configuration
First, install the required dependencies listed in `requirements.txt`:
```sh
pip install -r requirements.txt
```

### 1. Retrieve Building Data

#### 1.1 Using City and Country Names
You can retrieve building data using the city and country names.

**Script**: `city_country_matcher.py`
```sh
python city_country_fetcher.py "NY"
```
This script uses the Nominatim API to fetch city names and their corresponding countries based on a query provided through the command line. It outputs a list of cities and their countries that match the query.

**Script**: `Overpass.py`
```sh
python Overpass.py "New York" "United States" 1000
```
This script fetches and saves building data for a specified city and country using the Nominatim and Overpass APIs. It performs the following tasks:
- Fetch Bounding Box: Retrieves the bounding box coordinates for the given city and country.
- Fetch Building Data: Queries the Overpass API to get building IDs and coordinates within the bounding box.
- Fetch Building Details: Obtains additional details like address and height for each building.
- Save Data: Saves the building data to a JSONL file, categorized by building types.

#### 1.2 Using Bounding Box Coordinates
You can also retrieve building data by directly inputting bounding box coordinates.

**Script**: `Overpass_bounding_box.py`
```sh
python Overpass_bounding_box.py "New York" 1000 40.477399 -74.259090 40.917577 -73.700272
```
This script fetches and saves building data within a specified bounding box using the Overpass API. It performs the following tasks:
- Fetch Building Data: Retrieves building IDs and coordinates within the given bounding box.
- Fetch Building Details: Obtains additional details like address and height for each building.
- Save Data: Saves the building data to a JSONL file.

**Optional**: To visualize the sampled locations, you can use `map.py` to generate a map with markers.
```sh
python map.py <jsonl_path>
python map.py "Data/New_York_United_States_1000.jsonl"
```

### 2. Match Buildings with Street View Exteriors

**Script**: `StreetView_downloader.py`
Activate the Google Static Street View API by following the provided link. Use the script to download Google Street View images for the locations specified in a JSONL file.
```sh
python StreetView_downloader.py <jsonl_path> <api_key>
python StreetView_downloader.py "Data/New_York_United_States_1000.jsonl" "YOUR_API_KEY"
```
The script performs the following tasks:
- Create Directory: Creates a directory to save the images based on the name of the JSONL file.
- Read Locations: Reads latitude and longitude coordinates from the JSONL file.
- Download Images: Uses the Google Street View API to download images for each location.
- Save Images: Saves the images to the created directory.

### 3. Annotate Urban Building Exteriors

**Script**: `image_processing_pipeline.py`
Activate the OpenAI API by following the provided link. The prompt file contains predefined indicators for Urban Building Exteriors but can be customized.
```sh
python image_processing_pipeline.py <directory> <prompt_file> <api_keys_file>
python image_processing_pipeline.py "GoogleStreetViewImages/New_York_United_States_1000" "prompt.txt" "openai_api_keys.txt"
```
The script automates the process of downloading images, handling failed downloads, and merging JSONL files. It performs the following tasks:
- Run OpenAI Script: Executes an external script (`openai.py`) to download images using given parameters.
- Read Failed Images: Reads and returns a list of images that failed to download from a log file.
- Merge JSONL Files: Merges two JSONL files into one, ensuring there are no duplicate records.
- Read Existing Data: Reads and returns a set of previously processed image IDs from a JSONL file.

### 4. Export Results

**Script**: `export_results.py`
```sh
python export_results.py <input_file_path>
python export_results.py "result/New_York_United_States_1000.jsonl"
```
This script reads a JSONL file containing geospatial data and exports the data into CSV, Shapefile, and GeoJSON formats. It performs the following tasks:
- Read JSONL File: Reads the JSONL file and loads the data into a list.
- Convert to DataFrame: Converts the list of data into a pandas DataFrame.
- Generate Geometry: Creates a geometry column in the DataFrame using latitude and longitude to represent geographical points.
- Export Data: Exports the DataFrame to CSV, Shapefile, and GeoJSON formats.

---

By following these steps, you can create a comprehensive database of urban building exteriors using geospatial data, Google Street View images, and large language models. The provided scripts automate the data retrieval, processing, and exporting tasks, making the workflow efficient and effective.
