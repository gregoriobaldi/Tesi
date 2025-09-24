"""
Undo/Redo system with command pattern.
Supports multi-step operations and command stacking.
"""
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from model import SpreadsheetModel


class Command(ABC):
    """Abstract base class for undoable commands"""
    
    @abstractmethod
    def execute(self) -> bool:
        """Execute the command"""
        pass
    
    @abstractmethod
    def undo(self) -> bool:
        """Undo the command"""
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """Get human-readable description of the command"""
        pass


class SetCellCommand(Command):
    """Command to set cell content"""
    
    def __init__(self, model: SpreadsheetModel, row: int, col: int, new_raw: str, new_value: Any = None):
        self.model = model
        self.row = row
        self.col = col
        self.new_raw = new_raw
        self.new_value = new_value
        
        # Store old values for undo
        if (row, col) in model.sheet.cells:
            old_cell = model.sheet.cells[(row, col)]
            self.old_raw = old_cell.raw
            self.old_value = old_cell.value
            self.old_format = old_cell.format.copy()
            self.had_cell = True
        else:
            self.old_raw = ""
            self.old_value = ""
            self.old_format = {}
            self.had_cell = False
    
    def execute(self) -> bool:
        """Execute the set cell command"""
        try:
            self.model.set_cell_raw(self.row, self.col, self.new_raw)
            return True
        except Exception:
            return False
    
    def undo(self) -> bool:
        """Undo the set cell command"""
        try:
            if self.had_cell:
                self.model.sheet.set_cell(self.row, self.col, self.old_raw, self.old_value, self.old_format)
            else:
                self.model.sheet.delete_cell(self.row, self.col)
            
            self.model.notify_observers('cell_changed', row=self.row, col=self.col)
            return True
        except Exception:
            return False
    
    def get_description(self) -> str:
        from model import address_to_string
        return f"Set {address_to_string(self.row, self.col)}"


class InsertRowCommand(Command):
    """Command to insert a row"""
    
    def __init__(self, model: SpreadsheetModel, row: int):
        self.model = model
        self.row = row
    
    def execute(self) -> bool:
        try:
            self.model.sheet.insert_row(self.row)
            self.model.notify_observers('structure_changed')
            return True
        except Exception:
            return False
    
    def undo(self) -> bool:
        try:
            self.model.sheet.delete_row(self.row)
            self.model.notify_observers('structure_changed')
            return True
        except Exception:
            return False
    
    def get_description(self) -> str:
        return f"Insert row {self.row + 1}"


class DeleteRowCommand(Command):
    """Command to delete a row"""
    
    def __init__(self, model: SpreadsheetModel, row: int):
        self.model = model
        self.row = row
        
        # Store cells that will be deleted
        self.deleted_cells = {}
        for (r, c), cell in model.sheet.cells.items():
            if r == row:
                self.deleted_cells[(r, c)] = {
                    'raw': cell.raw,
                    'value': cell.value,
                    'format': cell.format.copy()
                }
    
    def execute(self) -> bool:
        try:
            self.model.sheet.delete_row(self.row)
            self.model.notify_observers('structure_changed')
            return True
        except Exception:
            return False
    
    def undo(self) -> bool:
        try:
            self.model.sheet.insert_row(self.row)
            
            # Restore deleted cells
            for (r, c), cell_data in self.deleted_cells.items():
                self.model.sheet.set_cell(r, c, cell_data['raw'], cell_data['value'], cell_data['format'])
            
            self.model.notify_observers('structure_changed')
            return True
        except Exception:
            return False
    
    def get_description(self) -> str:
        return f"Delete row {self.row + 1}"


class InsertColumnCommand(Command):
    """Command to insert a column"""
    
    def __init__(self, model: SpreadsheetModel, col: int):
        self.model = model
        self.col = col
    
    def execute(self) -> bool:
        try:
            self.model.sheet.insert_column(self.col)
            self.model.notify_observers('structure_changed')
            return True
        except Exception:
            return False
    
    def undo(self) -> bool:
        try:
            self.model.sheet.delete_column(self.col)
            self.model.notify_observers('structure_changed')
            return True
        except Exception:
            return False
    
    def get_description(self) -> str:
        from model import col_to_letter
        return f"Insert column {col_to_letter(self.col)}"


