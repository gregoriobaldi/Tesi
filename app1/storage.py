"""File storage and persistence for workbooks."""

import json
import csv
from typing import Dict, Tuple, Any
from model import CellData, format_cell_ref


class WorkbookStorage:
    """Handles saving and loading workbooks."""
    
    @staticmethod
    def save_to_json(cells: Dict[Tuple[int, int], CellData], filename: str):
        """Save workbook to JSON file."""
        data = {
            "cells": {}
        }
        
        for (row, col), cell in cells.items():
            cell_ref = format_cell_ref(row, col)
            data["cells"][cell_ref] = {
                "raw": cell.raw,
                "value": cell.value,
                "bold": cell.bold,
                "precision": cell.precision
            }
            
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    @staticmethod
    def load_from_json(filename: str) -> Dict[Tuple[int, int], CellData]:
        """Load workbook from JSON file."""
        from model import parse_cell_ref
        
        cells = {}
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for cell_ref, cell_data in data.get("cells", {}).items():
                try:
                    row, col = parse_cell_ref(cell_ref)
                    cell = CellData(
                        raw=cell_data.get("raw", ""),
                        value=cell_data.get("value", ""),
                        bold=cell_data.get("bold", False),
                        precision=cell_data.get("precision", 2)
                    )
                    cells[(row, col)] = cell
                except ValueError:
                    continue  # Skip invalid cell references
                    
        except (FileNotFoundError, json.JSONDecodeError):
            pass  # Return empty dict for new files or corrupted files
            
        return cells
        
    @staticmethod
    def export_to_csv(cells: Dict[Tuple[int, int], CellData], filename: str, max_row: int = 100, max_col: int = 26):
        """Export visible range to CSV."""
        # Find actual data bounds
        if not cells:
            max_row = max_col = 0
        else:
            max_row = max(row for row, col in cells.keys()) + 1
            max_col = max(col for row, col in cells.keys()) + 1
            
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            for row in range(max_row):
                row_data = []
                for col in range(max_col):
                    cell = cells.get((row, col))
                    if cell and cell.error:
                        row_data.append(cell.error)
                    elif cell:
                        row_data.append(str(cell.value))
                    else:
                        row_data.append("")
                writer.writerow(row_data)
                
    @staticmethod
    def import_from_csv(filename: str) -> Dict[Tuple[int, int], CellData]:
        """Import data from CSV file."""
        cells = {}
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                for row_idx, row_data in enumerate(reader):
                    for col_idx, value in enumerate(row_data):
                        if value.strip():  # Only import non-empty cells
                            cell = CellData(raw=value, value=value)
                            cells[(row_idx, col_idx)] = cell
        except FileNotFoundError:
            pass
            
        return cells