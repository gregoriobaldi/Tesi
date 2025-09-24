"""
Main UI module using tkinter.
Implements the spreadsheet interface with grid, menus, and dialogs.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import re
from typing import Optional, Tuple, List, Set, Dict, Any

from model import SpreadsheetModel, address_to_string, parse_address, col_to_letter
from engine import CalculationEngine
from storage import StorageManager
from undo import UndoRedoManager, SetCellCommand, InsertRowCommand, DeleteRowCommand, InsertColumnCommand, DeleteColumnCommand, FormatCellCommand


class FindReplaceDialog:
    """Find and Replace dialog"""
    
    def __init__(self, parent, spreadsheet_ui):
        self.parent = parent
        self.ui = spreadsheet_ui
        self.dialog = None
        self.find_var = tk.StringVar()
        self.replace_var = tk.StringVar()
        self.regex_var = tk.BooleanVar()
        self.match_case_var = tk.BooleanVar()
        
    def show(self):
        if self.dialog:
            self.dialog.lift()
            return
            
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Find & Replace")
        self.dialog.geometry("400x200")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Find frame
        find_frame = ttk.Frame(self.dialog)
        find_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(find_frame, text="Find:").pack(side='left')
        find_entry = ttk.Entry(find_frame, textvariable=self.find_var, width=30)
        find_entry.pack(side='right', fill='x', expand=True)
        
        # Replace frame
        replace_frame = ttk.Frame(self.dialog)
        replace_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(replace_frame, text="Replace:").pack(side='left')
        ttk.Entry(replace_frame, textvariable=self.replace_var, width=30).pack(side='right', fill='x', expand=True)
        
        # Options frame
        options_frame = ttk.Frame(self.dialog)
        options_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Checkbutton(options_frame, text="Regular Expression", variable=self.regex_var).pack(side='left')
        ttk.Checkbutton(options_frame, text="Match Case", variable=self.match_case_var).pack(side='left')
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.dialog)
        buttons_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Find Next", command=self.find_next).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Replace", command=self.replace_current).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Replace All", command=self.replace_all).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Close", command=self.close).pack(side='right', padx=5)
        
        find_entry.focus()
        self.dialog.protocol("WM_DELETE_WINDOW", self.close)
    
    def find_next(self):
        # Placeholder implementation
        messagebox.showinfo("Find", "Find functionality not fully implemented")
    
    def replace_current(self):
        # Placeholder implementation
        messagebox.showinfo("Replace", "Replace functionality not fully implemented")
    
    def replace_all(self):
        # Placeholder implementation
        messagebox.showinfo("Replace All", "Replace All functionality not fully implemented")
    
    def close(self):
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None


class GoToCellDialog:
    """Go to Cell dialog"""
    
    def __init__(self, parent, spreadsheet_ui):
        self.parent = parent
        self.ui = spreadsheet_ui
        self.result = None
    
    def show(self) -> Optional[Tuple[int, int]]:
        dialog = tk.Toplevel(self.parent)
        dialog.title("Go to Cell")
        dialog.geometry("300x120")
        dialog.transient(self.parent)
        dialog.grab_set()
        
        # Address frame
        addr_frame = ttk.Frame(dialog)
        addr_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(addr_frame, text="Cell Address:").pack(side='left')
        addr_var = tk.StringVar()
        addr_entry = ttk.Entry(addr_frame, textvariable=addr_var, width=10)
        addr_entry.pack(side='right')
        
        # Buttons frame
        buttons_frame = ttk.Frame(dialog)
        buttons_frame.pack(fill='x', padx=10, pady=10)
        
        def go_to():
            try:
                address = addr_var.get().strip().upper()
                row, col = parse_address(address)
                self.result = (row, col)
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Invalid cell address")
        
        def cancel():
            self.result = None
            dialog.destroy()
        
        ttk.Button(buttons_frame, text="Go", command=go_to).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=cancel).pack(side='right', padx=5)
        
        addr_entry.focus()
        addr_entry.bind('<Return>', lambda e: go_to())
        
        dialog.wait_window()
        return self.result


class SpreadsheetGrid(ttk.Frame):
    """Custom spreadsheet grid widget using Canvas"""
    
    def __init__(self, parent, model: SpreadsheetModel, **kwargs):
        super().__init__(parent, **kwargs)
        self.model = model
        self.visible_rows = 30
        self.visible_cols = 15
        self.selected_cell = (0, 0)
        self.cell_width = 80
        self.cell_height = 25
        self.header_width = 50
        self.header_height = 25
        self.editing_cell = None
        self.edit_widget = None
        
        self.setup_grid()
        self.setup_bindings()
    
    def setup_grid(self):
        # Create canvas with scrollbars
        self.canvas = tk.Canvas(self, bg='white', highlightthickness=0)
        
        v_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(self, orient='horizontal', command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Set scroll region
        total_width = self.header_width + self.visible_cols * self.cell_width
        total_height = self.header_height + self.visible_rows * self.cell_height
        self.canvas.configure(scrollregion=(0, 0, total_width, total_height))
        
        self.draw_grid()
    
    def setup_bindings(self):
        self.canvas.bind('<Button-1>', self.on_cell_click)
        self.canvas.bind('<Double-Button-1>', self.on_cell_double_click)
        self.canvas.bind('<Key>', self.on_key_press)
        self.canvas.focus_set()
        self.bind_all('<Key>', self.on_key_press)
    
    def draw_grid(self):
        self.canvas.delete('all')
        
        # Draw column headers
        for col in range(self.visible_cols):
            x1 = self.header_width + col * self.cell_width
            x2 = x1 + self.cell_width
            y1 = 0
            y2 = self.header_height
            
            self.canvas.create_rectangle(x1, y1, x2, y2, fill='lightgray', outline='black')
            self.canvas.create_text(x1 + self.cell_width//2, y1 + self.header_height//2, 
                                  text=col_to_letter(col), font=('Arial', 9, 'bold'))
        
        # Draw row headers
        for row in range(self.visible_rows):
            x1 = 0
            x2 = self.header_width
            y1 = self.header_height + row * self.cell_height
            y2 = y1 + self.cell_height
            
            self.canvas.create_rectangle(x1, y1, x2, y2, fill='lightgray', outline='black')
            self.canvas.create_text(x1 + self.header_width//2, y1 + self.cell_height//2, 
                                  text=str(row + 1), font=('Arial', 9, 'bold'))
        
        # Draw cells
        for row in range(self.visible_rows):
            for col in range(self.visible_cols):
                x1 = self.header_width + col * self.cell_width
                x2 = x1 + self.cell_width
                y1 = self.header_height + row * self.cell_height
                y2 = y1 + self.cell_height
                
                # Cell background
                fill_color = 'lightblue' if (row, col) == self.selected_cell else 'white'
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill_color, outline='gray')
                
                # Cell content
                cell_value = self.model.get_cell_display_value(row, col)
                if cell_value:
                    # Check for errors
                    if isinstance(cell_value, str) and cell_value.startswith('#'):
                        text_color = 'red'
                    else:
                        text_color = 'black'
                    
                    self.canvas.create_text(x1 + 5, y1 + self.cell_height//2, 
                                          text=str(cell_value)[:10], anchor='w', 
                                          font=('Arial', 9), fill=text_color)
    
    def on_cell_click(self, event):
        # Convert canvas coordinates to cell coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        if canvas_x < self.header_width or canvas_y < self.header_height:
            return
        
        col = int((canvas_x - self.header_width) // self.cell_width)
        row = int((canvas_y - self.header_height) // self.cell_height)
        
        if 0 <= row < self.visible_rows and 0 <= col < self.visible_cols:
            self.select_cell(row, col)
    
    def on_cell_double_click(self, event):
        self.start_edit()
    
    def on_key_press(self, event):
        if event.keysym == 'Return':
            if self.editing_cell:
                self.finish_edit()
            else:
                self.move_selection(1, 0)
        elif event.keysym == 'Tab':
            self.move_selection(0, 1)
        elif event.keysym == 'F2':
            self.start_edit()
        elif event.keysym in ['Up', 'Down', 'Left', 'Right']:
            self.handle_arrow_key(event.keysym)
        elif event.char and event.char.isprintable() and not self.editing_cell:
            self.start_edit(event.char)
    
    def select_cell(self, row: int, col: int):
        self.selected_cell = (row, col)
        self.draw_grid()
        
        # Notify parent of selection change
        if hasattr(self.master, 'on_cell_selected'):
            self.master.on_cell_selected(row, col)
    
    def move_selection(self, row_delta: int, col_delta: int):
        new_row = max(0, min(self.visible_rows - 1, self.selected_cell[0] + row_delta))
        new_col = max(0, min(self.visible_cols - 1, self.selected_cell[1] + col_delta))
        self.select_cell(new_row, new_col)
    
    def handle_arrow_key(self, key):
        if key == 'Up':
            self.move_selection(-1, 0)
        elif key == 'Down':
            self.move_selection(1, 0)
        elif key == 'Left':
            self.move_selection(0, -1)
        elif key == 'Right':
            self.move_selection(0, 1)
    
    def start_edit(self, initial_char: str = ""):
        if self.editing_cell:
            return
        
        row, col = self.selected_cell
        self.editing_cell = (row, col)
        
        # Get current cell value
        cell = self.model.sheet.get_cell(row, col)
        current_value = cell.raw if initial_char == "" else initial_char
        
        # Calculate edit widget position
        x = self.header_width + col * self.cell_width
        y = self.header_height + row * self.cell_height
        
        # Create edit widget
        self.edit_var = tk.StringVar(value=current_value)
        self.edit_widget = tk.Entry(self.canvas, textvariable=self.edit_var, 
                                   font=('Arial', 9), relief='solid', bd=2)
        self.canvas.create_window(x + 2, y + 2, window=self.edit_widget, 
                                anchor='nw', width=self.cell_width - 4, 
                                height=self.cell_height - 4)
        self.edit_widget.focus()
        self.edit_widget.bind('<Return>', lambda e: self.finish_edit())
        self.edit_widget.bind('<Escape>', lambda e: self.cancel_edit())
    
    def finish_edit(self):
        if not self.editing_cell or not self.edit_widget:
            return
        
        row, col = self.editing_cell
        new_value = self.edit_var.get()
        
        # Update model through parent
        if hasattr(self.master, 'set_cell_value'):
            self.master.set_cell_value(row, col, new_value)
        
        self.cancel_edit()
        self.draw_grid()
    
    def cancel_edit(self):
        if self.edit_widget:
            self.edit_widget.destroy()
            self.edit_widget = None
        self.editing_cell = None
        self.canvas.focus_set()


class SpreadsheetUI:
    """Main spreadsheet UI class"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Spreadsheet Lite")
        self.root.geometry("1000x700")
        
        # Initialize components
        self.model = SpreadsheetModel()
        self.engine = CalculationEngine(self.model)
        self.storage = StorageManager(self.model)
        self.undo_manager = UndoRedoManager()
        
        # UI state
        self.clipboard_data = ""
        
        # Setup UI
        self.setup_menu()
        self.setup_toolbar()
        self.setup_formula_bar()
        self.setup_grid()
        self.setup_status_bar()
        self.setup_bindings()
        
        # Model observers
        self.model.add_observer(self.on_model_changed)
        
        # Dialogs
        self.find_dialog = FindReplaceDialog(self.root, self)
    
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_command(label="Import CSV...", command=self.import_csv)
        file_menu.add_command(label="Export CSV...", command=self.export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Find & Replace...", command=self.show_find_replace, accelerator="Ctrl+F")
        
        # Insert menu
        insert_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Insert", menu=insert_menu)
        insert_menu.add_command(label="Row Above", command=self.insert_row_above)
        insert_menu.add_command(label="Row Below", command=self.insert_row_below)
        insert_menu.add_command(label="Column Left", command=self.insert_column_left)
        insert_menu.add_command(label="Column Right", command=self.insert_column_right)
        
        # Format menu
        format_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Format", menu=format_menu)
        format_menu.add_command(label="Bold", command=self.toggle_bold)
        
        precision_menu = tk.Menu(format_menu, tearoff=0)
        format_menu.add_cascade(label="Number Precision", menu=precision_menu)
        for i in range(7):
            precision_menu.add_command(label=str(i), command=lambda p=i: self.set_precision(p))
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Recalculate All", command=self.recalculate_all)
        tools_menu.add_command(label="Go to Cell...", command=self.go_to_cell, accelerator="Ctrl+G")
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
    
    def setup_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill='x', padx=5, pady=2)
        
        ttk.Button(toolbar, text="New", command=self.new_file).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Open", command=self.open_file).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_file).pack(side='left', padx=2)
        
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5)
        
        ttk.Button(toolbar, text="Undo", command=self.undo).pack(side='left', padx=2)
        ttk.Button(toolbar, text="Redo", command=self.redo).pack(side='left', padx=2)
        
        ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5)
        
        ttk.Button(toolbar, text="Bold", command=self.toggle_bold).pack(side='left', padx=2)
    
    def setup_formula_bar(self):
        formula_frame = ttk.Frame(self.root)
        formula_frame.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(formula_frame, text="Formula:").pack(side='left')
        
        self.formula_var = tk.StringVar()
        self.formula_entry = ttk.Entry(formula_frame, textvariable=self.formula_var)
        self.formula_entry.pack(side='left', fill='x', expand=True, padx=5)
        self.formula_entry.bind('<Return>', self.on_formula_enter)
    
    def setup_grid(self):
        self.grid = SpreadsheetGrid(self.root, self.model)
        self.grid.pack(fill='both', expand=True, padx=5, pady=5)
    
    def setup_status_bar(self):
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken')
        status_bar.pack(fill='x', side='bottom')
    
    def setup_bindings(self):
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Control-y>', lambda e: self.redo())
        self.root.bind('<Control-c>', lambda e: self.copy())
        self.root.bind('<Control-v>', lambda e: self.paste())
        self.root.bind('<Control-x>', lambda e: self.cut())
        self.root.bind('<Control-f>', lambda e: self.show_find_replace())
        self.root.bind('<Control-g>', lambda e: self.go_to_cell())
    
    def on_cell_selected(self, row: int, col: int):
        """Called when a cell is selected in the grid"""
        cell = self.model.sheet.get_cell(row, col)
        self.formula_var.set(cell.raw)
        
        # Update status bar
        addr = address_to_string(row, col)
        self.status_var.set(f"Cell: {addr}")
    
    def on_formula_enter(self, event=None):
        """Called when formula is entered in formula bar"""
        row, col = self.grid.selected_cell
        formula = self.formula_var.get()
        self.set_cell_value(row, col, formula)
    
    def set_cell_value(self, row: int, col: int, value: str):
        """Set cell value through undo system"""
        command = SetCellCommand(self.model, row, col, value)
        self.undo_manager.execute_command(command)
        
        # Update calculation engine
        if value.startswith('='):
            self.engine.set_cell_formula(row, col, value)
        else:
            self.engine.mark_dirty((row, col))
            self.engine.recalculate()
    
    def on_model_changed(self, event_type: str, **kwargs):
        """Handle model change events"""
        if event_type == 'cell_changed':
            self.grid.draw_grid()
        elif event_type == 'structure_changed':
            self.grid.draw_grid()
        elif event_type == 'model_loaded':
            self.grid.draw_grid()
    
    # File operations
    def new_file(self):
        if self.model.modified:
            if not messagebox.askyesno("New File", "Discard unsaved changes?"):
                return
        
        self.model = SpreadsheetModel()
        self.engine = CalculationEngine(self.model)
        self.storage = StorageManager(self.model)
        self.model.add_observer(self.on_model_changed)
        self.undo_manager.clear_history()
        self.grid.model = self.model
        self.grid.draw_grid()
        self.root.title("Spreadsheet Lite - Untitled")
    
    def open_file(self):
        filename = filedialog.askopenfilename(
            title="Open Spreadsheet",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            if self.storage.load_json(filename):
                self.engine = CalculationEngine(self.model)
                self.engine.recalculate_all()
                self.grid.draw_grid()
                self.root.title(f"Spreadsheet Lite - {filename}")
            else:
                messagebox.showerror("Error", "Failed to open file")
    
    def save_file(self):
        if self.model.filename:
            if self.storage.save_json(self.model.filename):
                self.root.title(f"Spreadsheet Lite - {self.model.filename}")
            else:
                messagebox.showerror("Error", "Failed to save file")
        else:
            self.save_as_file()
    
    def save_as_file(self):
        filename = filedialog.asksaveasfilename(
            title="Save Spreadsheet",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            if self.storage.save_json(filename):
                self.root.title(f"Spreadsheet Lite - {filename}")
            else:
                messagebox.showerror("Error", "Failed to save file")
    
    def import_csv(self):
        filename = filedialog.askopenfilename(
            title="Import CSV",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            if self.storage.import_csv(filename):
                self.engine.recalculate_all()
                self.grid.draw_grid()
                messagebox.showinfo("Success", "CSV imported successfully")
            else:
                messagebox.showerror("Error", "Failed to import CSV")
    
    def export_csv(self):
        filename = filedialog.asksaveasfilename(
            title="Export CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            if self.storage.export_csv(filename):
                messagebox.showinfo("Success", "CSV exported successfully")
            else:
                messagebox.showerror("Error", "Failed to export CSV")
    
    # Edit operations
    def undo(self):
        if self.undo_manager.undo():
            self.grid.draw_grid()
    
    def redo(self):
        if self.undo_manager.redo():
            self.grid.draw_grid()
    
    def copy(self):
        row, col = self.grid.selected_cell
        cell = self.model.sheet.get_cell(row, col)
        self.clipboard_data = cell.raw
        self.root.clipboard_clear()
        self.root.clipboard_append(self.clipboard_data)
    
    def cut(self):
        self.copy()
        row, col = self.grid.selected_cell
        self.set_cell_value(row, col, "")
    
    def paste(self):
        try:
            data = self.root.clipboard_get()
            row, col = self.grid.selected_cell
            self.set_cell_value(row, col, data)
        except tk.TclError:
            pass  # No clipboard data
    
    # Insert operations
    def insert_row_above(self):
        row, col = self.grid.selected_cell
        command = InsertRowCommand(self.model, row)
        self.undo_manager.execute_command(command)
    
    def insert_row_below(self):
        row, col = self.grid.selected_cell
        command = InsertRowCommand(self.model, row + 1)
        self.undo_manager.execute_command(command)
    
    def insert_column_left(self):
        row, col = self.grid.selected_cell
        command = InsertColumnCommand(self.model, col)
        self.undo_manager.execute_command(command)
    
    def insert_column_right(self):
        row, col = self.grid.selected_cell
        command = InsertColumnCommand(self.model, col + 1)
        self.undo_manager.execute_command(command)
    
    # Format operations
    def toggle_bold(self):
        row, col = self.grid.selected_cell
        cell = self.model.sheet.get_cell(row, col)
        current_bold = cell.format.get('bold', False)
        
        command = FormatCellCommand(self.model, row, col, {'bold': not current_bold})
        self.undo_manager.execute_command(command)
    
    def set_precision(self, precision: int):
        row, col = self.grid.selected_cell
        command = FormatCellCommand(self.model, row, col, {'precision': precision})
        self.undo_manager.execute_command(command)
    
    # Tools
    def recalculate_all(self):
        self.engine.recalculate_all()
        self.grid.draw_grid()
    
    def go_to_cell(self):
        dialog = GoToCellDialog(self.root, self)
        result = dialog.show()
        if result:
            row, col = result
            self.grid.select_cell(row, col)
    
    def show_find_replace(self):
        self.find_dialog.show()
    
    def show_about(self):
        messagebox.showinfo("About", 
            "Spreadsheet Lite v1.0\n\n"
            "A lightweight spreadsheet application built with Python and tkinter.\n\n"
            "Features:\n"
            "• Formula support with built-in functions\n"
            "• Undo/Redo operations\n"
            "• CSV import/export\n"
            "• Find & Replace\n"
            "• Cell formatting")
    
    def run(self):
        """Start the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = SpreadsheetUI()
    app.run()