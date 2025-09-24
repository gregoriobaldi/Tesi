"""
Calculation engine with dependency tracking and cycle detection.
Handles formula recalculation and dependency management.
"""
from typing import Dict, Set, List, Tuple, Any, Optional
from collections import defaultdict, deque
from model import SpreadsheetModel, parse_address, parse_range
from formula import parse_formula, FormulaEvaluator, ASTNode, CellRefNode, RangeNode, FunctionNode, BinaryOpNode, UnaryOpNode


class DependencyGraph:
    """Manages cell dependencies and recalculation order"""
    
    def __init__(self):
        self.dependents: Dict[Tuple[int, int], Set[Tuple[int, int]]] = defaultdict(set)
        self.dependencies: Dict[Tuple[int, int], Set[Tuple[int, int]]] = defaultdict(set)
        self.ast_cache: Dict[Tuple[int, int], ASTNode] = {}
    
    def clear_dependencies(self, cell: Tuple[int, int]):
        """Clear all dependencies for a cell"""
        # Remove this cell from its dependencies' dependents
        for dep in self.dependencies[cell]:
            self.dependents[dep].discard(cell)
        
        # Clear this cell's dependencies
        self.dependencies[cell].clear()
        
        # Clear AST cache
        if cell in self.ast_cache:
            del self.ast_cache[cell]
    
    def add_dependency(self, dependent: Tuple[int, int], dependency: Tuple[int, int]):
        """Add a dependency relationship"""
        self.dependencies[dependent].add(dependency)
        self.dependents[dependency].add(dependent)
    
    def get_dependencies(self, cell: Tuple[int, int]) -> Set[Tuple[int, int]]:
        """Get all cells that this cell depends on"""
        return self.dependencies[cell].copy()
    
    def get_dependents(self, cell: Tuple[int, int]) -> Set[Tuple[int, int]]:
        """Get all cells that depend on this cell"""
        return self.dependents[cell].copy()
    
    def find_cycles(self, start_cell: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Find cycles starting from a cell using DFS"""
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(cell: Tuple[int, int]) -> bool:
            if cell in rec_stack:
                # Found cycle, return the cycle path
                cycle_start = path.index(cell)
                return path[cycle_start:]
            
            if cell in visited:
                return False
            
            visited.add(cell)
            rec_stack.add(cell)
            path.append(cell)
            
            for dependent in self.dependents[cell]:
                cycle = dfs(dependent)
                if cycle:
                    return cycle
            
            rec_stack.remove(cell)
            path.pop()
            return False
        
        return dfs(start_cell) or []
    
    def topological_sort(self, cells: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Return cells in topological order for recalculation"""
        in_degree = defaultdict(int)
        
        # Calculate in-degrees
        for cell in cells:
            for dep in self.dependencies[cell]:
                if dep in cells:
                    in_degree[cell] += 1
        
        # Start with cells that have no dependencies
        queue = deque([cell for cell in cells if in_degree[cell] == 0])
        result = []
        
        while queue:
            cell = queue.popleft()
            result.append(cell)
            
            # Reduce in-degree for dependents
            for dependent in self.dependents[cell]:
                if dependent in cells:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        return result
    
    def extract_dependencies_from_ast(self, ast: ASTNode) -> Set[Tuple[int, int]]:
        """Extract cell dependencies from AST"""
        dependencies = set()
        
        def visit(node: ASTNode):
            if isinstance(node, CellRefNode):
                dependencies.add((node.row, node.col))
            elif isinstance(node, RangeNode):
                dependencies.update(node.cells)
            elif isinstance(node, BinaryOpNode):
                visit(node.left)
                visit(node.right)
            elif isinstance(node, UnaryOpNode):
                visit(node.operand)
            elif isinstance(node, FunctionNode):
                for arg in node.args:
                    visit(arg)
        
        visit(ast)
        return dependencies


class CalculationEngine:
    """Main calculation engine"""
    
    def __init__(self, model: SpreadsheetModel):
        self.model = model
        self.dependency_graph = DependencyGraph()
        self.dirty_cells: Set[Tuple[int, int]] = set()
        self.calculating = False
    
    def set_cell_formula(self, row: int, col: int, formula: str):
        """Set cell formula and update dependencies"""
        cell_pos = (row, col)
        
        # Clear existing dependencies
        self.dependency_graph.clear_dependencies(cell_pos)
        
        if formula.startswith('='):
            try:
                # Parse formula and cache AST
                ast = parse_formula(formula)
                self.dependency_graph.ast_cache[cell_pos] = ast
                
                # Extract dependencies
                dependencies = self.dependency_graph.extract_dependencies_from_ast(ast)
                
                # Add dependencies
                for dep in dependencies:
                    self.dependency_graph.add_dependency(cell_pos, dep)
                
                # Check for cycles
                cycles = self.dependency_graph.find_cycles(cell_pos)
                if cycles:
                    # Mark all cells in cycle as having cycle error
                    for cycle_cell in cycles:
                        cell = self.model.sheet.get_cell(cycle_cell[0], cycle_cell[1])
                        cell.error = "#CYCLE!"
                        cell.value = "#CYCLE!"
                    return
                
            except Exception as e:
                # Formula parsing error
                cell = self.model.sheet.get_cell(row, col)
                cell.error = "#ERROR!"
                cell.value = "#ERROR!"
                return
        
        # Mark cell and dependents as dirty
        self.mark_dirty(cell_pos)
        
        # Recalculate if not already calculating
        if not self.calculating:
            self.recalculate()
    
    def mark_dirty(self, cell: Tuple[int, int]):
        """Mark cell and all its dependents as dirty"""
        to_mark = {cell}
        marked = set()
        
        while to_mark:
            current = to_mark.pop()
            if current in marked:
                continue
            
            marked.add(current)
            self.dirty_cells.add(current)
            
            # Add dependents to mark
            to_mark.update(self.dependency_graph.get_dependents(current))
    
    def recalculate(self):
        """Recalculate all dirty cells"""
        if self.calculating or not self.dirty_cells:
            return
        
        self.calculating = True
        
        try:
            # Get topological order for dirty cells
            calc_order = self.dependency_graph.topological_sort(self.dirty_cells)
            
            # Recalculate in order
            for cell_pos in calc_order:
                self._calculate_cell(cell_pos)
            
            # Clear dirty cells
            self.dirty_cells.clear()
            
        finally:
            self.calculating = False
    
    def _calculate_cell(self, cell_pos: Tuple[int, int]):
        """Calculate a single cell"""
        row, col = cell_pos
        cell = self.model.sheet.get_cell(row, col)
        
        # Clear previous error
        cell.error = None
        
        if not cell.is_formula():
            # Literal value
            try:
                # Try to convert to number
                if isinstance(cell.raw, str) and cell.raw.replace('.', '').replace('-', '').isdigit():
                    cell.value = float(cell.raw)
                else:
                    cell.value = cell.raw
            except:
                cell.value = cell.raw
        else:
            # Formula
            if cell_pos in self.dependency_graph.ast_cache:
                ast = self.dependency_graph.ast_cache[cell_pos]
                evaluator = FormulaEvaluator(self._get_cell_value)
                result = evaluator.evaluate(ast)
                
                if isinstance(result, str) and result.startswith('#'):
                    cell.error = result
                    cell.value = result
                else:
                    cell.value = result
            else:
                cell.error = "#ERROR!"
                cell.value = "#ERROR!"
    
    def _get_cell_value(self, row: int, col: int) -> Any:
        """Get cell value for formula evaluation"""
        if (row, col) not in self.model.sheet.cells:
            return ""
        
        cell = self.model.sheet.cells[(row, col)]
        return cell.value if cell.value is not None else ""
    
    def recalculate_all(self):
        """Force recalculation of all formula cells"""
        formula_cells = set()
        
        for (row, col), cell in self.model.sheet.cells.items():
            if cell.is_formula():
                formula_cells.add((row, col))
        
        self.dirty_cells.update(formula_cells)
        self.recalculate()
    
    def get_cell_dependencies(self, row: int, col: int) -> List[str]:
        """Get list of cell addresses this cell depends on"""
        dependencies = self.dependency_graph.get_dependencies((row, col))
        return [f"{chr(65 + c)}{r + 1}" for r, c in dependencies]
    
    def get_cell_dependents(self, row: int, col: int) -> List[str]:
        """Get list of cell addresses that depend on this cell"""
        dependents = self.dependency_graph.get_dependents((row, col))
        return [f"{chr(65 + c)}{r + 1}" for r, c in dependents]
    
    def validate_formula(self, formula: str) -> Tuple[bool, str]:
        """Validate formula syntax"""
        try:
            parse_formula(formula)
            return True, ""
        except Exception as e:
            return False, str(e)