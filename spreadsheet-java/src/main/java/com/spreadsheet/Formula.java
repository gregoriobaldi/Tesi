package com.spreadsheet;

public class Formula {
    public static String evaluate(String expr, Model model) {
        expr = expr.trim();
        if (!expr.startsWith("=")) return expr;
        expr = expr.substring(1);
        // Simple formula: =A1+B1
        String[] tokens = expr.split("\\+");
        int sum = 0;
        for (String token : tokens) {
            token = token.trim();
            String val = model.getCell(token);
            try {
                sum += Integer.parseInt(val);
            } catch (NumberFormatException e) {
                // Not a number, ignore
            }
        }
        return String.valueOf(sum);
    }
}