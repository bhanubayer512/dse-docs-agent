"""
example.py — demo module for AI documentation generation.

Provides DataProcessor: a class that loads, processes,
and summarises tabular data stored as a list of dicts.
"""
from __future__ import annotations
from typing import Any


class DataProcessor:
    """Load, transform, and summarise a dataset.

    Args:
        name: A human-readable label for this processor instance.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._records: list[dict[str, Any]] = []

    def load(self, records: list[dict[str, Any]]) -> None:
        """Ingest raw records into the processor.

        Args:
            records: A list of dicts, each representing one data row.
        """
        self._records = list(records)

    def process(self, drop_nulls: bool = True) -> list[dict[str, Any]]:
        """Apply basic cleaning transformations to the loaded records.

        Args:
            drop_nulls: When True, rows that contain any None value are removed.

        Returns:
            A new list of cleaned records; internal state is not mutated.
        """
        result = self._records[:]
        if drop_nulls:
            result = [row for row in result if None not in row.values()]
        return result

    def summary(self) -> dict[str, Any]:
        """Return a statistical summary of the loaded dataset.

        Returns:
            A dict with keys: total_rows, columns, null_rows.
        """
        columns = sorted({key for row in self._records for key in row})
        null_rows = sum(1 for row in self._records if None in row.values())
        return {
            "total_rows": len(self._records),
            "columns": columns,
            "null_rows": null_rows,
        }


def load_csv_naive(path: str) -> list[dict[str, Any]]:
    """Parse a CSV file into a list of dicts using stdlib only.

    Args:
        path: Filesystem path to the CSV file.

    Returns:
        List of dicts mapping column names to string values.
    """
    import csv
    with open(path, newline="", encoding="utf-8") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def describe(processor: DataProcessor) -> str:
    """Return a one-liner describing a DataProcessor.

    Args:
        processor: An initialised DataProcessor instance.

    Returns:
        A descriptive string, e.g. "DataProcessor 42 rows loaded."
    """
    total = processor.summary()["total_rows"]
    return f"DataProcessor {processor.name!r} — {total} rows loaded."
