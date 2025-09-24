"""Data model and address utilities for the spreadsheet."""

import re
from typing import Dict, Tuple, Any, Optional, Set
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex, pyqtSignal
from PyQt6.QtGui import QFont


class CellData:
    """Represents a single cell's data."""
    def __init__(self, raw: str = "", value: Any = "", bold: bool = False, precision: int = 2):
        self.raw = raw
        self.value = value
        self.bold = bold
        self.precision = precision
        self.error = None


def col_to_letter(col: int) -> str:
    """Convert column index to letter (0->A, 25->Z, 26->AA)."""
    result = ""
    while col >= 0:
        result = chr(col % 26 + ord('A')) + result
        col = col // 26 - 1
    return result


def letter_to_col(letter: str) -> int:
    """Convert column letter to index (A->0, Z->25, AA->26)."""
    result = 0
    for char in letter:
        result = result * 26 + ord(char) - ord('A') + 1
    return result - 1


def parse_cell_ref(ref: str) -> Tuple[int, int]:
    """Parse cell reference like 'A1' to (row, col)."""
    match = re.match(r'^([A-Z]+)(\d+)$', ref.upper())
    if not match:
        raise ValueError(f"Invalid cell reference: {ref}")
    col = letter_to_col(match.group(1))
    row = int(match.group(2)) - 1
    return row, col


def format_cell_ref(row: int, col: int) -> str:
    """Format (row, col) to cell reference like 'A1'."""
    return f"{col_to_letter(col)}{row + 1}"


def parse_range(range_str: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Parse range like 'A1:B5' to ((start_row, start_col), (end_row, end_col))."""
    parts = range_str.split(':')
    if len(parts) != 2:
        raise ValueError(f"Invalid range: {range_str}")
    start = parse_cell_ref(parts[0])
    end = parse_cell_ref(parts[1])
    return start, end


class SpreadsheetModel(QAbstractTableModel):
    """Table model for the spreadsheet."""
    
    cellChanged = pyqtSignal(int, int)
    
    def __init__(self):
        super().__init__()
        self.cells: Dict[Tuple[int, int], CellData] = {}
        self.max_row = 100
        self.max_col = 26
        
    def rowCount(self, parent=QModelIndex()) -> int:
        return self.max_row
        
    def columnCount(self, parent=QModelIndex()) -> int:
        return self.max_col
        
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return col_to_letter(section)
            else:
                return str(section + 1)
        return None
        
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
            
        row, col = index.row(), index.column()
        cell = self.cells.get((row, col))
        
        if role == Qt.ItemDataRole.DisplayRole:
            if cell and cell.error:
                return cell.error
            return str(cell.value) if cell else ""
        elif role == Qt.ItemDataRole.FontRole:
            if cell and cell.bold:
                font = QFont()
                font.setBold(True)
                return font
        elif role == Qt.ItemDataRole.ToolTipRole:
            if cell and cell.error:
                return f"Error: {cell.error}"
                
        return None
        
    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
            
        row, col = index.row(), index.column()
        if (row, col) not in self.cells:
            self.cells[(row, col)] = CellData()
            
        self.cells[(row, col)].raw = str(value)
        self.dataChanged.emit(index, index)
        self.cellChanged.emit(row, col)
        return True
        
    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if index.isValid():
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable
        return Qt.ItemFlag.NoItemFlags
        
    def get_cell(self, row: int, col: int) -> Optional[CellData]:
        """Get cell data at position."""
        return self.cells.get((row, col))
        
    def set_cell_value(self, row: int, col: int, value: Any, error: str = None):
        """Set cell computed value."""
        if (row, col) not in self.cells:
            self.cells[(row, col)] = CellData()
        self.cells[(row, col)].value = value
        self.cells[(row, col)].error = error
        index = self.index(row, col)
        self.dataChanged.emit(index, index)
        
    def get_range_values(self, start: Tuple[int, int], end: Tuple[int, int]) -> list:
        """Get values in a range."""
        values = []
        start_row, start_col = start
        end_row, end_col = end
        for row in range(start_row, end_row + 1):
            for col in range(start_col, end_col + 1):
                cell = self.cells.get((row, col))
                if cell and isinstance(cell.value, (int, float)):
                    values.append(cell.value)
        return values
        
    def clear_cell(self, row: int, col: int):
        """Clear a cell."""
        if (row, col) in self.cells:
            del self.cells[(row, col)]
            index = self.index(row, col)
            self.dataChanged.emit(index, index)