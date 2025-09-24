"""
Data model for spreadsheet application.
Handles cell storage, addressing, and formatting.
"""
from typing import Dict, Tuple, Optional, Any, List
import json
import re


def col_to_letter(col: int) -> str:
    """Convert 0-based column index to letter (A, B, ..., Z, AA, AB, ...)"""
    result = ""
    while col >= 0:
        result = chr(65 + col % 26) + result
        col = col // 26 - 1
        if col < 0:
            break
    return result


def letter_to_col(letter: str) -> int:
    """Convert column letter to 0-based index"""
    result = 0
    for char in letter.upper():
        result = result * 26 + (ord(char) - 64)
    return result - 1


def parse_address(addr: str) -> Tuple[int, int]:
    """Parse cell address like 'A1' to (row, col) 0-based"""
    match = re.match(r'^([A-Z]+)(\d+)$', addr.upper())
    if not match:
        raise ValueError(f"Invalid cell address: {addr}")
    col_str, row_str = match.groups()
    return int(row_str) - 1, letter_to_col(col_str)


def address_to_string(row: int, col: int) -> str:
    """Convert (row, col) to address string like 'A1'"""
    return f"{col_to_letter(col)}{row + 1}"


def parse_range(range_str: str) -> List[Tuple[int, int]]:
    """Parse range like 'A1:B3' to list of (row, col) tuples"""
    if ':' not in range_str:
        row, col = parse_address(range_str)
        return [(row, col)]
    
    start_addr, end_addr = range_str.split(':', 1)
    start_row, start_col = parse_address(start_addr)
    end_row, end_col = parse_address(end_addr)
    
    cells = []
    for row in range(min(start_row, end_row), max(start_row, end_row) + 1):
        for col in range(min(start_col, end_col), max(start_col, end_col) + 1):
            cells.append((row, col))
    return cells


class Cell:
    """Represents a single spreadsheet cell"""
    
    def __init__(self, raw: str = "", value: Any = "", format_dict: Optional[Dict] = None):
        self.raw = raw  # Raw input (formula or literal)
        self.value = value  # Evaluated value
        self.format = format_dict or {}  # Formatting options
        self.error = None  # Error message if any
    
    def is_formula(self) -> bool:
        """Check if cell contains a formula"""
        return isinstance(self.raw, str) and self.raw.startswith('=')
    
    def to_dict(self) -> Dict:
        """Serialize cell to dictionary"""
        return {
            'raw': self.raw,
            'value': self.value,
            'format': self.format,
            'error': self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Cell':
        """Deserialize cell from dictionary"""
        cell = cls(data.get('raw', ''), data.get('value', ''), data.get('format', {}))
        cell.error = data.get('error')
        return cell


class Sheet:
    """Represents a spreadsheet sheet with sparse cell storage"""
    
    def __init__(self):
        self.cells: Dict[Tuple[int, int], Cell] = {}
        self.name = "Sheet1"
        self.max_row = 0
        self.max_col = 0
    
    def get_cell(self, row: int, col: int) -> Cell:
        """Get cell at position, creating empty cell if needed"""
        if (row, col) not in self.cells:
            self.cells[(row, col)] = Cell()
        return self.cells[(row, col)]
    
    def set_cell(self, row: int, col: int, raw: str, value: Any = None, format_dict: Optional[Dict] = None):
        """Set cell content"""
        cell = Cell(raw, value if value is not None else raw, format_dict)
        self.cells[(row, col)] = cell
        self.max_row = max(self.max_row, row)
        self.max_col = max(self.max_col, col)
    
    def delete_cell(self, row: int, col: int):
        """Delete cell content"""
        if (row, col) in self.cells:
            del self.cells[(row, col)]
    
    def get_used_range(self) -> Tuple[int, int, int, int]:
        """Get bounds of used cells (min_row, min_col, max_row, max_col)"""
        if not self.cells:
            return 0, 0, 0, 0
        
        rows = [pos[0] for pos in self.cells.keys()]
        cols = [pos[1] for pos in self.cells.keys()]
        return min(rows), min(cols), max(rows), max(cols)
    
    def insert_row(self, row: int):
        """Insert row at position, shifting cells down"""
        new_cells = {}
        for (r, c), cell in self.cells.items():
            if r >= row:
                new_cells[(r + 1, c)] = cell
            else:
                new_cells[(r, c)] = cell
        self.cells = new_cells
        self.max_row += 1
    
    def delete_row(self, row: int):
        """Delete row, shifting cells up"""
        new_cells = {}
        for (r, c), cell in self.cells.items():
            if r == row:
                continue
            elif r > row:
                new_cells[(r - 1, c)] = cell
            else:
                new_cells[(r, c)] = cell
        self.cells = new_cells
        if self.max_row > 0:
            self.max_row -= 1
    
    def insert_column(self, col: int):
        """Insert column at position, shifting cells right"""
        new_cells = {}
        for (r, c), cell in self.cells.items():
            if c >= col:
                new_cells[(r, c + 1)] = cell
            else:
                new_cells[(r, c)] = cell
        self.cells = new_cells
        self.max_col += 1
    
    def delete_column(self, col: int):
        """Delete column, shifting cells left"""
        new_cells = {}
        for (r, c), cell in self.cells.items():
            if c == col:
                continue
            elif c > col:
                new_cells[(r, c - 1)] = cell
            else:
                new_cells[(r, c)] = cell
        self.cells = new_cells
        if self.max_col > 0:
            self.max_col -= 1


class SpreadsheetModel:
    """Main spreadsheet model"""
    
    def __init__(self):
        self.sheet = Sheet()
        self.filename = None
        self.modified = False
        self.observers = []  # Callbacks for model changes
    
    def add_observer(self, callback):
        """Add observer for model changes"""
        self.observers.append(callback)
    
    def notify_observers(self, event_type: str, **kwargs):
        """Notify observers of model changes"""
        for callback in self.observers:
            callback(event_type, **kwargs)
    
    def set_cell_raw(self, row: int, col: int, raw: str):
        """Set cell raw content and mark as modified"""
        self.sheet.set_cell(row, col, raw)
        self.modified = True
        self.notify_observers('cell_changed', row=row, col=col)
    
    def get_cell_display_value(self, row: int, col: int) -> str:
        """Get cell value for display"""
        if (row, col) not in self.sheet.cells:
            return ""
        
        cell = self.sheet.cells[(row, col)]
        if cell.error:
            return cell.error
        
        value = cell.value
        if isinstance(value, float):
            precision = cell.format.get('precision', 2)
            return f"{value:.{precision}f}"
        return str(value)
    
    def to_dict(self) -> Dict:
        """Serialize model to dictionary"""
        cells_dict = {}
        for (row, col), cell in self.sheet.cells.items():
            cells_dict[f"{row},{col}"] = cell.to_dict()
        
        return {
            'sheet_name': self.sheet.name,
            'cells': cells_dict,
            'max_row': self.sheet.max_row,
            'max_col': self.sheet.max_col
        }
    
    def from_dict(self, data: Dict):
        """Deserialize model from dictionary"""
        self.sheet = Sheet()
        self.sheet.name = data.get('sheet_name', 'Sheet1')
        self.sheet.max_row = data.get('max_row', 0)
        self.sheet.max_col = data.get('max_col', 0)
        
        cells_dict = data.get('cells', {})
        for pos_str, cell_data in cells_dict.items():
            row, col = map(int, pos_str.split(','))
            self.sheet.cells[(row, col)] = Cell.from_dict(cell_data)
        
        self.modified = False
        self.notify_observers('model_loaded')