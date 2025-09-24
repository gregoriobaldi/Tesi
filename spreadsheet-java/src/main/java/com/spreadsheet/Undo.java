package com.spreadsheet;

import java.util.Stack;

public class Undo {
    private Stack<Model> history = new Stack<>();

    // This class implements functionality for undoing actions within the spreadsheet.
    // It may include methods for tracking changes and reverting to previous states.

    // Example method to undo the last action
    public void undoLastAction() {
        // Logic to undo the last action
    }

    // Example method to track changes
    public void trackChange(Object change) {
        // Logic to track changes
    }

    // Example method to revert to a previous state
    public void revertToPreviousState() {
        // Logic to revert to a previous state
    }

    public void save(Model model) {
        Model copy = new Model();
        for (String key : model.getAllCells().keySet()) {
            copy.setCell(key, model.getCell(key));
        }
        history.push(copy);
    }

    public Model undo() {
        if (!history.isEmpty()) {
            return history.pop();
        }
        return null;
    }
}