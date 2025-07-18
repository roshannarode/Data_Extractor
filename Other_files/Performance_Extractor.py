import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import os
import pandas as pd
import re
from tabulate import tabulate  # NEW: For pretty summary table

# === Global ===
summary_df_global = None
operation_name_map = {
    "ExportIFCTeklaAPI": "IFC",
    "CreateMeshGeometry": "Mesh",
    "CreateExchangeElementForPrimitive": "Primitives"
}
target_operations = list(operation_name_map.keys())

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

        folder_row = toga.Box(style=Pack(direction=ROW, padding=5))
        self.folder_input = toga.TextInput(readonly=True, style=Pack(flex=1))
        browse_btn = toga.Button("📁 Browse", on_press=self.browse_folder, style=Pack(padding_left=5))
        folder_row.add(toga.Label("Select Folder:", style=Pack(width=120)))
        folder_row.add(self.folder_input)
        folder_row.add(browse_btn)
        main_box.add(folder_row)

        connector_row = toga.Box(style=Pack(direction=ROW, padding=5))
        self.connector_choice = toga.Selection(items=["Tekla", "Rhino"], style=Pack(width=200))
        connector_row.add(toga.Label("Connector:", style=Pack(width=120)))
        connector_row.add(self.connector_choice)
        main_box.add(connector_row)

        run_btn = toga.Button("▶ Run Summary", on_press=self.run_processing, style=Pack(padding=10))
        main_box.add(run_btn)

        self.console_output = toga.MultilineTextInput(readonly=True, style=Pack(height=300, padding=5))
        main_box.add(self.console_output)

        self.save_btn = toga.Button("💾 Save CSV", on_press=self.save_csv, enabled=False, style=Pack(padding=5))
        main_box.add(self.save_btn)

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

        all_csvs = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                    if f.endswith('.csv') and os.path.isfile(os.path.join(folder_path, f))]

        create_folder = os.path.join(folder_path, "Create Exchange Data")
        read_folder = os.path.join(folder_path, "Read Exchange Data")

        if os.path.isdir(create_folder):
            all_csvs += [os.path.join(create_folder, f) for f in os.listdir(create_folder)
                         if f.endswith('.csv') and os.path.isfile(os.path.join(create_folder, f))]

        if os.path.isdir(read_folder):
            all_csvs += [os.path.join(read_folder, f) for f in os.listdir(read_folder)
                         if f.endswith('.csv') and os.path.isfile(os.path.join(read_folder, f))]

        if not all_csvs:
            self.log("❌ No CSV files found.")
            self.status_label.text = "⚠️ No CSVs found"
            return

        create_csvs = []
        read_csvs = []

        for csv_file in all_csvs:
            try:
                df = pd.read_csv(csv_file)
                if "Operation Name" not in df.columns:
                    continue
                if "TotalTimeToCreateExchange" in df["Operation Name"].values:
                    create_csvs.append(csv_file)
                elif "TotalTimeToLoadExchange" in df["Operation Name"].values:
                    read_csvs.append(csv_file)
            except Exception as e:
                self.log(f"❌ Could not inspect {os.path.basename(csv_file)}: {e}")

        if not create_csvs and not read_csvs:
            self.log("❌ No recognizable Tekla CSVs found.")
            self.status_label.text = "⚠️ No valid Tekla data"
            return

        model_name_to_summary = {}

        for create_file in create_csvs:
            try:
                model_name = extract_model_name(os.path.basename(create_file))
                self.log(f"📄 Processing Create CSV: {os.path.basename(create_file)}")

                df = pd.read_csv(create_file)
                df['Matched Operation'] = df['Operation Name'].apply(match_operation)
                matched_df = df[df['Matched Operation'].notnull()]

                summary = model_name_to_summary.get(model_name, {
                    "Data/Model": model_name,
                    "Mesh": 0, "IFC": 0, "Primitives": 0,
                    "CreateTime(ms)": 0,
                    "LoadTime(ms)": 0
                })

                if not matched_df.empty:
                    op_summary = matched_df.groupby('Matched Operation')['#Events'].sum().to_dict()
                    for op_key, count in op_summary.items():
                        display_name = operation_name_map.get(op_key)
                        if display_name:
                            summary[display_name] += count

                total_create = df[df['Operation Name'] == "TotalTimeToCreateExchange"]
                if not total_create.empty:
                    summary["CreateTime(ms)"] += int(total_create["Operation Time in Milliseconds"].sum())

                model_name_to_summary[model_name] = summary

            except Exception as e:
                self.log(f"❌ Error processing Create CSV {create_file}: {e}")

        for read_file in read_csvs:
            try:
                model_name = extract_model_name(os.path.basename(read_file))
                self.log(f"📄 Processing Read CSV: {os.path.basename(read_file)}")

                df = pd.read_csv(read_file)
                summary = model_name_to_summary.get(model_name, {
                    "Data/Model": model_name,
                    "Mesh": 0, "IFC": 0, "Primitives": 0,
                    "CreateTime(ms)": 0,
                    "LoadTime(ms)": 0
                })

                total_read = df[df['Operation Name'] == "TotalTimeToLoadExchange"]
                if not total_read.empty:
                    summary["LoadTime(ms)"] += int(total_read["Operation Time in Milliseconds"].sum())

                model_name_to_summary[model_name] = summary

            except Exception as e:
                self.log(f"❌ Error processing Read CSV {read_file}: {e}")

        if not model_name_to_summary:
            self.log("⚠️ No summary data collected.")
            self.status_label.text = "⚠️ Nothing to summarize"
            return

        summary_df = pd.DataFrame(list(model_name_to_summary.values()))
        summary_df["TotalTime(min)"] = ((summary_df["CreateTime(ms)"] + summary_df["LoadTime(ms)"]) / 60000).round(2)

        summary_df = summary_df.fillna(0).astype({
            "Mesh": int, "IFC": int, "Primitives": int,
            "CreateTime(ms)": int, "LoadTime(ms)": int
        })

        summary_df_global = summary_df

        # 👇 NEW: Beautiful console summary
        self.log("\n================= FINAL SUMMARY =================")
        formatted_table = tabulate(
            summary_df,
            headers="keys",
            tablefmt="github",
            showindex=False,
            numalign="right",
            stralign="left"
        )
        self.log(formatted_table)

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
