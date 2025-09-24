package com.spreadsheet;

import javax.swing.*;
import javax.swing.table.AbstractTableModel;
import java.awt.*;
import java.awt.event.*;
import java.io.File;
import java.util.Scanner;

public class UI extends JFrame {
    private Engine engine;
    private Model model;
    private Undo undo;
    private JTable table;
    private SpreadsheetTableModel tableModel;

    public UI(Engine engine, Model model, Undo undo) {
        this.engine = engine;
        this.model = model;
        this.undo = undo;
        setTitle("Java Spreadsheet");
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setSize(800, 400);

        tableModel = new SpreadsheetTableModel(engine, model);
        table = new JTable(tableModel);

        JScrollPane scrollPane = new JScrollPane(table);
        add(scrollPane, BorderLayout.CENTER);

        JPanel buttonPanel = new JPanel();
        JButton saveBtn = new JButton("Save");
        JButton loadBtn = new JButton("Load");
        JButton undoBtn = new JButton("Undo");

        saveBtn.addActionListener(e -> saveAction());
        loadBtn.addActionListener(e -> loadAction());
        undoBtn.addActionListener(e -> undoAction());

        buttonPanel.add(saveBtn);
        buttonPanel.add(loadBtn);
        buttonPanel.add(undoBtn);

        add(buttonPanel, BorderLayout.SOUTH);

        table.addPropertyChangeListener(evt -> {
            if ("tableCellEditor".equals(evt.getPropertyName())) {
                if (!table.isEditing()) {
                    int row = table.getSelectedRow();
                    int col = table.getSelectedColumn();
                    String cellName = tableModel.getCellName(row, col);
                    String value = (String) table.getValueAt(row, col);
                    undo.save(model);
                    engine.setCell(cellName, value);
                    tableModel.fireTableDataChanged();
                }
            }
        });
    }

    private void saveAction() {
        JFileChooser chooser = new JFileChooser();
        if (chooser.showSaveDialog(this) == JFileChooser.APPROVE_OPTION) {
            File file = chooser.getSelectedFile();
            try {
                Storage.save(model, file.getAbsolutePath());
                JOptionPane.showMessageDialog(this, "Saved!");
            } catch (Exception ex) {
                JOptionPane.showMessageDialog(this, "Error: " + ex.getMessage());
            }
        }
    }

    private void loadAction() {
        JFileChooser chooser = new JFileChooser();
        if (chooser.showOpenDialog(this) == JFileChooser.APPROVE_OPTION) {
            File file = chooser.getSelectedFile();
            try {
                Storage.load(model, file.getAbsolutePath());
                tableModel.fireTableDataChanged();
                JOptionPane.showMessageDialog(this, "Loaded!");
            } catch (Exception ex) {
                JOptionPane.showMessageDialog(this, "Error: " + ex.getMessage());
            }
        }
    }

    private void undoAction() {
        Model prev = undo.undo();
        if (prev != null) {
            model.getAllCells().clear();
            model.getAllCells().putAll(prev.getAllCells());
            tableModel.fireTableDataChanged();
        }
    }

    public void run() {
        SwingUtilities.invokeLater(() -> setVisible(true));
    }

    // Table model for spreadsheet
    static class SpreadsheetTableModel extends AbstractTableModel {
        private final int ROWS = 20;
        private final int COLS = 10;
        private Engine engine;
        private Model model;

        public SpreadsheetTableModel(Engine engine, Model model) {
            this.engine = engine;
            this.model = model;
        }

        @Override
        public int getRowCount() {
            return ROWS;
        }

        @Override
        public int getColumnCount() {
            return COLS;
        }

        @Override
        public String getColumnName(int column) {
            return String.valueOf((char) ('A' + column));
        }

        public String getCellName(int row, int col) {
            return getColumnName(col) + (row + 1);
        }

        @Override
        public Object getValueAt(int rowIndex, int columnIndex) {
            String cellName = getCellName(rowIndex, columnIndex);
            String value = model.getCell(cellName);
            if (value != null && value.startsWith("=")) {
                return engine.getCell(cellName);
            }
            return value;
        }

        @Override
        public boolean isCellEditable(int rowIndex, int columnIndex) {
            return true;
        }

        @Override
        public void setValueAt(Object aValue, int rowIndex, int columnIndex) {
            String cellName = getCellName(rowIndex, columnIndex);
            model.setCell(cellName, aValue.toString());
            fireTableCellUpdated(rowIndex, columnIndex);
        }
    }
}