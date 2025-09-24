package com.spreadsheet;

import java.io.*;
import java.util.Map;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;

public class Storage {
    // This class handles data persistence for the spreadsheet application.
    
    public static void save(Model model, String filename) throws IOException {
        if (filename.endsWith(".json")) {
            ObjectMapper mapper = new ObjectMapper();
            mapper.writerWithDefaultPrettyPrinter().writeValue(new File(filename), model.getAllCells());
        } else {
            try (BufferedWriter writer = new BufferedWriter(new FileWriter(filename))) {
                for (Map.Entry<String, String> entry : model.getAllCells().entrySet()) {
                    writer.write(entry.getKey() + "," + entry.getValue());
                    writer.newLine();
                }
            }
        }
    }

    public static void load(Model model, String filename) throws IOException {
        model.getAllCells().clear(); // Clear previous data
        if (filename.endsWith(".json")) {
            ObjectMapper mapper = new ObjectMapper();
            Map<String, String> data = mapper.readValue(new File(filename), new TypeReference<Map<String, String>>() {});
            for (Map.Entry<String, String> entry : data.entrySet()) {
                model.setCell(entry.getKey(), entry.getValue());
            }
        } else {
            try (BufferedReader reader = new BufferedReader(new FileReader(filename))) {
                String line;
                while ((line = reader.readLine()) != null) {
                    String[] parts = line.split(",", 2);
                    if (parts.length == 2) {
                        model.setCell(parts[0], parts[1]);
                    }
                }
            }
        }
    }
}