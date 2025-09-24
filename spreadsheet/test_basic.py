#!/usr/bin/env python3
"""
Basic tests for spreadsheet functionality.
Run this to verify core components work correctly.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model import SpreadsheetModel, parse_address, address_to_string, col_to_letter, letter_to_col
from formula import parse_formula, evaluate_formula
from engine import CalculationEngine
from storage import StorageManager


def test_addressing():
    """Test address conversion functions"""
    print("Testing address conversion...")
    
    # Test column conversion
    assert col_to_letter(0) == "A"
    assert col_to_letter(25) == "Z"
    assert letter_to_col("A") == 0
    assert letter_to_col("Z") == 25
    
    # Test address parsing
    assert parse_address("A1") == (0, 0)
    assert parse_address("B2") == (1, 1)
    assert address_to_string(0, 0) == "A1"
    assert address_to_string(1, 1) == "B2"
    
    print("[OK] Address conversion tests passed")


def test_model():
    """Test spreadsheet model"""
    print("Testing spreadsheet model...")
    
    model = SpreadsheetModel()
    
    # Test cell operations
    model.set_cell_raw(0, 0, "Hello")
    model.set_cell_raw(1, 1, "42")
    model.set_cell_raw(2, 2, "=A1")
    
    assert model.get_cell_display_value(0, 0) == "Hello"
    assert model.get_cell_display_value(1, 1) == "42"
    
    # Test serialization
    data = model.to_dict()
    assert "cells" in data
    assert "0,0" in data["cells"]
    
    print("[OK] Model tests passed")


def test_formulas():
    """Test formula parsing and evaluation"""
    print("Testing formula engine...")
    
    def get_cell_value(row, col):
        if row == 0 and col == 0:
            return 10
        elif row == 0 and col == 1:
            return 20
        return ""
    
    # Test basic arithmetic
    result = evaluate_formula("=5+3", get_cell_value)
    assert result == 8
    
    result = evaluate_formula("=10*2", get_cell_value)
    assert result == 20
    
    result = evaluate_formula("=A1+B1", get_cell_value)
    assert result == 30
    
    # Test functions
    result = evaluate_formula("=SUM(A1:B1)", get_cell_value)
    assert result == 30
    
    result = evaluate_formula("=IF(A1>5,\"Yes\",\"No\")", get_cell_value)
    assert result == "Yes"
    
    print("[OK] Formula tests passed")


def test_calculation_engine():
    """Test calculation engine with dependencies"""
    print("Testing calculation engine...")
    
    model = SpreadsheetModel()
    engine = CalculationEngine(model)
    
    # Set up some formulas
    model.set_cell_raw(0, 0, "10")
    model.set_cell_raw(0, 1, "20")
    model.set_cell_raw(0, 2, "=A1+B1")
    
    # Update through engine
    engine.set_cell_formula(0, 2, "=A1+B1")
    
    # Check result
    cell = model.sheet.get_cell(0, 2)
    assert cell.value == 30
    
    # Test dependency tracking
    deps = engine.get_cell_dependencies(0, 2)
    assert "A1" in deps
    assert "B1" in deps
    
    print("[OK] Calculation engine tests passed")


def test_storage():
    """Test file I/O operations"""
    print("Testing storage operations...")
    
    model = SpreadsheetModel()
    storage = StorageManager(model)
    
    # Set up some data
    model.set_cell_raw(0, 0, "Test")
    model.set_cell_raw(1, 1, "42")
    
    # Test JSON serialization
    data = model.to_dict()
    assert "cells" in data
    
    # Test CSV export (to string)
    csv_data = storage.get_range_as_csv_string(0, 0, 1, 1)
    assert "Test" in csv_data
    
    print("[OK] Storage tests passed")


def run_all_tests():
    """Run all basic tests"""
    print("Running basic functionality tests...\n")
    
    try:
        test_addressing()
        test_model()
        test_formulas()
        test_calculation_engine()
        test_storage()
        
        print("\n[SUCCESS] All tests passed! The spreadsheet core functionality is working correctly.")
        print("\nYou can now run the application with: python main.py")
        
    except Exception as e:
        print(f"\n[FAILED] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    run_all_tests()