"""
Formula parsing and evaluation engine.
Implements tokenizer, parser, and built-in functions.
"""
from typing import List, Dict, Any, Union, Optional, Callable
import re
import math
from enum import Enum
from model import parse_address, parse_range, address_to_string


class TokenType(Enum):
    NUMBER = "NUMBER"
    STRING = "STRING"
    CELL_REF = "CELL_REF"
    RANGE = "RANGE"
    FUNCTION = "FUNCTION"
    OPERATOR = "OPERATOR"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    COMMA = "COMMA"
    EOF = "EOF"


class Token:
    def __init__(self, type_: TokenType, value: str, position: int = 0):
        self.type = type_
        self.value = value
        self.position = position
    
    def __repr__(self):
        return f"Token({self.type}, {self.value})"


class ASTNode:
    pass


class NumberNode(ASTNode):
    def __init__(self, value: float):
        self.value = value


class StringNode(ASTNode):
    def __init__(self, value: str):
        self.value = value


class CellRefNode(ASTNode):
    def __init__(self, row: int, col: int):
        self.row = row
        self.col = col


class RangeNode(ASTNode):
    def __init__(self, cells: List[tuple]):
        self.cells = cells


class BinaryOpNode(ASTNode):
    def __init__(self, left: ASTNode, operator: str, right: ASTNode):
        self.left = left
        self.operator = operator
        self.right = right


class UnaryOpNode(ASTNode):
    def __init__(self, operator: str, operand: ASTNode):
        self.operator = operator
        self.operand = operand


class FunctionNode(ASTNode):
    def __init__(self, name: str, args: List[ASTNode]):
        self.name = name
        self.args = args


class FormulaTokenizer:
    """Tokenizes formula strings"""
    
    def __init__(self, formula: str):
        self.formula = formula.strip()
        if self.formula.startswith('='):
            self.formula = self.formula[1:]
        self.position = 0
        self.tokens = []
    
    def tokenize(self) -> List[Token]:
        """Tokenize the formula string"""
        self.tokens = []
        self.position = 0
        
        while self.position < len(self.formula):
            self._skip_whitespace()
            if self.position >= len(self.formula):
                break
            
            char = self.formula[self.position]
            
            if char.isdigit() or char == '.':
                self._read_number()
            elif char == '"':
                self._read_string()
            elif char.isalpha():
                self._read_identifier()
            elif char in '+-*/^=<>':
                self._read_operator()
            elif char == '(':
                self.tokens.append(Token(TokenType.LPAREN, char, self.position))
                self.position += 1
            elif char == ')':
                self.tokens.append(Token(TokenType.RPAREN, char, self.position))
                self.position += 1
            elif char == ',':
                self.tokens.append(Token(TokenType.COMMA, char, self.position))
                self.position += 1
            else:
                self.position += 1  # Skip unknown characters
        
        self.tokens.append(Token(TokenType.EOF, "", self.position))
        return self.tokens
    
    def _skip_whitespace(self):
        while self.position < len(self.formula) and self.formula[self.position].isspace():
            self.position += 1
    
    def _read_number(self):
        start = self.position
        while (self.position < len(self.formula) and 
               (self.formula[self.position].isdigit() or self.formula[self.position] == '.')):
            self.position += 1
        
        value = self.formula[start:self.position]
        self.tokens.append(Token(TokenType.NUMBER, value, start))
    
    def _read_string(self):
        start = self.position
        self.position += 1  # Skip opening quote
        
        while self.position < len(self.formula) and self.formula[self.position] != '"':
            self.position += 1
        
        if self.position < len(self.formula):
            self.position += 1  # Skip closing quote
        
        value = self.formula[start+1:self.position-1]
        self.tokens.append(Token(TokenType.STRING, value, start))
    
    def _read_identifier(self):
        start = self.position
        
        # Read letters and numbers
        while (self.position < len(self.formula) and 
               (self.formula[self.position].isalnum())):
            self.position += 1
        
        value = self.formula[start:self.position]
        
        # Check if it's a cell reference or range
        if re.match(r'^[A-Z]+\d+$', value):
            # Check for range (A1:B2)
            if (self.position < len(self.formula) - 1 and 
                self.formula[self.position] == ':'):
                # Read the range
                self.position += 1  # Skip ':'
                range_start = self.position
                while (self.position < len(self.formula) and 
                       (self.formula[self.position].isalnum())):
                    self.position += 1
                
                range_end = self.formula[range_start:self.position]
                if re.match(r'^[A-Z]+\d+$', range_end):
                    range_value = f"{value}:{range_end}"
                    self.tokens.append(Token(TokenType.RANGE, range_value, start))
                else:
                    # Invalid range, treat as cell ref
                    self.position = range_start - 1
                    self.tokens.append(Token(TokenType.CELL_REF, value, start))
            else:
                self.tokens.append(Token(TokenType.CELL_REF, value, start))
        else:
            # Function name
            self.tokens.append(Token(TokenType.FUNCTION, value, start))
    
    def _read_operator(self):
        start = self.position
        char = self.formula[self.position]
        
        # Handle multi-character operators
        if char in '<>=':
            if (self.position + 1 < len(self.formula) and 
                self.formula[self.position + 1] == '='):
                self.position += 2
                value = self.formula[start:self.position]
            else:
                self.position += 1
                value = char
        else:
            self.position += 1
            value = char
        
        self.tokens.append(Token(TokenType.OPERATOR, value, start))


