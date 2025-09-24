"""Formula parsing and evaluation engine."""

import re
import math
from typing import Any, Dict, List, Tuple, Union, Optional
from enum import Enum
from model import parse_cell_ref, parse_range, format_cell_ref


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
    def __init__(self, type_: TokenType, value: str, pos: int = 0):
        self.type = type_
        self.value = value
        self.pos = pos


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
    def __init__(self, start: Tuple[int, int], end: Tuple[int, int]):
        self.start = start
        self.end = end


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


class FormulaLexer:
    """Tokenizes formula strings."""
    
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        
    def tokenize(self) -> List[Token]:
        tokens = []
        while self.pos < len(self.text):
            if self.text[self.pos].isspace():
                self.pos += 1
            elif self.text[self.pos].isdigit() or self.text[self.pos] == '.':
                tokens.append(self._read_number())
            elif self.text[self.pos] == '"':
                tokens.append(self._read_string())
            elif self.text[self.pos].isalpha():
                tokens.append(self._read_identifier())
            elif self.text[self.pos] in '+-*/^':
                tokens.append(Token(TokenType.OPERATOR, self.text[self.pos]))
                self.pos += 1
            elif self.text[self.pos:self.pos+2] in ['<=', '>=', '<>', '!=']:
                tokens.append(Token(TokenType.OPERATOR, self.text[self.pos:self.pos+2]))
                self.pos += 2
            elif self.text[self.pos] in '<>=':
                tokens.append(Token(TokenType.OPERATOR, self.text[self.pos]))
                self.pos += 1
            elif self.text[self.pos] == '(':
                tokens.append(Token(TokenType.LPAREN, '('))
                self.pos += 1
            elif self.text[self.pos] == ')':
                tokens.append(Token(TokenType.RPAREN, ')'))
                self.pos += 1
            elif self.text[self.pos] == ',':
                tokens.append(Token(TokenType.COMMA, ','))
                self.pos += 1
            elif self.text[self.pos] == ':':
                tokens.append(Token(TokenType.OPERATOR, ':'))
                self.pos += 1
            else:
                raise ValueError(f"Unexpected character: {self.text[self.pos]}")
                
        tokens.append(Token(TokenType.EOF, ''))
        return self._process_ranges(tokens)
        
    def _read_number(self) -> Token:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isdigit() or self.text[self.pos] == '.'):
            self.pos += 1
        return Token(TokenType.NUMBER, self.text[start:self.pos])
        
    def _read_string(self) -> Token:
        self.pos += 1  # Skip opening quote
        start = self.pos
        while self.pos < len(self.text) and self.text[self.pos] != '"':
            self.pos += 1
        value = self.text[start:self.pos]
        self.pos += 1  # Skip closing quote
        return Token(TokenType.STRING, value)
        
    def _read_identifier(self) -> Token:
        start = self.pos
        while self.pos < len(self.text) and (self.text[self.pos].isalnum() or self.text[self.pos] in '_'):
            self.pos += 1
            
        # Check if followed by digits (cell reference)
        if self.pos < len(self.text) and self.text[self.pos].isdigit():
            while self.pos < len(self.text) and self.text[self.pos].isdigit():
                self.pos += 1
            return Token(TokenType.CELL_REF, self.text[start:self.pos])
            
        # Check if it's a function (followed by parenthesis)
        value = self.text[start:self.pos]
        if self.pos < len(self.text) and self.text[self.pos] == '(':
            return Token(TokenType.FUNCTION, value)
            
        return Token(TokenType.CELL_REF, value)  # Assume cell ref for now
        
    def _process_ranges(self, tokens: List[Token]) -> List[Token]:
        """Convert CELL_REF:CELL_REF to RANGE tokens."""
        result = []
        i = 0
        while i < len(tokens):
            if (i + 2 < len(tokens) and 
                tokens[i].type == TokenType.CELL_REF and
                tokens[i + 1].type == TokenType.OPERATOR and
                tokens[i + 1].value == ':' and
                tokens[i + 2].type == TokenType.CELL_REF):
                # Create range token
                range_value = f"{tokens[i].value}:{tokens[i + 2].value}"
                result.append(Token(TokenType.RANGE, range_value))
                i += 3
            else:
                result.append(tokens[i])
                i += 1
        return result


