import os
import sys
import json
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

def read_jsonl(file_path):
    """
    Reads a JSONL file and returns a list of data.

    Parameters:
        file_path (str): Path to the JSONL file.

    Returns:
        list: List of data from the JSONL file.
    """
    data = []
    with open(file_path, 'r') as file:
        for line in file:
            data.append(json.loads(line))
    return data

def export_to_formats(df, base_export_path, base_filename):
    """
    Exports the DataFrame to CSV, Shapefile, and GeoJSON formats.

    Parameters:
        df (pandas.DataFrame): DataFrame containing the data.
        base_export_path (str): Base path for exporting the files.
        base_filename (str): Base filename for the exported files.
    """
    # Ensure the export directory exists
    os.makedirs(base_export_path, exist_ok=True)

    # Define export file paths
    csv_file_path = f"{base_export_path}/{base_filename}.csv"
    shapefile_path = f"{base_export_path}/{base_filename}"
    geojson_file_path = f"{base_export_path}/{base_filename}.geojson"

    # Export to CSV
    df.to_csv(csv_file_path, index=False)
    print(f"Exported CSV to {csv_file_path}")

    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry='geometry')

    # Export to Shapefile
    gdf.to_file(shapefile_path, driver='ESRI Shapefile')
    print(f"Exported Shapefile to {shapefile_path}")

    # Export to GeoJSON
    gdf.to_file(geojson_file_path, driver='GeoJSON')
    print(f"Exported GeoJSON to {geojson_file_path}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python export_results.py <input_file_path>")
        sys.exit(1)

    input_file_path = sys.argv[1]
    base_export_path = os.path.join('export', os.path.splitext(os.path.basename(input_file_path))[0])

    # Read JSONL file
    data = read_jsonl(input_file_path)

    # Convert to DataFrame
    df = pd.DataFrame(data)

    # Generate 'geometry' column for GeoDataFrame
    df['geometry'] = [Point(xy) for xy in zip(df.lon, df.lat)]

    # Define base filename for exports
    base_filename = os.path.splitext(os.path.basename(input_file_path))[0]

    # Export to formats
    export_to_formats(df, base_export_path, base_filename)
