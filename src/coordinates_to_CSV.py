import argparse
import json
import numpy as np
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import unary_union
import os
import csv
from tqdm import tqdm
import logging
import traceback
from contextlib import contextmanager
import sys
from typing import List, Tuple, Iterator, Any

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

script_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(script_dir, '..', 'data')

# Set up argument parser
parser = argparse.ArgumentParser(description='Process GeoJSON and create grid points')
parser.add_argument('--input', required=True, help='Path to input GeoJSON file')
parser.add_argument('--output', default=output_dir, help='Path to output directory')
parser.add_argument('--spacing', type=float, default=0.02, help='Grid spacing (default: 0.02)')
parser.add_argument('--batch_size', type=int, default=10000, help='Batch size for writing to CSV (default: 10000)')
args = parser.parse_args()

def write_batch_to_csv(csv_writer: csv.writer, batch: List[Tuple[float, float]]) -> None:
    for point in batch:
        csv_writer.writerow(point)

@contextmanager
def process_geojson(file_path: str) -> Iterator[MultiPolygon]:
    try:
        with open(file_path, 'r') as f:
            geojson_data: dict = json.load(f)
        
        polygons: List[Polygon] = []
        for feature in tqdm(geojson_data['features'], desc="Processing GeoJSON features"):
            if feature['geometry']['type'] == 'MultiPolygon':
                for polygon_coords in feature['geometry']['coordinates']:
                    polygons.append(Polygon(polygon_coords[0]))
            elif feature['geometry']['type'] == 'Polygon':
                polygons.append(Polygon(feature['geometry']['coordinates'][0]))
        
        logging.info("Creating unified shape")
        shape: MultiPolygon = unary_union(polygons)
        yield shape
    except FileNotFoundError:
        logging.error(f"GeoJSON file not found: {file_path}")
        raise
    except json.JSONDecodeError:
        logging.error(f"Invalid JSON data in the GeoJSON file: {file_path}")
        raise
    except Exception as e:
        logging.error(f"An error occurred while processing GeoJSON: {str(e)}")
        raise

def generate_grid_points(shape: MultiPolygon, grid_spacing: float) -> Iterator[Tuple[float, float]]:
    minx, miny, maxx, maxy = shape.bounds
    x_grid = np.arange(minx, maxx, grid_spacing)
    y_grid = np.arange(miny, maxy, grid_spacing)
    total_points = len(x_grid) * len(y_grid)
    with tqdm(total=total_points, desc="Generating grid points") as pbar:
        for x in x_grid:
            for y in y_grid:
                point = Point(x, y)
                if shape.contains(point):
                    yield x, y
                pbar.update(1)

def process_points(shape: MultiPolygon, grid_spacing: float, output_file: str, batch_size: int) -> None:
    with open(output_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["longitude", "latitude"])

        batch: List[Tuple[float, float]] = []
        points_processed = 0
        with tqdm(desc="Processing points", unit="point") as pbar:
            for x, y in generate_grid_points(shape, grid_spacing):
                batch.append((x, y))
                if len(batch) >= batch_size:
                    write_batch_to_csv(writer, batch)
                    points_processed += len(batch)
                    pbar.update(len(batch))
                    batch = []
        
            if batch:
                write_batch_to_csv(writer, batch)
                points_processed += len(batch)
                pbar.update(len(batch))

        logging.info(f"Total points processed: {points_processed}")

        logging.info("Processing polygon boundaries")
        boundary_points = sum(len(polygon.exterior.coords) for polygon in shape.geoms)
        with tqdm(total=boundary_points, desc="Processing boundary points") as pbar:
            for polygon in shape.geoms:
                write_batch_to_csv(writer, polygon.exterior.coords)
                pbar.update(len(polygon.exterior.coords))

def main() -> None:
    try:
        logging.info("Starting GeoJSON processing")
        with process_geojson(args.input) as shape:
            os.makedirs(args.output, exist_ok=True)
            input_filename = os.path.splitext(os.path.basename(args.input))[0]
            output_file = os.path.join(args.output, f"{input_filename}.csv")
            process_points(shape, args.spacing, output_file, args.batch_size)
        logging.info("GeoJSON processing completed successfully")
    except FileNotFoundError as e:
        logging.error(f"File not found: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON data: {e}")
        sys.exit(1)
    except PermissionError as e:
        logging.error(f"Permission denied: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        logging.debug(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