class FormulaParser:
    """Parses tokenized formulas into AST"""
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.position = 0
        self.current_token = self.tokens[0] if tokens else Token(TokenType.EOF, "")
    
    def parse(self) -> ASTNode:
        """Parse tokens into AST"""
        return self._parse_expression()
    
    def _advance(self):
        if self.position < len(self.tokens) - 1:
            self.position += 1
            self.current_token = self.tokens[self.position]
    
    def _parse_expression(self) -> ASTNode:
        return self._parse_comparison()
    
    def _parse_comparison(self) -> ASTNode:
        node = self._parse_addition()
        
        while self.current_token.type == TokenType.OPERATOR and self.current_token.value in ['=', '<>', '<', '<=', '>', '>=']:
            operator = self.current_token.value
            self._advance()
            right = self._parse_addition()
            node = BinaryOpNode(node, operator, right)
        
        return node
    
    def _parse_addition(self) -> ASTNode:
        node = self._parse_multiplication()
        
        while self.current_token.type == TokenType.OPERATOR and self.current_token.value in ['+', '-']:
            operator = self.current_token.value
            self._advance()
            right = self._parse_multiplication()
            node = BinaryOpNode(node, operator, right)
        
        return node
    
    def _parse_multiplication(self) -> ASTNode:
        node = self._parse_power()
        
        while self.current_token.type == TokenType.OPERATOR and self.current_token.value in ['*', '/']:
            operator = self.current_token.value
            self._advance()
            right = self._parse_power()
            node = BinaryOpNode(node, operator, right)
        
        return node
    
    def _parse_power(self) -> ASTNode:
        node = self._parse_unary()
        
        if self.current_token.type == TokenType.OPERATOR and self.current_token.value == '^':
            operator = self.current_token.value
            self._advance()
            right = self._parse_power()  # Right associative
            node = BinaryOpNode(node, operator, right)
        
        return node
    
    def _parse_unary(self) -> ASTNode:
        if self.current_token.type == TokenType.OPERATOR and self.current_token.value in ['+', '-']:
            operator = self.current_token.value
            self._advance()
            operand = self._parse_unary()
            return UnaryOpNode(operator, operand)
        
        return self._parse_primary()
    
    def _parse_primary(self) -> ASTNode:
        token = self.current_token
        
        if token.type == TokenType.NUMBER:
            self._advance()
            return NumberNode(float(token.value))
        
        elif token.type == TokenType.STRING:
            self._advance()
            return StringNode(token.value)
        
        elif token.type == TokenType.CELL_REF:
            self._advance()
            row, col = parse_address(token.value)
            return CellRefNode(row, col)
        
        elif token.type == TokenType.RANGE:
            self._advance()
            cells = parse_range(token.value)
            return RangeNode(cells)
        
        elif token.type == TokenType.FUNCTION:
            return self._parse_function()
        
        elif token.type == TokenType.LPAREN:
            self._advance()
            node = self._parse_expression()
            if self.current_token.type == TokenType.RPAREN:
                self._advance()
            return node
        
        else:
            raise ValueError(f"Unexpected token: {token}")
    
    def _parse_function(self) -> FunctionNode:
        name = self.current_token.value
        self._advance()
        
        if self.current_token.type != TokenType.LPAREN:
            raise ValueError(f"Expected '(' after function {name}")
        
        self._advance()
        args = []
        
        if self.current_token.type != TokenType.RPAREN:
            args.append(self._parse_expression())
            
            while self.current_token.type == TokenType.COMMA:
                self._advance()
                args.append(self._parse_expression())
        
        if self.current_token.type != TokenType.RPAREN:
            raise ValueError(f"Expected ')' after function arguments")
        
        self._advance()
        return FunctionNode(name, args)


