package com.spreadsheet;

import java.util.HashMap;
import java.util.Map;

public class Model {
    private Map<String, String> cells = new HashMap<>();

    public void setCell(String address, String value) {
        cells.put(address, value);
    }

    public String getCell(String address) {
        return cells.getOrDefault(address, "");
    }

    public Map<String, String> getAllCells() {
        return cells;
    }
}