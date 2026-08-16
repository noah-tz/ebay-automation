"""
Data-Driven testing utility.
Loads test data from YAML, JSON, or CSV files.
"""
import json
import csv
from pathlib import Path
from typing import Any

import yaml

DATA_DIR = Path(__file__).parent.parent / "data"


class DataLoader:
    """Loads test data from external files (YAML/JSON/CSV)."""

    @staticmethod
    def load_yaml(filename: str) -> Any:
        """Load data from a YAML file."""
        filepath = DATA_DIR / filename
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    @staticmethod
    def load_json(filename: str) -> Any:
        """Load data from a JSON file."""
        filepath = DATA_DIR / filename
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def load_csv(filename: str) -> list[dict]:
        """Load data from a CSV file. Returns list of dicts."""
        filepath = DATA_DIR / filename
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    @staticmethod
    def load(filename: str) -> Any:
        """Auto-detect file format and load data."""
        ext = Path(filename).suffix.lower()
        if ext in (".yml", ".yaml"):
            return DataLoader.load_yaml(filename)
        elif ext == ".json":
            return DataLoader.load_json(filename)
        elif ext == ".csv":
            return DataLoader.load_csv(filename)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