class FormulaEvaluator:
    """Evaluates parsed formula AST"""
    
    def __init__(self, get_cell_value: Callable[[int, int], Any]):
        self.get_cell_value = get_cell_value
        self.functions = {
            'SUM': self._sum,
            'AVERAGE': self._average,
            'MIN': self._min,
            'MAX': self._max,
            'COUNT': self._count,
            'IF': self._if,
            'ABS': self._abs,
            'ROUND': self._round,
            'CONCAT': self._concat,
        }
    
    def evaluate(self, node: ASTNode) -> Any:
        """Evaluate AST node"""
        try:
            return self._evaluate_node(node)
        except ZeroDivisionError:
            return "#DIV/0!"
        except ValueError as e:
            return "#VALUE!"
        except Exception as e:
            return "#ERROR!"
    
    def _evaluate_node(self, node: ASTNode) -> Any:
        if isinstance(node, NumberNode):
            return node.value
        
        elif isinstance(node, StringNode):
            return node.value
        
        elif isinstance(node, CellRefNode):
            try:
                value = self.get_cell_value(node.row, node.col)
                return self._to_number(value) if isinstance(value, str) and value.replace('.', '').replace('-', '').isdigit() else value
            except:
                return "#REF!"
        
        elif isinstance(node, RangeNode):
            values = []
            for row, col in node.cells:
                try:
                    value = self.get_cell_value(row, col)
                    if value != "":
                        values.append(value)
                except:
                    pass
            return values
        
        elif isinstance(node, BinaryOpNode):
            return self._evaluate_binary_op(node)
        
        elif isinstance(node, UnaryOpNode):
            operand = self._evaluate_node(node.operand)
            if node.operator == '+':
                return self._to_number(operand)
            elif node.operator == '-':
                return -self._to_number(operand)
        
        elif isinstance(node, FunctionNode):
            return self._evaluate_function(node)
        
        return "#ERROR!"
    
    def _evaluate_binary_op(self, node: BinaryOpNode) -> Any:
        left = self._evaluate_node(node.left)
        right = self._evaluate_node(node.right)
        
        if isinstance(left, str) and left.startswith('#'):
            return left
        if isinstance(right, str) and right.startswith('#'):
            return right
        
        op = node.operator
        
        if op == '+':
            return self._to_number(left) + self._to_number(right)
        elif op == '-':
            return self._to_number(left) - self._to_number(right)
        elif op == '*':
            return self._to_number(left) * self._to_number(right)
        elif op == '/':
            right_num = self._to_number(right)
            if right_num == 0:
                raise ZeroDivisionError()
            return self._to_number(left) / right_num
        elif op == '^':
            return self._to_number(left) ** self._to_number(right)
        elif op == '=':
            return left == right
        elif op == '<>':
            return left != right
        elif op == '<':
            return self._to_number(left) < self._to_number(right)
        elif op == '<=':
            return self._to_number(left) <= self._to_number(right)
        elif op == '>':
            return self._to_number(left) > self._to_number(right)
        elif op == '>=':
            return self._to_number(left) >= self._to_number(right)
        
        return "#ERROR!"
    
    def _evaluate_function(self, node: FunctionNode) -> Any:
        func_name = node.name.upper()
        if func_name not in self.functions:
            return "#NAME?"
        
        args = [self._evaluate_node(arg) for arg in node.args]
        
        # Check for errors in arguments
        for arg in args:
            if isinstance(arg, str) and arg.startswith('#'):
                return arg
        
        return self.functions[func_name](args)
    
    def _to_number(self, value: Any) -> float:
        """Convert value to number"""
        if isinstance(value, (int, float)):
            return float(value)
        elif isinstance(value, str):
            if value == "":
                return 0.0
            try:
                return float(value)
            except ValueError:
                raise ValueError(f"Cannot convert '{value}' to number")
        elif isinstance(value, bool):
            return 1.0 if value else 0.0
        else:
            raise ValueError(f"Cannot convert {type(value)} to number")
    
    def _flatten_ranges(self, args: List[Any]) -> List[Any]:
        """Flatten range arguments into individual values"""
        result = []
        for arg in args:
            if isinstance(arg, list):
                result.extend(arg)
            else:
                result.append(arg)
        return result
    
    # Built-in functions
    def _sum(self, args: List[Any]) -> float:
        values = self._flatten_ranges(args)
        total = 0.0
        for value in values:
            if value != "":
                total += self._to_number(value)
        return total
    
    def _average(self, args: List[Any]) -> float:
        values = self._flatten_ranges(args)
        numeric_values = [self._to_number(v) for v in values if v != ""]
        if not numeric_values:
            return "#DIV/0!"
        return sum(numeric_values) / len(numeric_values)
    
    def _min(self, args: List[Any]) -> float:
        values = self._flatten_ranges(args)
        numeric_values = [self._to_number(v) for v in values if v != ""]
        if not numeric_values:
            return "#VALUE!"
        return min(numeric_values)
    
    def _max(self, args: List[Any]) -> float:
        values = self._flatten_ranges(args)
        numeric_values = [self._to_number(v) for v in values if v != ""]
        if not numeric_values:
            return "#VALUE!"
        return max(numeric_values)
    
    def _count(self, args: List[Any]) -> int:
        values = self._flatten_ranges(args)
        return len([v for v in values if v != ""])
    
    def _if(self, args: List[Any]) -> Any:
        if len(args) < 2:
            return "#VALUE!"
        
        condition = args[0]
        true_value = args[1]
        false_value = args[2] if len(args) > 2 else ""
        
        if isinstance(condition, bool):
            return true_value if condition else false_value
        else:
            return true_value if self._to_number(condition) != 0 else false_value
    
    def _abs(self, args: List[Any]) -> float:
        if len(args) != 1:
            return "#VALUE!"
        return abs(self._to_number(args[0]))
    
    def _round(self, args: List[Any]) -> float:
        if len(args) < 1 or len(args) > 2:
            return "#VALUE!"
        
        number = self._to_number(args[0])
        digits = int(self._to_number(args[1])) if len(args) > 1 else 0
        return round(number, digits)
    
    def _concat(self, args: List[Any]) -> str:
        return "".join(str(arg) for arg in args)


def parse_formula(formula: str) -> ASTNode:
    """Parse formula string into AST"""
    tokenizer = FormulaTokenizer(formula)
    tokens = tokenizer.tokenize()
    parser = FormulaParser(tokens)
    return parser.parse()


def evaluate_formula(formula: str, get_cell_value: Callable[[int, int], Any]) -> Any:
    """Parse and evaluate formula"""
    try:
        ast = parse_formula(formula)
        evaluator = FormulaEvaluator(get_cell_value)
        return evaluator.evaluate(ast)
    except Exception as e:
        return "#ERROR!"