import pandas as pd
import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# === Global Data Storage ===
summary_df_global = None  # Used to store result DataFrame for saving

# === Operation Mapping ===
operation_name_map = {
    "ExportIFCTeklaAPI": "IFC",
    "CreateMeshGeometry": "Mesh",
    "CreateExchangeElementForPrimitive": "Primitives"
}
target_operations = list(operation_name_map.keys())
total_time_operation = "TotalTimeToCreateExchange"

# === Utility Functions ===
def extract_model_name(file_name):
    match = re.match(r"metrics_(.*?)_Demo.*\.csv", file_name)
    if match:
        return match.group(1)
    return file_name

def match_operation(op_name):
    for internal in target_operations:
        if internal in op_name:
            return internal
    return None

# === Tekla Processing Logic ===
def process_tekla_csv_files(file_paths, output_console, status_label):
    global summary_df_global
    output_console.insert(tk.END, "⏳ Processing Tekla files...\n\n")
    output_console.update()
    model_data = []
    status_label.config(text="Processing...")
    status_label.update()

    csv_files = [f for f in file_paths if f.endswith(".csv") and os.path.isfile(f)]

    if not csv_files:
        output_console.insert(tk.END, "❌ No valid CSV files selected.\n")
        output_console.update()
        status_label.config(text="⚠️ No valid CSV files")
        status_label.update()
        return

    for csv_file in csv_files:
        try:
            output_console.insert(tk.END, f"📄 Processing: {os.path.basename(csv_file)}\n")
            output_console.update()

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
                total_time_ms = total_time_row["Operation Time in Milliseconds"].sum()
                summary["milliseconds"] = int(total_time_ms)

            model_data.append(summary)

        except Exception as e:
            output_console.insert(tk.END, f"❌ Error processing {csv_file}: {e}\n")
            output_console.update()

    if not model_data:
        output_console.insert(tk.END, "⚠️ No matching operations found in any CSV files.\n")
        status_label.config(text="⚠️ No relevant data found")
        return

    summary_df = pd.DataFrame(model_data)
    summary_df["minutes"] = (summary_df["milliseconds"] / 60000).round(2)
    summary_df = summary_df.fillna(0).astype({
        "Mesh": int, "IFC": int, "Primitives": int, "milliseconds": int
    })

    summary_df_global = summary_df  # Store for saving later

    output_console.insert(tk.END, "\n===== Final Summary =====\n\n")
    output_console.insert(tk.END, f"{summary_df.to_string(index=False)}\n")
    output_console.update()
    status_label.config(text="✅ Processing complete. Click 'Save CSV Now' to export.")
    status_label.update()

    # Enable Save button
    save_button.config(state="normal")

# === Rhino Placeholder ===
def process_rhino_placeholder(output_console, status_label):
    output_console.insert(tk.END, "🔧 Rhino processing logic placeholder...\n")
    output_console.insert(tk.END, "💡 Add your Rhino-specific data processing here.\n")
    output_console.update()
    status_label.config(text="🛠️ Rhino logic not yet implemented")
    status_label.update()

# === CSV Saving ===
def save_summary_csv():
    global summary_df_global
    if summary_df_global is None or summary_df_global.empty:
        messagebox.showwarning("No Data", "No summary available to save.")
        return

    file_paths = resolve_file_paths(folder_entry.get().strip())

    if not file_paths:
        messagebox.showerror("Error", "Invalid file or folder selection!")
        return

    folder_path = os.path.dirname(file_paths[0])
    output_csv_path = os.path.join(folder_path, "final_model_summary.csv")
    summary_df_global.to_csv(output_csv_path, index=False)

    output_console.insert(tk.END, f"\n💾 CSV successfully saved to: {output_csv_path}\n")
    output_console.update()
    status_label.config(text="✅ CSV saved")

# === File/Folder Resolution ===
def resolve_file_paths(entry_value):
    if os.path.isdir(entry_value):
        return [os.path.join(entry_value, f) for f in os.listdir(entry_value) if f.endswith(".csv")]
    elif ";" in entry_value:
        return [f for f in entry_value.split(";") if os.path.isfile(f)]
    elif os.path.isfile(entry_value):
        return [entry_value]
    return []

# === Browse (Files or Folder) ===
def browse_files_or_folder():
    file_selected = filedialog.askopenfilenames(filetypes=[("CSV files", "*.csv")])
    if file_selected:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, ";".join(file_selected))
    else:
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            folder_entry.delete(0, tk.END)
            folder_entry.insert(0, folder_selected)

# === Main Run Button ===
def run_processing():
    save_button.config(state="disabled")
    entry_value = folder_entry.get().strip()
    selected_connector = connector_var.get()
    file_paths = resolve_file_paths(entry_value)

    if not file_paths:
        messagebox.showerror("Error", "Please select valid CSV files or a folder containing CSV files!")
        return

    output_console.delete(1.0, tk.END)

    if selected_connector == "Tekla":
        process_tekla_csv_files(file_paths, output_console, status_label)
    elif selected_connector == "Rhino":
        process_rhino_placeholder(output_console, status_label)
    else:
        messagebox.showwarning("Warning", "Please select a valid connector.")

# === GUI Setup ===
root = tk.Tk()
root.title("Data Extractor Version 2")
root.geometry("860x720")
root.resizable(False, False)

style = ttk.Style(root)
try:
    style.theme_use("clam")
except:
    style.theme_use("default")

# === Top Frame ===
top_frame = ttk.Frame(root, padding=15)
top_frame.pack(fill=tk.X)

ttk.Label(top_frame, text="📄 Select CSV Files or Folder:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
folder_entry = ttk.Entry(top_frame, width=60)
folder_entry.grid(row=0, column=1, padx=5)
ttk.Button(top_frame, text="Browse", command=browse_files_or_folder).grid(row=0, column=2, padx=3)

ttk.Label(top_frame, text="🔌 Select Connector:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, padx=5, pady=10, sticky="w")
connector_var = tk.StringVar()
connector_dropdown = ttk.Combobox(top_frame, textvariable=connector_var, state="readonly", width=57)
connector_dropdown['values'] = ("Tekla", "Rhino")
connector_dropdown.current(0)
connector_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="w")

# === Run Button ===
ttk.Button(root, text="▶ Run Summary", command=run_processing).pack(pady=10)

# === Console Output ===
output_console = scrolledtext.ScrolledText(root, width=110, height=28, font=("Consolas", 10))
output_console.pack(padx=10)

# === Save Button at Bottom ===
bottom_frame = ttk.Frame(root, padding=10)
bottom_frame.pack()

save_button = ttk.Button(bottom_frame, text="💾 Save CSV Now", command=save_summary_csv, state="disabled")
save_button.grid(row=0, column=0, padx=5)

# === Status Label ===
status_label = ttk.Label(root, text="", font=("Segoe UI", 9, "italic"), foreground="green")
status_label.pack(pady=5)

# === Run App ===
root.mainloop()