class DeleteColumnCommand(Command):
    """Command to delete a column"""
    
    def __init__(self, model: SpreadsheetModel, col: int):
        self.model = model
        self.col = col
        
        # Store cells that will be deleted
        self.deleted_cells = {}
        for (r, c), cell in model.sheet.cells.items():
            if c == col:
                self.deleted_cells[(r, c)] = {
                    'raw': cell.raw,
                    'value': cell.value,
                    'format': cell.format.copy()
                }
    
    def execute(self) -> bool:
        try:
            self.model.sheet.delete_column(self.col)
            self.model.notify_observers('structure_changed')
            return True
        except Exception:
            return False
    
    def undo(self) -> bool:
        try:
            self.model.sheet.insert_column(self.col)
            
            # Restore deleted cells
            for (r, c), cell_data in self.deleted_cells.items():
                self.model.sheet.set_cell(r, c, cell_data['raw'], cell_data['value'], cell_data['format'])
            
            self.model.notify_observers('structure_changed')
            return True
        except Exception:
            return False
    
    def get_description(self) -> str:
        from model import col_to_letter
        return f"Delete column {col_to_letter(self.col)}"


class FormatCellCommand(Command):
    """Command to format a cell"""
    
    def __init__(self, model: SpreadsheetModel, row: int, col: int, format_changes: Dict[str, Any]):
        self.model = model
        self.row = row
        self.col = col
        self.format_changes = format_changes
        
        # Store old format for undo
        cell = model.sheet.get_cell(row, col)
        self.old_format = cell.format.copy()
    
    def execute(self) -> bool:
        try:
            cell = self.model.sheet.get_cell(self.row, self.col)
            cell.format.update(self.format_changes)
            self.model.notify_observers('cell_changed', row=self.row, col=self.col)
            return True
        except Exception:
            return False
    
    def undo(self) -> bool:
        try:
            cell = self.model.sheet.get_cell(self.row, self.col)
            cell.format = self.old_format
            self.model.notify_observers('cell_changed', row=self.row, col=self.col)
            return True
        except Exception:
            return False
    
    def get_description(self) -> str:
        from model import address_to_string
        return f"Format {address_to_string(self.row, self.col)}"


class MacroCommand(Command):
    """Command that groups multiple commands together"""
    
    def __init__(self, commands: List[Command], description: str):
        self.commands = commands
        self.description = description
    
    def execute(self) -> bool:
        """Execute all commands in order"""
        executed = []
        
        for command in self.commands:
            if command.execute():
                executed.append(command)
            else:
                # Rollback executed commands
                for cmd in reversed(executed):
                    cmd.undo()
                return False
        
        return True
    
    def undo(self) -> bool:
        """Undo all commands in reverse order"""
        for command in reversed(self.commands):
            if not command.undo():
                return False
        return True
    
    def get_description(self) -> str:
        return self.description


class UndoRedoManager:
    """Manages undo/redo operations"""
    
    def __init__(self, max_history: int = 100):
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.max_history = max_history
    
    def execute_command(self, command: Command) -> bool:
        """Execute a command and add it to undo stack"""
        if command.execute():
            self.undo_stack.append(command)
            
            # Limit history size
            if len(self.undo_stack) > self.max_history:
                self.undo_stack.pop(0)
            
            # Clear redo stack when new command is executed
            self.redo_stack.clear()
            
            return True
        return False
    
    def can_undo(self) -> bool:
        """Check if undo is possible"""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """Check if redo is possible"""
        return len(self.redo_stack) > 0
    
    def undo(self) -> bool:
        """Undo the last command"""
        if not self.can_undo():
            return False
        
        command = self.undo_stack.pop()
        if command.undo():
            self.redo_stack.append(command)
            return True
        else:
            # If undo fails, put command back
            self.undo_stack.append(command)
            return False
    
    def redo(self) -> bool:
        """Redo the last undone command"""
        if not self.can_redo():
            return False
        
        command = self.redo_stack.pop()
        if command.execute():
            self.undo_stack.append(command)
            return True
        else:
            # If redo fails, put command back
            self.redo_stack.append(command)
            return False
    
    def get_undo_description(self) -> Optional[str]:
        """Get description of command that would be undone"""
        if self.can_undo():
            return self.undo_stack[-1].get_description()
        return None
    
    def get_redo_description(self) -> Optional[str]:
        """Get description of command that would be redone"""
        if self.can_redo():
            return self.redo_stack[-1].get_description()
        return None
    
    def clear_history(self):
        """Clear all undo/redo history"""
        self.undo_stack.clear()
        self.redo_stack.clear()
    
    def get_history_size(self) -> Tuple[int, int]:
        """Get size of undo and redo stacks"""
        return len(self.undo_stack), len(self.redo_stack)