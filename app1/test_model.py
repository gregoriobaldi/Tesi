"""Tests for the data model and address utilities."""

import pytest
from model import col_to_letter, letter_to_col, parse_cell_ref, format_cell_ref, parse_range, SpreadsheetModel, CellData


class TestAddressUtils:
    """Test address conversion utilities."""
    
    def test_col_to_letter(self):
        assert col_to_letter(0) == "A"
        assert col_to_letter(25) == "Z"
        assert col_to_letter(26) == "AA"
        assert col_to_letter(27) == "AB"
        assert col_to_letter(701) == "ZZ"
        
    def test_letter_to_col(self):
        assert letter_to_col("A") == 0
        assert letter_to_col("Z") == 25
        assert letter_to_col("AA") == 26
        assert letter_to_col("AB") == 27
        assert letter_to_col("ZZ") == 701
        
    def test_parse_cell_ref(self):
        assert parse_cell_ref("A1") == (0, 0)
        assert parse_cell_ref("B5") == (4, 1)
        assert parse_cell_ref("Z99") == (98, 25)
        assert parse_cell_ref("AA1") == (0, 26)
        
    def test_format_cell_ref(self):
        assert format_cell_ref(0, 0) == "A1"
        assert format_cell_ref(4, 1) == "B5"
        assert format_cell_ref(98, 25) == "Z99"
        assert format_cell_ref(0, 26) == "AA1"
        
    def test_parse_range(self):
        start, end = parse_range("A1:B5")
        assert start == (0, 0)
        assert end == (4, 1)
        
        start, end = parse_range("C3:E7")
        assert start == (2, 2)
        assert end == (6, 4)
        
    def test_invalid_cell_ref(self):
        with pytest.raises(ValueError):
            parse_cell_ref("123")
        with pytest.raises(ValueError):
            parse_cell_ref("ABC")
        with pytest.raises(ValueError):
            parse_cell_ref("")


class TestSpreadsheetModel:
    """Test the spreadsheet model."""
    
    def setup_method(self):
        self.model = SpreadsheetModel()
        
    def test_initial_state(self):
        assert self.model.rowCount() == 100
        assert self.model.columnCount() == 26
        assert len(self.model.cells) == 0
        
    def test_header_data(self):
        # Column headers
        assert self.model.headerData(0, 1) == "A"
        assert self.model.headerData(1, 1) == "B"
        assert self.model.headerData(25, 1) == "Z"
        
        # Row headers
        assert self.model.headerData(0, 2) == "1"
        assert self.model.headerData(4, 2) == "5"
        
    def test_set_get_data(self):
        index = self.model.index(0, 0)
        
        # Set data
        result = self.model.setData(index, "Hello")
        assert result is True
        
        # Get data
        data = self.model.data(index)
        assert data == "Hello"
        
    def test_cell_operations(self):
        # Set cell value
        self.model.set_cell_value(0, 0, 42)
        cell = self.model.get_cell(0, 0)
        assert cell.value == 42
        
        # Clear cell
        self.model.clear_cell(0, 0)
        cell = self.model.get_cell(0, 0)
        assert cell is None
        
    def test_range_values(self):
        # Set up some cells
        self.model.cells[(0, 0)] = CellData("1", 1)
        self.model.cells[(0, 1)] = CellData("2", 2)
        self.model.cells[(1, 0)] = CellData("3", 3)
        self.model.cells[(1, 1)] = CellData("4", 4)
        
        values = self.model.get_range_values((0, 0), (1, 1))
        assert values == [1, 2, 3, 4]
        
    def test_cell_data(self):
        cell = CellData("=A1+B1", 42, bold=True, precision=3)
        assert cell.raw == "=A1+B1"
        assert cell.value == 42
        assert cell.bold is True
        assert cell.precision == 3
        assert cell.error is None


if __name__ == "__main__":
    pytest.main([__file__])