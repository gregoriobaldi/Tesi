"""Main UI window and dialogs."""

import sys
import os

# Apply Qt compatibility fixes
try:
    from qt_fix import fix_qt_import
    fix_qt_import()
except ImportError:
    pass

from typing import Set, Dict, Tuple, Optional
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
                            QWidget, QTableView, QLineEdit, QMenuBar, QToolBar, 
                            QStatusBar, QDialog, QDialogButtonBox, QLabel, QCheckBox,
                            QMessageBox, QFileDialog, QHeaderView, QAbstractItemView)
from PyQt6.QtCore import Qt, QModelIndex, pyqtSignal
from PyQt6.QtGui import QAction, QKeySequence, QUndoStack, QFont

from model import SpreadsheetModel, CellData, format_cell_ref, parse_cell_ref
from formula import evaluate_formula, parse_formula
from storage import WorkbookStorage
from undo import CellEditCommand, FormatCommand


class FindReplaceDialog(QDialog):
    """Find and replace dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Find & Replace")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Find section
        find_layout = QHBoxLayout()
        find_layout.addWidget(QLabel("Find:"))
        self.find_edit = QLineEdit()
        find_layout.addWidget(self.find_edit)
        layout.addLayout(find_layout)
        
        # Replace section
        replace_layout = QHBoxLayout()
        replace_layout.addWidget(QLabel("Replace:"))
        self.replace_edit = QLineEdit()
        replace_layout.addWidget(self.replace_edit)
        layout.addLayout(replace_layout)
        
        # Options
        self.regex_check = QCheckBox("Use Regular Expressions")
        self.formulas_check = QCheckBox("Search in Formulas")
        layout.addWidget(self.regex_check)
        layout.addWidget(self.formulas_check)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)


class GotoCellDialog(QDialog):
    """Go to cell dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Go To Cell")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        cell_layout = QHBoxLayout()
        cell_layout.addWidget(QLabel("Cell:"))
        self.cell_edit = QLineEdit()
        self.cell_edit.setPlaceholderText("e.g., A1, B5")
        cell_layout.addWidget(self.cell_edit)
        layout.addLayout(cell_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
    def get_cell_reference(self) -> str:
        return self.cell_edit.text().strip().upper()


class AboutDialog(QDialog):
    """About dialog."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Spreadsheet")
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Spreadsheet Lite v1.0"))
        layout.addWidget(QLabel("A simple spreadsheet application built with PyQt6"))
        layout.addWidget(QLabel("Features: Formulas, Functions, Import/Export"))
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        
        self.setLayout(layout)


class DependencyTracker:
    """Tracks cell dependencies for recalculation."""
    
    def __init__(self):
        self.dependencies: Dict[Tuple[int, int], Set[Tuple[int, int]]] = {}
        self.dependents: Dict[Tuple[int, int], Set[Tuple[int, int]]] = {}
        
    def clear_dependencies(self, cell: Tuple[int, int]):
        """Clear all dependencies for a cell."""
        if cell in self.dependencies:
            for dep in self.dependencies[cell]:
                if dep in self.dependents:
                    self.dependents[dep].discard(cell)
            del self.dependencies[cell]
            
    def add_dependency(self, cell: Tuple[int, int], depends_on: Tuple[int, int]):
        """Add a dependency relationship."""
        if cell not in self.dependencies:
            self.dependencies[cell] = set()
        self.dependencies[cell].add(depends_on)
        
        if depends_on not in self.dependents:
            self.dependents[depends_on] = set()
        self.dependents[depends_on].add(cell)
        
    def get_dependents(self, cell: Tuple[int, int]) -> Set[Tuple[int, int]]:
        """Get all cells that depend on this cell."""
        return self.dependents.get(cell, set())
        
    def has_cycle(self, cell: Tuple[int, int], visited: Set[Tuple[int, int]] = None) -> bool:
        """Check if there's a circular dependency."""
        if visited is None:
            visited = set()
            
        if cell in visited:
            return True
            
        visited.add(cell)
        for dep in self.dependencies.get(cell, set()):
            if self.has_cycle(dep, visited.copy()):
                return True
        return False


class SpreadsheetWindow(QMainWindow):
    """Main spreadsheet window."""
    
    def __init__(self):
        super().__init__()
        self.model = SpreadsheetModel()
        self.dependency_tracker = DependencyTracker()
        self.undo_stack = QUndoStack()
        self.current_file = None
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Spreadsheet Lite")
        self.setGeometry(100, 100, 800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Formula bar
        formula_layout = QHBoxLayout()
        formula_layout.addWidget(QLabel("Formula:"))
        self.formula_bar = QLineEdit()
        formula_layout.addWidget(self.formula_bar)
        layout.addLayout(formula_layout)
        
        # Table view
        self.table_view = QTableView()
        self.table_view.setModel(self.model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectItems)
        self.table_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Resize columns to fit content
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setDefaultSectionSize(80)
        
        layout.addWidget(self.table_view)
        
        # Menu bar
        self.create_menu_bar()
        
        # Tool bar
        self.create_tool_bar()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_file)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        import_action = QAction("Import CSV", self)
        import_action.triggered.connect(self.import_csv)
        file_menu.addAction(import_action)
        
        export_action = QAction("Export CSV", self)
        export_action.triggered.connect(self.export_csv)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("Edit")
        
        undo_action = self.undo_stack.createUndoAction(self, "Undo")
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        edit_menu.addAction(undo_action)
        
        redo_action = self.undo_stack.createRedoAction(self, "Redo")
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        find_action = QAction("Find & Replace", self)
        find_action.setShortcut(QKeySequence.StandardKey.Find)
        find_action.triggered.connect(self.show_find_replace)
        edit_menu.addAction(find_action)
        
        goto_action = QAction("Go To Cell", self)
        goto_action.setShortcut(QKeySequence("Ctrl+G"))
        goto_action.triggered.connect(self.show_goto_cell)
        edit_menu.addAction(goto_action)
        
        # Format menu
        format_menu = menubar.addMenu("Format")
        
        bold_action = QAction("Bold", self)
        bold_action.setShortcut(QKeySequence.StandardKey.Bold)
        bold_action.triggered.connect(self.toggle_bold)
        format_menu.addAction(bold_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_tool_bar(self):
        """Create the tool bar."""
        toolbar = self.addToolBar("Main")
        
        new_action = QAction("New", self)
        new_action.triggered.connect(self.new_file)
        toolbar.addAction(new_action)
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        toolbar.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_file)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        bold_action = QAction("Bold", self)
        bold_action.triggered.connect(self.toggle_bold)
        toolbar.addAction(bold_action)
        
    def setup_connections(self):
        """Setup signal connections."""
        self.table_view.selectionModel().currentChanged.connect(self.on_selection_changed)
        self.formula_bar.returnPressed.connect(self.on_formula_entered)
        self.model.cellChanged.connect(self.on_cell_changed)
        
    def on_selection_changed(self, current: QModelIndex, previous: QModelIndex):
        """Handle selection change in table."""
        if current.isValid():
            row, col = current.row(), current.column()
            cell = self.model.get_cell(row, col)
            
            # Update formula bar
            if cell and cell.raw:
                self.formula_bar.setText(cell.raw)
            else:
                self.formula_bar.clear()
                
            # Update status bar
            cell_ref = format_cell_ref(row, col)
            self.status_bar.showMessage(f"Cell: {cell_ref}")
            
    def on_formula_entered(self):
        """Handle formula entry."""
        current = self.table_view.currentIndex()
        if not current.isValid():
            return
            
        row, col = current.row(), current.column()
        formula = self.formula_bar.text()
        
        # Create undo command
        old_cell = self.model.get_cell(row, col)
        old_data = CellData(old_cell.raw, old_cell.value, old_cell.bold, old_cell.precision) if old_cell else None
        
        command = CellEditCommand(self.model, row, col, old_data, formula)
        self.undo_stack.push(command)
        
    def on_cell_changed(self, row: int, col: int):
        """Handle cell content change."""
        cell = self.model.get_cell(row, col)
        if not cell:
            return
            
        # Clear old dependencies
        self.dependency_tracker.clear_dependencies((row, col))
        
        # Evaluate formula
        if cell.raw.startswith('='):
            try:
                # Parse to find dependencies
                ast = parse_formula(cell.raw)
                self.extract_dependencies(ast, row, col)
                
                # Check for cycles
                if self.dependency_tracker.has_cycle((row, col)):
                    self.model.set_cell_value(row, col, "", "#CYCLE!")
                else:
                    # Evaluate formula
                    result = evaluate_formula(cell.raw, self.model)
                    if isinstance(result, str) and result.startswith('#'):
                        self.model.set_cell_value(row, col, "", result)
                    else:
                        self.model.set_cell_value(row, col, result)
            except Exception:
                self.model.set_cell_value(row, col, "", "#VALUE!")
        else:
            # Try to convert to number
            try:
                value = float(cell.raw) if '.' in cell.raw else int(cell.raw)
                self.model.set_cell_value(row, col, value)
            except ValueError:
                self.model.set_cell_value(row, col, cell.raw)
                
        # Recalculate dependents
        self.recalculate_dependents((row, col))
        
    def extract_dependencies(self, node, cell_row: int, cell_col: int):
        """Extract cell dependencies from AST."""
        from formula import CellRefNode, RangeNode, BinaryOpNode, UnaryOpNode, FunctionNode
        
        if isinstance(node, CellRefNode):
            self.dependency_tracker.add_dependency((cell_row, cell_col), (node.row, node.col))
        elif isinstance(node, RangeNode):
            start_row, start_col = node.start
            end_row, end_col = node.end
            for row in range(start_row, end_row + 1):
                for col in range(start_col, end_col + 1):
                    self.dependency_tracker.add_dependency((cell_row, cell_col), (row, col))
        elif isinstance(node, (BinaryOpNode, UnaryOpNode)):
            if hasattr(node, 'left'):
                self.extract_dependencies(node.left, cell_row, cell_col)
            if hasattr(node, 'right'):
                self.extract_dependencies(node.right, cell_row, cell_col)
            if hasattr(node, 'operand'):
                self.extract_dependencies(node.operand, cell_row, cell_col)
        elif isinstance(node, FunctionNode):
            for arg in node.args:
                self.extract_dependencies(arg, cell_row, cell_col)
                
    def recalculate_dependents(self, cell: Tuple[int, int]):
        """Recalculate all cells that depend on the given cell."""
        dependents = self.dependency_tracker.get_dependents(cell)
        for dep_row, dep_col in dependents:
            self.on_cell_changed(dep_row, dep_col)
            
    def new_file(self):
        """Create a new file."""
        self.model.cells.clear()
        self.dependency_tracker = DependencyTracker()
        self.undo_stack.clear()
        self.current_file = None
        self.setWindowTitle("Spreadsheet Lite - Untitled")
        self.model.layoutChanged.emit()
        
    def open_file(self):
        """Open a file."""
        filename, _ = QFileDialog.getOpenFileName(self, "Open Workbook", "", "JSON Files (*.json)")
        if filename:
            cells = WorkbookStorage.load_from_json(filename)
            self.model.cells = cells
            self.current_file = filename
            self.setWindowTitle(f"Spreadsheet Lite - {os.path.basename(filename)}")
            self.model.layoutChanged.emit()
            
            # Recalculate all formulas
            for (row, col), cell in cells.items():
                if cell.raw.startswith('='):
                    self.on_cell_changed(row, col)
                    
    def save_file(self):
        """Save the current file."""
        if self.current_file:
            WorkbookStorage.save_to_json(self.model.cells, self.current_file)
            self.status_bar.showMessage("File saved", 2000)
        else:
            self.save_file_as()
            
    def save_file_as(self):
        """Save file with new name."""
        filename, _ = QFileDialog.getSaveFileName(self, "Save Workbook", "", "JSON Files (*.json)")
        if filename:
            WorkbookStorage.save_to_json(self.model.cells, filename)
            self.current_file = filename
            self.setWindowTitle(f"Spreadsheet Lite - {os.path.basename(filename)}")
            self.status_bar.showMessage("File saved", 2000)
            
    def import_csv(self):
        """Import CSV file."""
        filename, _ = QFileDialog.getOpenFileName(self, "Import CSV", "", "CSV Files (*.csv)")
        if filename:
            cells = WorkbookStorage.import_from_csv(filename)
            self.model.cells.update(cells)
            self.model.layoutChanged.emit()
            self.status_bar.showMessage("CSV imported", 2000)
            
    def export_csv(self):
        """Export to CSV file."""
        filename, _ = QFileDialog.getSaveFileName(self, "Export CSV", "", "CSV Files (*.csv)")
        if filename:
            WorkbookStorage.export_to_csv(self.model.cells, filename)
            self.status_bar.showMessage("CSV exported", 2000)
            
    def show_find_replace(self):
        """Show find and replace dialog."""
        dialog = FindReplaceDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # TODO: Implement find/replace functionality
            self.status_bar.showMessage("Find/Replace not yet implemented", 2000)
            
    def show_goto_cell(self):
        """Show go to cell dialog."""
        dialog = GotoCellDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                cell_ref = dialog.get_cell_reference()
                row, col = parse_cell_ref(cell_ref)
                index = self.model.index(row, col)
                self.table_view.setCurrentIndex(index)
                self.table_view.scrollTo(index)
            except ValueError:
                QMessageBox.warning(self, "Invalid Cell", "Please enter a valid cell reference (e.g., A1)")
                
    def show_about(self):
        """Show about dialog."""
        dialog = AboutDialog(self)
        dialog.exec()
        
    def toggle_bold(self):
        """Toggle bold formatting for selected cell."""
        current = self.table_view.currentIndex()
        if not current.isValid():
            return
            
        row, col = current.row(), current.column()
        cell = self.model.get_cell(row, col)
        
        old_bold = cell.bold if cell else False
        new_bold = not old_bold
        
        command = FormatCommand(self.model, [(row, col)], "bold", [old_bold], new_bold)
        self.undo_stack.push(command)


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = SpreadsheetWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()