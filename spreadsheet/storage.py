"""
File I/O operations for spreadsheet data.
Handles JSON save/load and CSV import/export.
"""
import json
import csv
import os
from typing import Optional, Tuple, List, Dict, Any
from model import SpreadsheetModel, parse_address, address_to_string


class StorageManager:
    """Handles file operations for spreadsheet data"""
    
    def __init__(self, model: SpreadsheetModel):
        self.model = model
    
    def save_json(self, filename: str) -> bool:
        """Save spreadsheet to JSON file"""
        try:
            data = self.model.to_dict()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.model.filename = filename
            self.model.modified = False
            return True
        
        except Exception as e:
            print(f"Error saving file: {e}")
            return False
    
    def load_json(self, filename: str) -> bool:
        """Load spreadsheet from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.model.from_dict(data)
            self.model.filename = filename
            self.model.modified = False
            return True
        
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def export_csv(self, filename: str, start_row: int = 0, start_col: int = 0, 
                   end_row: Optional[int] = None, end_col: Optional[int] = None) -> bool:
        """Export range to CSV file"""
        try:
            # Determine export range
            if end_row is None or end_col is None:
                min_row, min_col, max_row, max_col = self.model.sheet.get_used_range()
                if end_row is None:
                    end_row = max_row
                if end_col is None:
                    end_col = max_col
            
            # Ensure we have a valid range
            if start_row > end_row or start_col > end_col:
                return False
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                for row in range(start_row, end_row + 1):
                    row_data = []
                    for col in range(start_col, end_col + 1):
                        value = self.model.get_cell_display_value(row, col)
                        row_data.append(value)
                    writer.writerow(row_data)
            
            return True
        
        except Exception as e:
            print(f"Error exporting CSV: {e}")
            return False
    
    def import_csv(self, filename: str, start_row: int = 0, start_col: int = 0, 
                   has_headers: bool = False) -> bool:
        """Import CSV file into spreadsheet"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                
                current_row = start_row
                for row_data in reader:
                    current_col = start_col
                    for cell_value in row_data:
                        if cell_value.strip():  # Only import non-empty cells
                            # Try to convert to number if possible
                            try:
                                if '.' in cell_value:
                                    numeric_value = float(cell_value)
                                else:
                                    numeric_value = int(cell_value)
                                self.model.set_cell_raw(current_row, current_col, str(numeric_value))
                            except ValueError:
                                # Keep as string
                                self.model.set_cell_raw(current_row, current_col, cell_value)
                        
                        current_col += 1
                    current_row += 1
            
            return True
        
        except Exception as e:
            print(f"Error importing CSV: {e}")
            return False
    
    def get_range_as_csv_string(self, start_row: int, start_col: int, 
                               end_row: int, end_col: int) -> str:
        """Get range data as CSV string for clipboard operations"""
        lines = []
        
        for row in range(start_row, end_row + 1):
            row_data = []
            for col in range(start_col, end_col + 1):
                value = self.model.get_cell_display_value(row, col)
                # Escape quotes and commas for CSV
                if '"' in value or ',' in value or '\n' in value:
                    value = '"' + value.replace('"', '""') + '"'
                row_data.append(value)
            lines.append(','.join(row_data))
        
        return '\n'.join(lines)
    
    def set_range_from_csv_string(self, csv_string: str, start_row: int, start_col: int):
        """Set range data from CSV string (for clipboard paste)"""
        lines = csv_string.strip().split('\n')
        
        current_row = start_row
        for line in lines:
            # Simple CSV parsing (doesn't handle all edge cases)
            values = []
            current_value = ""
            in_quotes = False
            
            i = 0
            while i < len(line):
                char = line[i]
                
                if char == '"' and not in_quotes:
                    in_quotes = True
                elif char == '"' and in_quotes:
                    if i + 1 < len(line) and line[i + 1] == '"':
                        current_value += '"'
                        i += 1
                    else:
                        in_quotes = False
                elif char == ',' and not in_quotes:
                    values.append(current_value)
                    current_value = ""
                else:
                    current_value += char
                
                i += 1
            
            values.append(current_value)  # Add last value
            
            current_col = start_col
            for value in values:
                if value.strip():
                    self.model.set_cell_raw(current_row, current_col, value)
                current_col += 1
            
            current_row += 1
    
    def auto_save(self) -> bool:
        """Auto-save to temporary file"""
        if not self.model.filename:
            return False
        
        try:
            temp_filename = self.model.filename + '.tmp'
            if self.save_json(temp_filename):
                # Restore original filename
                self.model.filename = self.model.filename.replace('.tmp', '')
                return True
            return False
        
        except Exception:
            return False
    
    def create_backup(self) -> bool:
        """Create backup of current file"""
        if not self.model.filename or not os.path.exists(self.model.filename):
            return False
        
        try:
            backup_filename = self.model.filename + '.bak'
            with open(self.model.filename, 'r', encoding='utf-8') as src:
                with open(backup_filename, 'w', encoding='utf-8') as dst:
                    dst.write(src.read())
            return True
        
        except Exception:
            return False
    
    def get_recent_files(self, max_files: int = 10) -> List[str]:
        """Get list of recently opened files (placeholder implementation)"""
        # In a real application, this would read from a config file or registry
        return []
    
    def add_to_recent_files(self, filename: str):
        """Add file to recent files list (placeholder implementation)"""
        # In a real application, this would update a config file or registry
        pass