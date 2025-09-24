# Spreadsheet Lite

A desktop spreadsheet application built with Python and PyQt6, featuring a complete formula engine, dependency tracking, and file persistence.

## Features

### Core Functionality
- **Grid Interface**: QTableView with custom model supporting 100 rows × 26 columns (A-Z)
- **Formula Bar**: Edit cell formulas and see live updates
- **Cell References**: Support for A1-style cell references and ranges (A1:B5)
- **Sparse Storage**: Efficient memory usage with dictionary-based cell storage

### Formula Engine
- **Arithmetic Operations**: `+`, `-`, `*`, `/`, `^` (power)
- **Comparison Operators**: `=`, `<>`, `<`, `<=`, `>`, `>=`
- **Built-in Functions**:
  - `SUM(range)` - Sum of values
  - `AVERAGE(range)` - Average of values
  - `MIN(range)` / `MAX(range)` - Minimum/Maximum values
  - `COUNT(range)` - Count of numeric values
  - `IF(condition, true_val, false_val)` - Conditional logic
  - `ABS(number)` - Absolute value
  - `ROUND(number, digits)` - Round to specified digits
  - `CONCAT(text1, text2, ...)` - Concatenate text

### Error Handling
- **#DIV/0!** - Division by zero
- **#REF!** - Invalid cell reference
- **#VALUE!** - Invalid value or operation
- **#NAME?** - Unknown function name
- **#CYCLE!** - Circular reference detected

### Advanced Features
- **Dependency Tracking**: Automatic recalculation of dependent cells
- **Cycle Detection**: Prevents infinite loops in formulas
- **Undo/Redo**: Full undo stack with QUndoStack
- **Cell Formatting**: Bold text formatting
- **Find & Replace**: Search in values or formulas (dialog ready)
- **Go To Cell**: Quick navigation to specific cells

### File Operations
- **Save/Load**: JSON format for complete workbook persistence
- **Import/Export**: CSV support for data exchange
- **Auto-save**: Preserves formulas, values, and formatting

## Installation

### Requirements
```bash
pip install -r requirements.txt
```

### Dependencies
- PyQt6 >= 6.6.1
- pytest >= 7.4.3 (for testing)
- pyinstaller >= 6.2.0 (for building executable)

## Usage

### Running the Application
```bash
python ui.py
```

### Building Executable
```bash
pyinstaller spreadsheet.spec
```

### Running Tests
```bash
pytest test_*.py -v
```

## Architecture

### Module Structure
- **`ui.py`** - Main window, dialogs, and user interface
- **`model.py`** - Data model and address utilities
- **`formula.py`** - Formula lexer, parser, and evaluator
- **`storage.py`** - JSON and CSV file operations
- **`undo.py`** - Undo/redo command system

### Key Classes
- **`SpreadsheetModel`** - QAbstractTableModel for grid data
- **`FormulaLexer`** - Tokenizes formula strings
- **`FormulaParser`** - Builds AST from tokens using Pratt parsing
- **`FormulaEvaluator`** - Evaluates AST nodes
- **`DependencyTracker`** - Manages cell dependencies and recalculation

## Examples

### Basic Formulas
```
=2+3*4          → 14
=A1+B1          → Sum of cells A1 and B1
=SUM(A1:A10)    → Sum of range A1 to A10
=IF(A1>10,"High","Low") → Conditional result
```

### Cell Dependencies
```
A1: 10
B1: =A1*2       → 20
C1: =B1+5       → 25
```
When A1 changes to 5, B1 automatically recalculates to 10, and C1 to 15.

### Error Handling
```
=1/0            → #DIV/0!
=UNKNOWN()      → #NAME?
=A1 (if A1 contains =B1 and B1 contains =A1) → #CYCLE!
```

## Screenshots

### Main Interface
The application features a clean interface with:
- Menu bar with File, Edit, Format, and Help menus
- Toolbar with common actions (New, Open, Save, Bold)
- Formula bar showing the active cell's formula
- Grid with column headers (A, B, C...) and row numbers (1, 2, 3...)
- Status bar showing current cell position

### Dialogs
- **Find & Replace**: Search and replace text in cells
- **Go To Cell**: Navigate directly to a specific cell
- **About**: Application information

## Testing

The application includes comprehensive tests:

### Formula Engine Tests (`test_formula.py`)
- Lexer tokenization
- Parser AST generation
- Evaluator computation
- Error handling
- Function evaluation

### Model Tests (`test_model.py`)
- Address conversion utilities
- Cell data operations
- Range handling
- Model interface

### Dependency Tests (`test_dependencies.py`)
- Dependency tracking
- Cycle detection
- Recalculation logic
- Error propagation

## License

This project is provided as-is for educational and demonstration purposes.