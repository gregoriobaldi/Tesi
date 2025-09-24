"""Grid-based UI with clear cell borders."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import os

# Simple model classes
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
            expr = formula[1:].replace('^', '**')
            return eval(expr)
        except:
            return "#ERROR!"
    return formula

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
            cells_data = data.get('cells', data) if isinstance(data, dict) else data
            for key, cell_data in cells_data.items():
                col = ord(key[0]) - ord('A')
                row = int(key[1:]) - 1
                raw = cell_data.get('raw', '') if isinstance(cell_data, dict) else str(cell_data)
                value = cell_data.get('value', '') if isinstance(cell_data, dict) else str(cell_data)
                cells[(row, col)] = CellData(raw, value)
        except Exception as e:
            print(f"Error loading: {e}")
        return cells

class SpreadsheetGrid:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Spreadsheet Lite")
        self.root.geometry("900x700")
        
        self.model = SimpleModel()
        self.current_file = None
        self.selected_row = 0
        self.selected_col = 0
        self.cells = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        # Menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_file)
        file_menu.add_command(label="Open", command=self.open_file)
        file_menu.add_command(label="Save", command=self.save_file)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Formula bar
        formula_frame = tk.Frame(self.root)
        formula_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(formula_frame, text="Formula:").pack(side=tk.LEFT)
        self.formula_var = tk.StringVar()
        self.formula_entry = tk.Entry(formula_frame, textvariable=self.formula_var)
        self.formula_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        self.formula_entry.bind('<Return>', self.on_formula_enter)
        
        # Grid container with canvas for scrolling
        canvas = tk.Canvas(self.root)
        scrollbar_v = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollbar_h = tk.Scrollbar(self.root, orient="horizontal", command=canvas.xview)
        
        grid_frame = tk.Frame(canvas)
        
        # Configure scrolling
        canvas.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        canvas.create_window((0, 0), window=grid_frame, anchor="nw")
        
        # Pack scrollbars and canvas
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar_v.pack(side="right", fill="y")
        scrollbar_h.pack(side="bottom", fill="x")
        
        # Empty corner cell
        corner = tk.Label(grid_frame, text="", width=5, height=2, bg='lightgray', relief='solid', bd=1)
        corner.grid(row=0, column=0, sticky='nsew')
        
        # Column headers A-J
        for col in range(10):
            header = tk.Label(grid_frame, text=chr(ord('A') + col), width=12, height=2, bg='lightgray', relief='solid', bd=1)
            header.grid(row=0, column=col+1, sticky='nsew')
        
        # Grid with cells
        for row in range(20):
            # Row header
            row_header = tk.Label(grid_frame, text=str(row+1), width=5, height=2, bg='lightgray', relief='solid', bd=1)
            row_header.grid(row=row+1, column=0, sticky='nsew')
            
            # Cells
            for col in range(10):
                cell = tk.Entry(grid_frame, width=12, justify='center', relief='solid', bd=1, font=('Arial', 10))
                cell.grid(row=row+1, column=col+1, sticky='nsew', padx=1, pady=1)
                cell.bind('<FocusIn>', lambda e, r=row, c=col: self.on_cell_select(r, c))
                cell.bind('<KeyRelease>', lambda e, r=row, c=col: self.on_cell_edit(r, c, e.widget.get()))
                self.cells[(row, col)] = cell
        
        # Update scroll region
        grid_frame.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def on_cell_select(self, row, col):
        self.selected_row = row
        self.selected_col = col
        
        cell = self.model.get_cell(row, col)
        if cell:
            self.formula_var.set(cell.raw)
        else:
            self.formula_var.set('')
            
        cell_ref = format_cell_ref(row, col)
        self.status_var.set(f"Cell: {cell_ref}")
        
    def on_cell_edit(self, row, col, value):
        if (row, col) not in self.model.cells:
            self.model.cells[(row, col)] = CellData()
            
        cell = self.model.cells[(row, col)]
        cell.raw = value
        
        if value.startswith('='):
            try:
                result = evaluate_simple_formula(value)
                cell.value = result
                self.cells[(row, col)].delete(0, tk.END)
                self.cells[(row, col)].insert(0, str(result))
            except:
                cell.value = "#ERROR!"
                self.cells[(row, col)].delete(0, tk.END)
                self.cells[(row, col)].insert(0, "#ERROR!")
        else:
            try:
                cell.value = float(value) if '.' in value else int(value)
            except ValueError:
                cell.value = value
                
    def on_formula_enter(self, event):
        formula = self.formula_var.get()
        row, col = self.selected_row, self.selected_col
        
        self.cells[(row, col)].delete(0, tk.END)
        self.cells[(row, col)].insert(0, formula)
        self.on_cell_edit(row, col, formula)
        
    def update_display(self):
        for (row, col), cell_data in self.model.cells.items():
            if (row, col) in self.cells:
                self.cells[(row, col)].delete(0, tk.END)
                self.cells[(row, col)].insert(0, str(cell_data.value))
                
    def new_file(self):
        self.model.cells.clear()
        self.current_file = None
        self.root.title("Spreadsheet Lite - Untitled")
        for cell_widget in self.cells.values():
            cell_widget.delete(0, tk.END)
            
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
            
    def run(self):
        self.root.mainloop()

def main():
    app = SpreadsheetGrid()
    app.run()

if __name__ == "__main__":
    main()