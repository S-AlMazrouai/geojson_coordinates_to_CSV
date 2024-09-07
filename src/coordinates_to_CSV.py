import argparse
import json
import numpy as np
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
import os
import csv
from tqdm import tqdm
import logging
import traceback
from contextlib import contextmanager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, '..', 'data')

# Set up argument parser
parser = argparse.ArgumentParser(description='Process GeoJSON and create grid points')
parser.add_argument('--input', help='Path to input GeoJSON file')
parser.add_argument('--output', default=output_dir, help='Path to outptu csv file')
parser.add_argument('--spacing', type=float, default=0.02, help='Grid spacing (default: 0.02)')
parser.add_argument('--batch_size', type=int, default=10000, help='Batch size for writing to CSV (default: 10000)')
args = parser.parse_args()

def write_batch_to_csv(csv_writer, batch):
    for point in batch:
        csv_writer.writerow(point)

@contextmanager
def process_geojson(file_path):
    try:
        with open(file_path, 'r') as f:
            geojson_data = json.load(f)
        
        polygons = []
        for feature in geojson_data['features']:
            if feature['geometry']['type'] == 'MultiPolygon':
                for polygon_coords in feature['geometry']['coordinates']:
                    polygons.append(Polygon(polygon_coords[0]))
            elif feature['geometry']['type'] == 'Polygon':
                polygons.append(Polygon(feature['geometry']['coordinates'][0]))
        
        oman = unary_union(polygons)
        yield oman
    except FileNotFoundError:
        logging.error(f"GeoJSON file not found: {file_path}")
        raise
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON data in the GeoJSON file: {file_path}")
        raise
    except Exception as e:
        logging.error(f"An error occurred while processing GeoJSON: {str(e)}")
        raise

def generate_grid_points(oman, grid_spacing):
    minx, miny, maxx, maxy = oman.bounds
    x_grid = np.arange(minx, maxx, grid_spacing)
    y_grid = np.arange(miny, maxy, grid_spacing)
    total_points = len(x_grid) * len(y_grid)
    with tqdm(total=total_points, desc="Generating grid points") as pbar:
        for x in x_grid:
            for y in y_grid:
                point = Point(x, y)
                if oman.contains(point):
                    yield x, y
                pbar.update(1)

def process_points(oman, grid_spacing, output_file, batch_size):
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["longitude", "latitude"])

        batch = []
        for x, y in generate_grid_points(oman, grid_spacing):
            batch.append((x, y))
            if len(batch) >= batch_size:
                write_batch_to_csv(writer, batch)
                batch = []
        
        if batch:
            write_batch_to_csv(writer, batch)

        for polygon in oman.geoms:
            write_batch_to_csv(writer, polygon.exterior.coords)

def main():
    try:
        logging.info("Starting GeoJSON processing")
        with process_geojson(args.input) as oman:
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, "points.csv")
            process_points(oman, args.spacing, output_file, args.batch_size)
        logging.info("GeoJSON processing completed successfully")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        logging.debug(traceback.format_exc())

if __name__ == "__main__":
    main()
