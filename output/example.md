# Example Module Documentation

## Overview

This module provides utilities for loading, processing, and summarising tabular data. It includes a `DataProcessor` class for data manipulation and helper functions for CSV parsing and description generation.

## Classes

### DataProcessor

A versatile class for loading, transforming, and summarising datasets.

#### Initialization

```python
DataProcessor(name: str)
```

- **name**: A human-readable label for the processor instance

#### Methods

##### `load(records: list[dict[str, Any]]) -> None`
Ingest raw records into the processor.

- **records**: A list of dictionaries, each representing one data row
- **Returns**: None

##### `process(drop_nulls: bool = True) -> list[dict[str, Any]]`
Apply basic cleaning transformations to the loaded records.

- **drop_nulls**: When True, rows containing any None value are removed
- **Returns**: A new list of cleaned records (does not mutate internal state)

##### `summary() -> dict[str, Any]`
Return a statistical summary of the loaded dataset.

- **Returns**: A dictionary with keys:
  - `total_rows`: Total number of records
  - `columns`: Sorted list of unique column names
  - `null_rows`: Number of rows containing null values

## Functions

### `load_csv_naive(path: str) -> list[dict[str, Any]]`
Parse a CSV file into a list of dictionaries using only the standard library.

- **path**: Filesystem path to the CSV file
- **Returns**: List of dictionaries mapping column names to string values

### `describe(processor: DataProcessor) -> str`
Generate a one-line description of a DataProcessor instance.

- **processor**: An initialized DataProcessor instance
- **Returns**: A descriptive string (e.g., "DataProcessor '42' — 10 rows loaded.")

## Example Usage

```python
# Create a processor
proc = DataProcessor("my_dataset")

# Load records
records = load_csv_naive("data.csv")
proc.load(records)

# Process data
cleaned_records = proc.process()

# Get summary
summary = proc.summary()

# Generate description
desc = describe(proc)
print(desc)
```

## Notes

- Uses type hints for better code readability
- Provides basic data cleaning and summary capabilities
- Supports flexible data processing with minimal dependencies