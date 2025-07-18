import os
import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QLabel,
    QFileDialog, QLineEdit, QTextEdit, QComboBox
)
from tekla_processor import process_tekla_csv_files


class CSVSummaryApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CSV Summary App")
        self.setMinimumSize(700, 500)
        self.summary_df = None

        # UI Elements
        self.folder_input = QLineEdit()
        self.folder_input.setReadOnly(True)
        self.browse_btn = QPushButton("📁 Browse")
        self.browse_btn.clicked.connect(self.browse_folder)

        self.connector_choice = QComboBox()
        self.connector_choice.addItems(["Tekla", "Rhino"])

        self.run_btn = QPushButton("▶ Run Summary")
        self.run_btn.clicked.connect(self.run_processing)

        self.console = QTextEdit()
        self.console.setReadOnly(True)

        self.save_btn = QPushButton("💾 Save CSV")
        self.save_btn.clicked.connect(self.save_csv)
        self.save_btn.setEnabled(False)

        self.status = QLabel("")

        # Layouts
        layout = QVBoxLayout()

        folder_row = QHBoxLayout()
        folder_row.addWidget(QLabel("Select Folder:"))
        folder_row.addWidget(self.folder_input)
        folder_row.addWidget(self.browse_btn)
        layout.addLayout(folder_row)

        connector_row = QHBoxLayout()
        connector_row.addWidget(QLabel("Connector:"))
        connector_row.addWidget(self.connector_choice)
        layout.addLayout(connector_row)

        layout.addWidget(self.run_btn)
        layout.addWidget(self.console)
        layout.addWidget(self.save_btn)
        layout.addWidget(self.status)

        self.setLayout(layout)

    def browse_folder(self):
        appdata_local = os.path.join(os.getenv('USERPROFILE'), "AppData", "Local")
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", appdata_local)
        if folder:
            self.folder_input.setText(folder)

    def run_processing(self):
        folder_path = self.folder_input.text()
        self.console.clear()
        self.status.setText("")
        self.save_btn.setEnabled(False)

        if not os.path.isdir(folder_path):
            self.status.setText("⚠️ Invalid folder selected!")
            return

        connector = self.connector_choice.currentText()
        if connector == "Tekla":
            self.summary_df = process_tekla_csv_files(folder_path, self)
        else:
            self.log("🛠️ Rhino processing not implemented.")
            self.status.setText("Rhino logic placeholder.")

    def log(self, msg):
        self.console.append(msg)

    def save_csv(self):
        if self.summary_df is None or self.summary_df.empty:
            self.status.setText("⚠️ No data to save!")
            return

        folder = self.folder_input.text()
        output_path = os.path.join(folder, "final_model_summary.csv")
        self.summary_df.to_csv(output_path, index=False)
        self.log(f"💾 CSV saved to: {output_path}")
        self.status.setText("✅ CSV saved!")
