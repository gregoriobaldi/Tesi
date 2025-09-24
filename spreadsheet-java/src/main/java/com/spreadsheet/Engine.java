package com.spreadsheet;

public class Engine {
    private Model model;

    public Engine(Model model) {
        this.model = model;
    }

    public void setCell(String address, String value) {
        model.setCell(address, value);
    }

    public String getCell(String address) {
        String val = model.getCell(address);
        if (val.startsWith("=")) {
            return Formula.evaluate(val, model);
        }
        return val;
    }
}