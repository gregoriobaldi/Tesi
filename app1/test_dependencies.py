"""Tests for dependency tracking and recalculation."""

import pytest
from ui import DependencyTracker
from model import SpreadsheetModel, CellData
from formula import evaluate_formula


class TestDependencyTracker:
    """Test the dependency tracking system."""
    
    def setup_method(self):
        self.tracker = DependencyTracker()
        
    def test_add_dependency(self):
        # A1 depends on B1
        self.tracker.add_dependency((0, 0), (0, 1))
        
        assert (0, 1) in self.tracker.dependencies[(0, 0)]
        assert (0, 0) in self.tracker.dependents[(0, 1)]
        
    def test_clear_dependencies(self):
        # Set up dependencies
        self.tracker.add_dependency((0, 0), (0, 1))
        self.tracker.add_dependency((0, 0), (0, 2))
        
        # Clear them
        self.tracker.clear_dependencies((0, 0))
        
        assert (0, 0) not in self.tracker.dependencies
        assert (0, 0) not in self.tracker.dependents.get((0, 1), set())
        assert (0, 0) not in self.tracker.dependents.get((0, 2), set())
        
    def test_get_dependents(self):
        # B1 and C1 depend on A1
        self.tracker.add_dependency((0, 1), (0, 0))  # B1 depends on A1
        self.tracker.add_dependency((0, 2), (0, 0))  # C1 depends on A1
        
        dependents = self.tracker.get_dependents((0, 0))
        assert dependents == {(0, 1), (0, 2)}
        
    def test_cycle_detection(self):
        # Create a cycle: A1 -> B1 -> C1 -> A1
        self.tracker.add_dependency((0, 0), (0, 1))  # A1 depends on B1
        self.tracker.add_dependency((0, 1), (0, 2))  # B1 depends on C1
        self.tracker.add_dependency((0, 2), (0, 0))  # C1 depends on A1
        
        assert self.tracker.has_cycle((0, 0)) is True
        assert self.tracker.has_cycle((0, 1)) is True
        assert self.tracker.has_cycle((0, 2)) is True
        
    def test_no_cycle(self):
        # Create a chain without cycle: A1 -> B1 -> C1
        self.tracker.add_dependency((0, 0), (0, 1))  # A1 depends on B1
        self.tracker.add_dependency((0, 1), (0, 2))  # B1 depends on C1
        
        assert self.tracker.has_cycle((0, 0)) is False
        assert self.tracker.has_cycle((0, 1)) is False
        assert self.tracker.has_cycle((0, 2)) is False


class TestRecalculation:
    """Test recalculation scenarios."""
    
    def setup_method(self):
        self.model = SpreadsheetModel()
        
    def test_simple_recalculation(self):
        # Set up: A1=10, B1=A1*2
        self.model.cells[(0, 0)] = CellData("10", 10)
        
        # B1 should calculate to 20
        result = evaluate_formula("=A1*2", self.model)
        assert result == 20
        
        # Change A1 to 5
        self.model.cells[(0, 0)] = CellData("5", 5)
        
        # B1 should recalculate to 10
        result = evaluate_formula("=A1*2", self.model)
        assert result == 10
        
    def test_chain_recalculation(self):
        # Set up: A1=10, B1=A1*2, C1=B1+5
        self.model.cells[(0, 0)] = CellData("10", 10)
        self.model.cells[(0, 1)] = CellData("=A1*2", 20)
        
        # C1 should be 25 (20 + 5)
        result = evaluate_formula("=B1+5", self.model)
        assert result == 25
        
    def test_range_recalculation(self):
        # Set up range A1:A3 with values 1,2,3
        self.model.cells[(0, 0)] = CellData("1", 1)
        self.model.cells[(1, 0)] = CellData("2", 2)
        self.model.cells[(2, 0)] = CellData("3", 3)
        
        # SUM should be 6
        result = evaluate_formula("=SUM(A1:A3)", self.model)
        assert result == 6
        
        # Change A2 to 10
        self.model.cells[(1, 0)] = CellData("10", 10)
        
        # SUM should recalculate to 14
        result = evaluate_formula("=SUM(A1:A3)", self.model)
        assert result == 14
        
    def test_error_propagation(self):
        # Set up: A1=10, B1=A1/0 (error), C1=B1+5
        self.model.cells[(0, 0)] = CellData("10", 10)
        
        # B1 should be error
        result = evaluate_formula("=A1/0", self.model)
        assert result == "#DIV/0!"
        
        # Set B1 to the error
        self.model.cells[(0, 1)] = CellData("=A1/0", "#DIV/0!")
        self.model.cells[(0, 1)].error = "#DIV/0!"
        
        # C1 should propagate the error
        result = evaluate_formula("=B1+5", self.model)
        assert result == "#DIV/0!"


if __name__ == "__main__":
    pytest.main([__file__])