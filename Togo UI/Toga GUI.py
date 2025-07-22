import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import os
import pandas as pd
import re

# === Global ===
summary_df_global = None
operation_name_map = {
    "ExportIFCTeklaAPI": "IFC",
    "CreateMeshGeometry": "Mesh",
    "CreateExchangeElementForPrimitive": "Primitives"
}
target_operations = list(operation_name_map.keys())
total_time_operation = "TotalTimeToCreateExchange"

def extract_model_name(file_name):
    match = re.match(r"metrics_(.*?)_Demo.*\.csv", file_name)
    return match.group(1) if match else file_name

def match_operation(op_name):
    for internal in target_operations:
        if internal in op_name:
            return internal
    return None

class CSVSummaryApp(toga.App):

    def startup(self):
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # === Folder Input ===
        folder_row = toga.Box(style=Pack(direction=ROW, padding=5))
        self.folder_input = toga.TextInput(readonly=True, style=Pack(flex=1))
        browse_btn = toga.Button("📁 Browse", on_press=self.browse_folder, style=Pack(padding_left=5))
        folder_row.add(toga.Label("Select Folder:", style=Pack(width=120)))
        folder_row.add(self.folder_input)
        folder_row.add(browse_btn)
        main_box.add(folder_row)

        # === Connector Dropdown ===
        connector_row = toga.Box(style=Pack(direction=ROW, padding=5))
        self.connector_choice = toga.Selection(items=["Tekla", "Rhino"], style=Pack(width=200))
        connector_row.add(toga.Label("Connector:", style=Pack(width=120)))
        connector_row.add(self.connector_choice)
        main_box.add(connector_row)

        # === Run Button ===
        run_btn = toga.Button("▶ Run Summary", on_press=self.run_processing, style=Pack(padding=10))
        main_box.add(run_btn)

        # === Output Console ===
        self.console_output = toga.MultilineTextInput(readonly=True, style=Pack(height=300, padding=5))
        main_box.add(self.console_output)

        # === Save Button ===
        self.save_btn = toga.Button("💾 Save CSV", on_press=self.save_csv, enabled=False, style=Pack(padding=5))
        main_box.add(self.save_btn)

        # === Status Label ===
        self.status_label = toga.Label("", style=Pack(padding_top=10, color="green"))
        main_box.add(self.status_label)

        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = main_box
        self.main_window.show()

    async def browse_folder(self, widget):
        folder_path = await self.main_window.select_folder_dialog("Select Folder")
        if folder_path:
            self.folder_input.value = folder_path

    def log(self, msg):
        self.console_output.value += msg + "\n"

    def run_processing(self, widget):
        self.save_btn.enabled = False
        self.console_output.value = ""
        folder_path = self.folder_input.value
        connector = self.connector_choice.value

        if not os.path.isdir(folder_path):
            self.status_label.text = "Invalid folder selected!"
            return

        if connector == "Tekla":
            self.process_tekla_csv_files(folder_path)
        else:
            self.log("🛠️ Rhino processing not yet implemented.")
            self.status_label.text = "Rhino logic placeholder."

    def process_tekla_csv_files(self, folder_path):
        global summary_df_global
        self.log("⏳ Processing Tekla files...\n")
        self.status_label.text = "Processing..."
        model_data = []

        csv_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                     if f.endswith('.csv') and os.path.isfile(os.path.join(folder_path, f))]

        if not csv_files:
            self.log("❌ No CSV files found.")
            self.status_label.text = "⚠️ No CSV files"
            return

        for csv_file in csv_files:
            try:
                self.log(f"📄 Processing: {os.path.basename(csv_file)}")
                df = pd.read_csv(csv_file)
                model_name = extract_model_name(os.path.basename(csv_file))
                df['Matched Operation'] = df['Operation Name'].apply(match_operation)
                matched_df = df[df['Matched Operation'].notnull()]

                summary = {"Data/Model": model_name, "Mesh": 0, "IFC": 0, "Primitives": 0, "milliseconds": 0}

                if not matched_df.empty:
                    op_summary = matched_df.groupby('Matched Operation')['#Events'].sum().to_dict()
                    for op_key, count in op_summary.items():
                        display_name = operation_name_map.get(op_key)
                        if display_name:
                            summary[display_name] = count

                total_time_row = df[df['Operation Name'] == total_time_operation]
                if not total_time_row.empty:
                    summary["milliseconds"] = int(total_time_row["Operation Time in Milliseconds"].sum())

                model_data.append(summary)

            except Exception as e:
                self.log(f"❌ Error processing {csv_file}: {e}")

        if not model_data:
            self.log("⚠️ No matching operations found.")
            self.status_label.text = "⚠️ No relevant data"
            return

        summary_df = pd.DataFrame(model_data)
        summary_df["minutes"] = (summary_df["milliseconds"] / 60000).round(2)
        summary_df = summary_df.fillna(0).astype({
            "Mesh": int, "IFC": int, "Primitives": int, "milliseconds": int
        })

        summary_df_global = summary_df
        self.log("\n===== Final Summary =====\n")
        self.log(summary_df.to_string(index=False))
        self.status_label.text = "✅ Done. Click 'Save CSV' to export."
        self.save_btn.enabled = True

    def save_csv(self, widget):
        global summary_df_global
        if summary_df_global is None or summary_df_global.empty:
            self.status_label.text = "⚠️ No data to save!"
            return

        folder_path = self.folder_input.value
        output_path = os.path.join(folder_path, "final_model_summary.csv")
        summary_df_global.to_csv(output_path, index=False)
        self.log(f"💾 CSV saved to: {output_path}")
        self.status_label.text = "✅ CSV saved!"

def main():
    return CSVSummaryApp("CSV Summary App", "org.example.csvsummary")

if __name__ == "__main__":
    main().main_loop()