class FormulaParser:
    """Parses tokens into an AST using Pratt parsing."""
    
    PRECEDENCE = {
        '=': 1, '<>': 1, '!=': 1, '<': 1, '<=': 1, '>': 1, '>=': 1,
        '+': 2, '-': 2,
        '*': 3, '/': 3,
        '^': 4
    }
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        
    def parse(self) -> ASTNode:
        return self._parse_expression(0)
        
    def _current_token(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else Token(TokenType.EOF, '')
        
    def _consume(self, expected_type: TokenType = None) -> Token:
        token = self._current_token()
        if expected_type and token.type != expected_type:
            raise ValueError(f"Expected {expected_type}, got {token.type}")
        self.pos += 1
        return token
        
    def _parse_expression(self, min_precedence: int) -> ASTNode:
        left = self._parse_primary()
        
        while True:
            token = self._current_token()
            if token.type != TokenType.OPERATOR or self.PRECEDENCE.get(token.value, 0) < min_precedence:
                break
                
            op = self._consume(TokenType.OPERATOR)
            right = self._parse_expression(self.PRECEDENCE[op.value] + 1)
            left = BinaryOpNode(left, op.value, right)
            
        return left
        
    def _parse_primary(self) -> ASTNode:
        token = self._current_token()
        
        if token.type == TokenType.NUMBER:
            self._consume()
            return NumberNode(float(token.value))
        elif token.type == TokenType.STRING:
            self._consume()
            return StringNode(token.value)
        elif token.type == TokenType.CELL_REF:
            self._consume()
            try:
                row, col = parse_cell_ref(token.value)
                return CellRefNode(row, col)
            except ValueError:
                raise ValueError(f"Invalid cell reference: {token.value}")
        elif token.type == TokenType.RANGE:
            self._consume()
            try:
                start, end = parse_range(token.value)
                return RangeNode(start, end)
            except ValueError:
                raise ValueError(f"Invalid range: {token.value}")
        elif token.type == TokenType.FUNCTION:
            return self._parse_function()
        elif token.type == TokenType.LPAREN:
            self._consume()
            expr = self._parse_expression(0)
            self._consume(TokenType.RPAREN)
            return expr
        elif token.type == TokenType.OPERATOR and token.value in ['+', '-']:
            op = self._consume()
            operand = self._parse_primary()
            return UnaryOpNode(op.value, operand)
        else:
            raise ValueError(f"Unexpected token: {token.value}")
            
    def _parse_function(self) -> FunctionNode:
        name = self._consume(TokenType.FUNCTION).value
        self._consume(TokenType.LPAREN)
        
        args = []
        if self._current_token().type != TokenType.RPAREN:
            args.append(self._parse_expression(0))
            while self._current_token().type == TokenType.COMMA:
                self._consume()
                args.append(self._parse_expression(0))
                
        self._consume(TokenType.RPAREN)
        return FunctionNode(name, args)


class FormulaEvaluator:
    """Evaluates AST nodes."""
    
    def __init__(self, model):
        self.model = model
        
    def evaluate(self, node: ASTNode) -> Any:
        if isinstance(node, NumberNode):
            return node.value
        elif isinstance(node, StringNode):
            return node.value
        elif isinstance(node, CellRefNode):
            cell = self.model.get_cell(node.row, node.col)
            if cell is None:
                return 0
            if cell.error:
                return cell.error
            return cell.value if cell.value != "" else 0
        elif isinstance(node, RangeNode):
            return self.model.get_range_values(node.start, node.end)
        elif isinstance(node, BinaryOpNode):
            return self._evaluate_binary_op(node)
        elif isinstance(node, UnaryOpNode):
            return self._evaluate_unary_op(node)
        elif isinstance(node, FunctionNode):
            return self._evaluate_function(node)
        else:
            raise ValueError(f"Unknown node type: {type(node)}")
            
    def _evaluate_binary_op(self, node: BinaryOpNode) -> Any:
        left = self.evaluate(node.left)
        right = self.evaluate(node.right)
        
        # Handle errors
        if isinstance(left, str) and left.startswith('#'):
            return left
        if isinstance(right, str) and right.startswith('#'):
            return right
            
        op = node.operator
        try:
            if op == '+':
                return left + right
            elif op == '-':
                return left - right
            elif op == '*':
                return left * right
            elif op == '/':
                if right == 0:
                    return "#DIV/0!"
                return left / right
            elif op == '^':
                return left ** right
            elif op == '=':
                return 1 if left == right else 0
            elif op in ['<>', '!=']:
                return 1 if left != right else 0
            elif op == '<':
                return 1 if left < right else 0
            elif op == '<=':
                return 1 if left <= right else 0
            elif op == '>':
                return 1 if left > right else 0
            elif op == '>=':
                return 1 if left >= right else 0
            else:
                return "#VALUE!"
        except (TypeError, ValueError):
            return "#VALUE!"
            
    def _evaluate_unary_op(self, node: UnaryOpNode) -> Any:
        operand = self.evaluate(node.operand)
        if isinstance(operand, str) and operand.startswith('#'):
            return operand
            
        try:
            if node.operator == '+':
                return +operand
            elif node.operator == '-':
                return -operand
            else:
                return "#VALUE!"
        except (TypeError, ValueError):
            return "#VALUE!"
            
    def _evaluate_function(self, node: FunctionNode) -> Any:
        name = node.name.upper()
        args = [self.evaluate(arg) for arg in node.args]
        
        # Check for errors in arguments
        for arg in args:
            if isinstance(arg, str) and arg.startswith('#'):
                return arg
                
        try:
            if name == 'SUM':
                total = 0
                for arg in args:
                    if isinstance(arg, list):
                        total += sum(arg)
                    elif isinstance(arg, (int, float)):
                        total += arg
                return total
            elif name == 'AVERAGE':
                values = []
                for arg in args:
                    if isinstance(arg, list):
                        values.extend(arg)
                    elif isinstance(arg, (int, float)):
                        values.append(arg)
                return sum(values) / len(values) if values else 0
            elif name == 'MIN':
                values = []
                for arg in args:
                    if isinstance(arg, list):
                        values.extend(arg)
                    elif isinstance(arg, (int, float)):
                        values.append(arg)
                return min(values) if values else 0
            elif name == 'MAX':
                values = []
                for arg in args:
                    if isinstance(arg, list):
                        values.extend(arg)
                    elif isinstance(arg, (int, float)):
                        values.append(arg)
                return max(values) if values else 0
            elif name == 'COUNT':
                count = 0
                for arg in args:
                    if isinstance(arg, list):
                        count += len(arg)
                    elif isinstance(arg, (int, float)):
                        count += 1
                return count
            elif name == 'IF':
                if len(args) < 2:
                    return "#VALUE!"
                condition = args[0]
                true_val = args[1] if len(args) > 1 else ""
                false_val = args[2] if len(args) > 2 else ""
                return true_val if condition else false_val
            elif name == 'ABS':
                if len(args) != 1:
                    return "#VALUE!"
                return abs(args[0])
            elif name == 'ROUND':
                if len(args) < 1 or len(args) > 2:
                    return "#VALUE!"
                digits = int(args[1]) if len(args) > 1 else 0
                return round(args[0], digits)
            elif name == 'CONCAT':
                return ''.join(str(arg) for arg in args)
            else:
                return "#NAME?"
        except (TypeError, ValueError, ZeroDivisionError):
            return "#VALUE!"


def parse_formula(formula: str) -> ASTNode:
    """Parse a formula string into an AST."""
    if not formula.startswith('='):
        raise ValueError("Formula must start with =")
    
    lexer = FormulaLexer(formula[1:])  # Skip the =
    tokens = lexer.tokenize()
    parser = FormulaParser(tokens)
    return parser.parse()


def evaluate_formula(formula: str, model) -> Any:
    """Parse and evaluate a formula."""
    try:
        ast = parse_formula(formula)
        evaluator = FormulaEvaluator(model)
        return evaluator.evaluate(ast)
    except Exception as e:
        return f"#VALUE!"