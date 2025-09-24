"""Tkinter-based UI as fallback for PyQt6 issues."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os

# Simple model classes for tkinter version
class CellData:
    def __init__(self, raw="", value=""):
        self.raw = raw
        self.value = value

class SimpleModel:
    def __init__(self):
        self.cells = {}
    
    def get_cell(self, row, col):
        return self.cells.get((row, col))

def format_cell_ref(row, col):
    return chr(ord('A') + col) + str(row + 1)

def evaluate_simple_formula(formula):
    if formula.startswith('='):
        try:
            # Simple evaluation - just basic math
            expr = formula[1:].replace('^', '**')
            return eval(expr)
        except:
            return "#ERROR!"
    return formula

# Simple storage
class SimpleStorage:
    @staticmethod
    def save_to_json(cells, filename):
        import json
        data = {}
        for (row, col), cell in cells.items():
            key = format_cell_ref(row, col)
            data[key] = {"raw": cell.raw, "value": str(cell.value)}
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    @staticmethod
    def load_from_json(filename):
        import json
        cells = {}
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            # Handle both direct cells dict and nested structure
            cells_data = data.get('cells', data) if isinstance(data, dict) else data
            for key, cell_data in cells_data.items():
                # Parse cell reference (simplified)
                col = ord(key[0]) - ord('A')
                row = int(key[1:]) - 1
                raw = cell_data.get('raw', '') if isinstance(cell_data, dict) else str(cell_data)
                value = cell_data.get('value', '') if isinstance(cell_data, dict) else str(cell_data)
                cells[(row, col)] = CellData(raw, value)
        except Exception as e:
            print(f"Error loading file: {e}")
        return cells


class SpreadsheetApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Spreadsheet Lite")
        self.root.geometry("800x600")
        
        self.model = SimpleModel()
        self.current_file = None
        self.selected_row = 0
        self.selected_col = 0
        
        self.setup_ui()
        
    def setup_ui(self):
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Copy", command=self.copy_cell)
        edit_menu.add_command(label="Paste", command=self.paste_cell)
        
        format_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Format", menu=format_menu)
        format_menu.add_command(label="Bold", command=self.toggle_bold)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Toolbar
        toolbar = tk.Frame(self.root, relief=tk.RAISED, bd=1)
        toolbar.pack(fill=tk.X)
        
        tk.Button(toolbar, text="New", command=self.new_file).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Open", command=self.open_file).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Button(toolbar, text="Save", command=self.save_file).pack(side=tk.LEFT, padx=2, pady=2)
        tk.Frame(toolbar, width=2, bg='gray').pack(side=tk.LEFT, fill=tk.Y, padx=5)
        tk.Button(toolbar, text="Bold", command=self.toggle_bold).pack(side=tk.LEFT, padx=2, pady=2)
        
        # Formula bar frame
        formula_frame = tk.Frame(self.root)
        formula_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(formula_frame, text="Formula:").pack(side=tk.LEFT)
        self.formula_var = tk.StringVar()
        self.formula_entry = tk.Entry(formula_frame, textvariable=self.formula_var)
        self.formula_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.formula_entry.bind('<Return>', self.on_formula_enter)
        
        # Grid frame
        grid_frame = tk.Frame(self.root)
        grid_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview for spreadsheet with styling
        columns = [format_cell_ref(0, i) for i in range(10)]  # A-J for simplicity
        
        # Configure style for better cell visibility with grid lines
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", 
                       rowheight=25, 
                       fieldbackground="white", 
                       relief="solid", 
                       borderwidth=1,
                       font=('Arial', 9))
        style.configure("Treeview.Heading", 
                       background="lightgray", 
                       relief="solid", 
                       borderwidth=1,
                       font=('Arial', 9, 'bold'))
        
        # Map style to add grid lines
        style.map('Treeview', 
                 background=[('selected', '#0078d4')],
                 foreground=[('selected', 'white')])
        
        self.tree = ttk.Treeview(grid_frame, columns=columns, show='tree headings', height=20, style="Treeview")
        
        # Configure column headers with borders
        self.tree.heading('#0', text='Row')
        self.tree.column('#0', width=50, anchor='center')
        for i, col in enumerate(columns):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=85, anchor='center', minwidth=85)
        
        # Configure grid appearance
        self.tree.configure(selectmode='browse')
        
        # Add tags for alternating row colors
        self.tree.tag_configure('oddrow', background='#f8f8f8')
        self.tree.tag_configure('evenrow', background='white')
        self.tree.tag_configure('selected', background='#cce8ff')
        
        # Add rows with alternating colors
        for row in range(20):
            values = [''] * 10
            tag = 'evenrow' if row % 2 == 0 else 'oddrow'
            self.tree.insert('', 'end', text=str(row + 1), values=values, tags=(tag,))
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(grid_frame, orient=tk.VERTICAL, command=self.tree.yview)
        h_scroll = ttk.Scrollbar(grid_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        # Pack grid components
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection and click events
        self.tree.bind('<<TreeviewSelect>>', self.on_cell_select)
        self.tree.bind('<Button-1>', self.on_cell_click)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def on_cell_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.tree.identify_row(event.y)
            column = self.tree.identify_column(event.x)
            
            if item and column:
                self.selected_row = self.tree.index(item)
                # Column format: '#1', '#2', etc. Convert to 0-based index
                self.selected_col = int(column.replace('#', '')) - 1
                
                # Update formula bar
                cell = self.model.get_cell(self.selected_row, self.selected_col)
                if cell:
                    self.formula_var.set(cell.raw)
                else:
                    self.formula_var.set('')
                    
                # Update status
                cell_ref = format_cell_ref(self.selected_row, self.selected_col)
                self.status_var.set(f"Cell: {cell_ref}")
                
                # Highlight selected cell
                self.highlight_selected_cell()
    
    def on_cell_select(self, event):
        pass  # Keep for compatibility
    
    def on_formula_enter(self, event):
        formula = self.formula_var.get()
        
        # Update model
        if (self.selected_row, self.selected_col) not in self.model.cells:
            self.model.cells[(self.selected_row, self.selected_col)] = CellData()
            
        cell = self.model.cells[(self.selected_row, self.selected_col)]
        cell.raw = formula
        
        # Evaluate formula
        if formula.startswith('='):
            try:
                result = evaluate_simple_formula(formula)
                cell.value = result
            except Exception:
                cell.value = "#ERROR!"
        else:
            try:
                cell.value = float(formula) if '.' in formula else int(formula)
            except ValueError:
                cell.value = formula
                
        # Update display
        self.update_display()
        self.highlight_selected_cell()
        
    def update_display(self):
        """Update the grid display."""
        for row_idx in range(20):
            item = self.tree.get_children()[row_idx]
            values = []
            for col_idx in range(10):
                cell = self.model.get_cell(row_idx, col_idx)
                if cell:
                    values.append(str(cell.value))
                else:
                    values.append('')
            tag = 'evenrow' if row_idx % 2 == 0 else 'oddrow'
            self.tree.item(item, values=values, tags=(tag,))
            
    def highlight_selected_cell(self):
        """Highlight the currently selected cell."""
        # Clear previous selection
        for item in self.tree.get_children():
            tags = list(self.tree.item(item, 'tags'))
            if 'selected' in tags:
                tags.remove('selected')
                row_idx = self.tree.index(item)
                base_tag = 'evenrow' if row_idx % 2 == 0 else 'oddrow'
                self.tree.item(item, tags=(base_tag,))
        
        # Highlight current selection
        if self.selected_row < len(self.tree.get_children()):
            item = self.tree.get_children()[self.selected_row]
            self.tree.selection_set(item)
            self.tree.focus(item)
            
    def new_file(self):
        self.model.cells.clear()
        self.current_file = None
        self.root.title("Spreadsheet Lite - Untitled")
        self.update_display()
        
    def open_file(self):
        filename = filedialog.askopenfilename(
            title="Open Workbook",
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            cells = SimpleStorage.load_from_json(filename)
            self.model.cells = cells
            self.current_file = filename
            self.root.title(f"Spreadsheet Lite - {os.path.basename(filename)}")
            self.update_display()
            
    def save_file(self):
        if self.current_file:
            SimpleStorage.save_to_json(self.model.cells, self.current_file)
            self.status_var.set("File saved")
        else:
            self.save_file_as()
            
    def save_file_as(self):
        filename = filedialog.asksaveasfilename(
            title="Save Workbook",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        if filename:
            SimpleStorage.save_to_json(self.model.cells, filename)
            self.current_file = filename
            self.root.title(f"Spreadsheet Lite - {os.path.basename(filename)}")
            self.status_var.set("File saved")
            
    def copy_cell(self):
        cell = self.model.get_cell(self.selected_row, self.selected_col)
        if cell:
            self.root.clipboard_clear()
            self.root.clipboard_append(cell.raw)
            self.status_var.set("Cell copied")
            
    def paste_cell(self):
        try:
            content = self.root.clipboard_get()
            self.formula_var.set(content)
            self.on_formula_enter(None)
            self.status_var.set("Cell pasted")
        except:
            self.status_var.set("Nothing to paste")
            
    def toggle_bold(self):
        self.status_var.set("Bold formatting not implemented")
        
    def show_about(self):
        messagebox.showinfo("About", "Spreadsheet Lite v1.0\nBuilt with Python and Tkinter")
            
    def run(self):
        self.root.mainloop()


def main():
    app = SpreadsheetApp()
    app.run()


if __name__ == "__main__":
    main()