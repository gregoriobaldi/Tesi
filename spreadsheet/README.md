# Spreadsheet Lite

A lightweight desktop spreadsheet application built with Python and tkinter. Features a complete formula engine, dependency tracking, undo/redo system, and file I/O capabilities.

## Features

### Core Functionality
- **Spreadsheet Grid**: Interactive grid with row/column headers and cell selection
- **Formula Engine**: Complete formula parser and evaluator with built-in functions
- **Dependency Tracking**: Automatic recalculation with cycle detection
- **Undo/Redo**: Multi-level undo/redo system for all operations
- **File I/O**: Save/load workbooks in JSON format, import/export CSV

### User Interface
- **Menu System**: Complete menu structure with keyboard shortcuts
- **Toolbar**: Quick access buttons for common operations
- **Formula Bar**: Display and edit cell formulas
- **Status Bar**: Show current cell address and application status
- **Dialogs**: Find/Replace, Go to Cell, About dialog

### Formula Support
- **Arithmetic**: `+`, `-`, `*`, `/`, `^` (power)
- **Comparisons**: `=`, `<>`, `<`, `<=`, `>`, `>=`
- **Cell References**: `A1`, `B2`, etc.
- **Ranges**: `A1:B5` for aggregate functions
- **Built-in Functions**:
  - `SUM(range)` - Sum of values
  - `AVERAGE(range)` - Average of values
  - `MIN(range)` - Minimum value
  - `MAX(range)` - Maximum value
  - `COUNT(range)` - Count of non-empty cells
  - `IF(condition, true_value, false_value)` - Conditional logic
  - `ABS(number)` - Absolute value
  - `ROUND(number, digits)` - Round to specified digits
  - `CONCAT(text1, text2, ...)` - Concatenate text

### Error Handling
- **Formula Errors**: `#DIV/0!`, `#REF!`, `#VALUE!`, `#NAME?`, `#CYCLE!`, `#ERROR!`
- **Cycle Detection**: Prevents infinite calculation loops
- **Error Display**: Visual indicators for cells with errors

### Editing Features
- **Cell Selection**: Single cell and range selection
- **In-place Editing**: Double-click or F2 to edit cells
- **Clipboard Operations**: Copy, cut, paste with Ctrl+C/X/V
- **Insert/Delete**: Add or remove rows and columns
- **Find/Replace**: Search and replace across the spreadsheet

### Formatting
- **Bold Text**: Toggle bold formatting for cells
- **Number Precision**: Set decimal places (0-6) for numeric values
- **Format Persistence**: Formatting saved with workbook

## Architecture

The application is structured into several key modules:

### Core Modules

- **`model.py`**: Data model with sparse cell storage, addressing utilities, and sheet management
- **`formula.py`**: Formula tokenizer, parser (AST), and evaluator with built-in functions
- **`engine.py`**: Calculation engine with dependency graph and topological sorting
- **`storage.py`**: File I/O operations for JSON and CSV formats
- **`undo.py`**: Command pattern implementation for undo/redo operations
- **`ui.py`**: Main tkinter interface with grid widget and dialogs

### Key Design Patterns

- **Observer Pattern**: Model notifies UI of changes
- **Command Pattern**: All operations are undoable commands
- **MVC Architecture**: Clear separation between model, view, and control logic
- **Sparse Storage**: Only stores non-empty cells for memory efficiency

### Dependency Management

The calculation engine maintains a directed graph of cell dependencies:
- **Dependency Tracking**: Automatically tracks which cells depend on others
- **Topological Sort**: Ensures correct calculation order
- **Cycle Detection**: Prevents infinite loops with `#CYCLE!` error
- **Incremental Updates**: Only recalculates affected cells

## Installation and Usage

### Requirements
- Python 3.6 or higher
- tkinter (included with Python)
- All other dependencies are part of Python standard library

### Running the Application

```bash
python main.py
```

### Keyboard Shortcuts

- **File Operations**:
  - `Ctrl+N` - New workbook
  - `Ctrl+O` - Open workbook
  - `Ctrl+S` - Save workbook

- **Edit Operations**:
  - `Ctrl+Z` - Undo
  - `Ctrl+Y` - Redo
  - `Ctrl+C` - Copy
  - `Ctrl+X` - Cut
  - `Ctrl+V` - Paste

- **Navigation**:
  - `Arrow Keys` - Move cell selection
  - `Enter` - Move down and commit edit
  - `Tab` - Move right
  - `F2` - Edit current cell
  - `Ctrl+G` - Go to cell

- **Search**:
  - `Ctrl+F` - Find and replace

### File Formats

#### JSON Workbook Format
Workbooks are saved in JSON format with complete cell data, formulas, and formatting:

```json
{
  "sheet_name": "Sheet1",
  "cells": {
    "0,0": {
      "raw": "=SUM(A1:A10)",
      "value": 55,
      "format": {"bold": true, "precision": 2},
      "error": null
    }
  },
  "max_row": 10,
  "max_col": 5
}
```

#### CSV Import/Export
- Import CSV files into the spreadsheet starting at any cell
- Export ranges or entire sheet to CSV format
- Automatic type detection for imported data

## Sample Files

The `samples/` directory contains example files:

- **`sample_data.csv`**: Sample CSV data for import testing
- **`sample_workbook.json`**: Example workbook with formulas and formatting

## Testing

The application includes comprehensive error handling and validation:

- **Formula Validation**: Syntax checking before evaluation
- **Circular Reference Detection**: Prevents infinite calculation loops
- **Type Coercion**: Automatic conversion between numbers and text
- **Bounds Checking**: Validates cell references and ranges

## Performance

The application is optimized for handling spreadsheets with thousands of cells:

- **Sparse Storage**: Only stores non-empty cells
- **AST Caching**: Parsed formulas are cached for performance
- **Incremental Calculation**: Only recalculates affected cells
- **Efficient Dependencies**: Graph-based dependency tracking

## Limitations

- Single sheet per workbook
- Limited to 26 columns (A-Z) in current UI implementation
- Basic formatting options (bold, precision)
- Simplified CSV parsing (doesn't handle all edge cases)

## Future Enhancements

Potential improvements for future versions:

- Multiple sheets per workbook
- Extended column support (AA, AB, etc.)
- More formatting options (colors, fonts, borders)
- Chart and graph support
- Advanced functions (date/time, text manipulation)
- Plugin system for custom functions
- Network collaboration features

## License

This project is provided as-is for educational and demonstration purposes.

## Screenshots

### Main Interface
The main window shows the spreadsheet grid with menu bar, toolbar, formula bar, and status bar.

### Formula Editing
The formula bar displays the current cell's formula, with real-time validation and error checking.

### Find and Replace
The Find & Replace dialog supports text search with options for regular expressions and case sensitivity.

### Error Handling
Cells with formula errors display visual indicators and detailed error messages.