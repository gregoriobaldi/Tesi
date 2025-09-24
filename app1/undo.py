"""Undo/Redo system using QUndoStack."""

from PyQt6.QtGui import QUndoCommand
from typing import Any, Dict, Tuple
from model import CellData


class CellEditCommand(QUndoCommand):
    """Command for cell editing operations."""
    
    def __init__(self, model, row: int, col: int, old_data: CellData, new_raw: str):
        super().__init__(f"Edit {model.headerData(col, 1)} {row + 1}")
        self.model = model
        self.row = row
        self.col = col
        self.old_data = old_data
        self.new_raw = new_raw
        
    def redo(self):
        """Apply the edit."""
        index = self.model.index(self.row, self.col)
        self.model.setData(index, self.new_raw)
        
    def undo(self):
        """Revert the edit."""
        if self.old_data is None:
            self.model.clear_cell(self.row, self.col)
        else:
            if (self.row, self.col) not in self.model.cells:
                self.model.cells[(self.row, self.col)] = CellData()
            cell = self.model.cells[(self.row, self.col)]
            cell.raw = self.old_data.raw
            cell.value = self.old_data.value
            cell.bold = self.old_data.bold
            cell.precision = self.old_data.precision
            cell.error = self.old_data.error
            
        index = self.model.index(self.row, self.col)
        self.model.dataChanged.emit(index, index)


class FormatCommand(QUndoCommand):
    """Command for formatting operations."""
    
    def __init__(self, model, positions: list, property_name: str, old_values: list, new_value: Any):
        super().__init__(f"Format {property_name}")
        self.model = model
        self.positions = positions
        self.property_name = property_name
        self.old_values = old_values
        self.new_value = new_value
        
    def redo(self):
        """Apply formatting."""
        for (row, col) in self.positions:
            if (row, col) not in self.model.cells:
                self.model.cells[(row, col)] = CellData()
            setattr(self.model.cells[(row, col)], self.property_name, self.new_value)
            index = self.model.index(row, col)
            self.model.dataChanged.emit(index, index)
            
    def undo(self):
        """Revert formatting."""
        for i, (row, col) in enumerate(self.positions):
            if (row, col) in self.model.cells:
                setattr(self.model.cells[(row, col)], self.property_name, self.old_values[i])
                index = self.model.index(row, col)
                self.model.dataChanged.emit(index, index)