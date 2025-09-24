package com.spreadsheet;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class BasicTest {
    @Test
    public void testSetGetCell() {
        Model model = new Model();
        Engine engine = new Engine(model);
        engine.setCell("A1", "5");
        assertEquals("5", engine.getCell("A1"));
    }

    @Test
    public void testFormula() {
        Model model = new Model();
        Engine engine = new Engine(model);
        engine.setCell("A1", "5");
        engine.setCell("B1", "3");
        engine.setCell("C1", "=A1+B1");
        assertEquals("8", engine.getCell("C1"));
    }

    @Test
    void testModelDataManagement() {
        Model model = new Model();
        model.setCell("A1", "Test");
        assertEquals("Test", model.getCell("A1"));
    }

    @Test
    void testStoragePersistence() throws Exception {
        Model model = new Model();
        model.setCell("A1", "42");
        Storage.save(model, "testFile.csv");

        Model loadedModel = new Model();
        Storage.load(loadedModel, "testFile.csv");
        assertEquals("42", loadedModel.getCell("A1"));
        // Clean up
        java.nio.file.Files.deleteIfExists(java.nio.file.Paths.get("testFile.csv"));
    }

    @Test
    void testUndoFunctionality() {
        Model model = new Model();
        Undo undo = new Undo();
        model.setCell("A1", "1");
        undo.save(model);
        model.setCell("A1", "2");
        Model prev = undo.undo();
        assertEquals("1", prev.getCell("A1"));
    }
}