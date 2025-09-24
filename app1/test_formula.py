"""Tests for formula parsing and evaluation."""

import pytest
from formula import FormulaLexer, FormulaParser, FormulaEvaluator, parse_formula, evaluate_formula
from formula import NumberNode, StringNode, CellRefNode, BinaryOpNode, FunctionNode
from model import SpreadsheetModel, CellData


class TestFormulaLexer:
    """Test the formula lexer."""
    
    def test_tokenize_numbers(self):
        lexer = FormulaLexer("123 45.67")
        tokens = lexer.tokenize()
        assert len(tokens) == 3  # 2 numbers + EOF
        assert tokens[0].value == "123"
        assert tokens[1].value == "45.67"
        
    def test_tokenize_operators(self):
        lexer = FormulaLexer("+ - * / ^")
        tokens = lexer.tokenize()
        operators = [t.value for t in tokens[:-1]]  # Exclude EOF
        assert operators == ["+", "-", "*", "/", "^"]
        
    def test_tokenize_cell_refs(self):
        lexer = FormulaLexer("A1 B25 Z99")
        tokens = lexer.tokenize()
        refs = [t.value for t in tokens[:-1]]
        assert refs == ["A1", "B25", "Z99"]
        
    def test_tokenize_ranges(self):
        lexer = FormulaLexer("A1:B5")
        tokens = lexer.tokenize()
        assert tokens[0].value == "A1:B5"
        
    def test_tokenize_functions(self):
        lexer = FormulaLexer("SUM(A1:B5)")
        tokens = lexer.tokenize()
        assert tokens[0].value == "SUM"
        assert tokens[1].value == "("


class TestFormulaParser:
    """Test the formula parser."""
    
    def test_parse_number(self):
        lexer = FormulaLexer("42")
        parser = FormulaParser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, NumberNode)
        assert ast.value == 42.0
        
    def test_parse_binary_op(self):
        lexer = FormulaLexer("2 + 3")
        parser = FormulaParser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "+"
        assert ast.left.value == 2.0
        assert ast.right.value == 3.0
        
    def test_parse_precedence(self):
        lexer = FormulaLexer("2 + 3 * 4")
        parser = FormulaParser(lexer.tokenize())
        ast = parser.parse()
        # Should be: 2 + (3 * 4)
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "+"
        assert ast.left.value == 2.0
        assert isinstance(ast.right, BinaryOpNode)
        assert ast.right.operator == "*"
        
    def test_parse_parentheses(self):
        lexer = FormulaLexer("(2 + 3) * 4")
        parser = FormulaParser(lexer.tokenize())
        ast = parser.parse()
        # Should be: (2 + 3) * 4
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "*"
        assert isinstance(ast.left, BinaryOpNode)
        assert ast.left.operator == "+"
        
    def test_parse_function(self):
        lexer = FormulaLexer("SUM(1, 2, 3)")
        parser = FormulaParser(lexer.tokenize())
        ast = parser.parse()
        assert isinstance(ast, FunctionNode)
        assert ast.name == "SUM"
        assert len(ast.args) == 3


class TestFormulaEvaluator:
    """Test the formula evaluator."""
    
    def setup_method(self):
        self.model = SpreadsheetModel()
        self.evaluator = FormulaEvaluator(self.model)
        
    def test_evaluate_number(self):
        node = NumberNode(42.5)
        result = self.evaluator.evaluate(node)
        assert result == 42.5
        
    def test_evaluate_arithmetic(self):
        # 2 + 3
        node = BinaryOpNode(NumberNode(2), "+", NumberNode(3))
        result = self.evaluator.evaluate(node)
        assert result == 5
        
        # 10 / 2
        node = BinaryOpNode(NumberNode(10), "/", NumberNode(2))
        result = self.evaluator.evaluate(node)
        assert result == 5
        
    def test_evaluate_division_by_zero(self):
        node = BinaryOpNode(NumberNode(10), "/", NumberNode(0))
        result = self.evaluator.evaluate(node)
        assert result == "#DIV/0!"
        
    def test_evaluate_cell_ref(self):
        # Set up a cell with value
        self.model.cells[(0, 0)] = CellData("42", 42)
        
        node = CellRefNode(0, 0)  # A1
        result = self.evaluator.evaluate(node)
        assert result == 42
        
    def test_evaluate_sum_function(self):
        node = FunctionNode("SUM", [NumberNode(1), NumberNode(2), NumberNode(3)])
        result = self.evaluator.evaluate(node)
        assert result == 6
        
    def test_evaluate_if_function(self):
        # IF(1, "yes", "no") -> "yes"
        node = FunctionNode("IF", [NumberNode(1), StringNode("yes"), StringNode("no")])
        result = self.evaluator.evaluate(node)
        assert result == "yes"
        
        # IF(0, "yes", "no") -> "no"
        node = FunctionNode("IF", [NumberNode(0), StringNode("yes"), StringNode("no")])
        result = self.evaluator.evaluate(node)
        assert result == "no"


class TestIntegration:
    """Integration tests for complete formula processing."""
    
    def setup_method(self):
        self.model = SpreadsheetModel()
        
    def test_simple_formula(self):
        result = evaluate_formula("=2+3", self.model)
        assert result == 5
        
    def test_cell_reference_formula(self):
        # Set up cells
        self.model.cells[(0, 0)] = CellData("10", 10)  # A1
        self.model.cells[(0, 1)] = CellData("20", 20)  # B1
        
        result = evaluate_formula("=A1+B1", self.model)
        assert result == 30
        
    def test_function_formula(self):
        result = evaluate_formula("=SUM(1,2,3,4,5)", self.model)
        assert result == 15
        
    def test_complex_formula(self):
        # Set up cells
        self.model.cells[(0, 0)] = CellData("10", 10)  # A1
        self.model.cells[(0, 1)] = CellData("5", 5)    # B1
        
        result = evaluate_formula("=IF(A1>B1, A1*2, B1*2)", self.model)
        assert result == 20  # A1 > B1, so A1*2 = 20
        
    def test_error_propagation(self):
        result = evaluate_formula("=1/0", self.model)
        assert result == "#DIV/0!"
        
    def test_invalid_formula(self):
        result = evaluate_formula("=INVALID_FUNC()", self.model)
        assert result == "#NAME?"


if __name__ == "__main__":
    pytest.main([__file__])