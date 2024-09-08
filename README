# GeoJSON Coordinates to CSV

This script processes GeoJSON data and creates a CSV file containing grid points within a specified geographical area.

## Purpose

The main purpose of this code is to take a GeoJSON file containing polygon data (likely representing a geographical area like a country or region) and generate a grid of points within that area. It then saves these points to a CSV file.

## Inputs

The script accepts the following inputs:
- A path to an input GeoJSON file
- An optional output directory path (defaults to a 'data' folder in the parent directory)
- An optional grid spacing value (default is 0.02)
- An optional batch size for writing to CSV (default is 10000)

## Outputs

The main output is a CSV file named "points.csv" containing longitude and latitude coordinates. This file is saved in the specified output directory.

## How it works

The code reads the GeoJSON file, extracts polygon data from it, and creates a unified shape representing the entire area. It then generates a grid of points within this shape based on the specified spacing. Finally, it writes these points to a CSV file in batches.

## Usage Example

To run the script with default settings:

```bash
python geojson_coordinates_to_CSV.py --input_file path/to/input.geojson
```

To specify custom output directory, grid spacing, and batch size:

```bash
python geojson_coordinates_to_CSV.py --input path/to/input.geojson --output path/to/output_dir --spacing 0.02 --batch_size 1000
```

## Important logic and data transformations

- The code first reads and processes the GeoJSON file, converting its data into Shapely Polygon objects.
- It then creates a unified shape from all these polygons.
- A grid is generated based on the bounds of this shape and the specified spacing.
- Each point in the grid is checked to see if it falls within the shape.
- Valid points are collected in batches and written to the CSV file.
- The code also includes the boundary coordinates of the polygons in the output.

This script could be useful for tasks like generating sample points within a country's borders, creating a dataset for geographical analysis, or preparing data for mapping applications. It's designed to handle large areas efficiently by processing points in batches and showing a progress bar during execution.
