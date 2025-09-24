package com.spreadsheet;

public class Main {
    public static void main(String[] args) {
        // Initialize the application
        Model model = new Model();
        Engine engine = new Engine(model);
        Undo undo = new Undo();
        
        // Start the user interface
        UI ui = new UI(engine, model, undo);
        ui.run();
    }
}