import pandas as pd
import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# Method → Display Name mapping
operation_name_map = {
    "ExportIFCTeklaAPI": "IFC",
    "CreateMeshGeometry": "MESH",
    "CreateExchangeElementForPrimitive": "Primitive"
}
target_operations = list(operation_name_map.keys())
total_time_operation = "TotalTimeToCreateExchange"


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


def process_csv_files(folder_path, output_console):
    output_blocks = []
    csv_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                 if f.endswith('.csv') and os.path.isfile(os.path.join(folder_path, f))]

    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            file_name = extract_model_name(os.path.basename(csv_file))
            df['Matched Operation'] = df['Operation Name'].apply(match_operation)
            matched_df = df[df['Matched Operation'].notnull()]

            if matched_df.empty:
                continue

            op_summary = matched_df.groupby('Matched Operation').agg(
                Element_Count=('#Events', 'sum'),
                Total_Time_ms=('Operation Time in Milliseconds', 'sum')
            ).reset_index()

            op_summary['Operation'] = op_summary['Matched Operation'].map(operation_name_map)
            op_summary = op_summary[['Operation', 'Element_Count', 'Total_Time_ms']]

            total_time_row = df[df['Operation Name'] == total_time_operation]
            total_time_ms = total_time_row["Operation Time in Milliseconds"].sum() if not total_time_row.empty else None

            block = []
            block.append([f"===== File: {file_name} ====="])
            block.append(["Operation", "Element Count", "Total Time (ms)"])

            for _, row in op_summary.iterrows():
                block.append([
                    row["Operation"],
                    f"{int(row['Element_Count']):,}",
                    f"{int(row['Total_Time_ms']):,}"
                ])

            if total_time_ms is not None:
                block.append(["TotalTimeToCreateExchange", "", f"{int(total_time_ms):,}"])

            block.append([])  # Spacer
            output_blocks.extend(block)

        except Exception as e:
            output_console.insert(tk.END, f"❌ Error processing {csv_file}: {e}\n")

    # Save output
    output_df = pd.DataFrame(output_blocks)
    output_csv_path = os.path.join(folder_path, "operation_summary_grouped.csv")
    output_df.to_csv(output_csv_path, index=False, header=False)

    # Print to console
    output_console.insert(tk.END, "\n===== Summary Output =====\n\n")
    for line in output_blocks:
        if not line:
            output_console.insert(tk.END, "\n")
        elif len(line) == 1:
            output_console.insert(tk.END, f"{line[0]}\n")
        else:
            output_console.insert(tk.END, "{:<30} {:>15} {:>20}\n".format(*line))

    output_console.insert(tk.END, f"\n✔️ Output saved to: {output_csv_path}\n")


# ==== GUI Setup ====
def browse_folder():
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        folder_entry.delete(0, tk.END)
        folder_entry.insert(0, folder_selected)


def run_processing():
    folder_path = folder_entry.get()
    if not os.path.isdir(folder_path):
        messagebox.showerror("Error", "Invalid folder path!")
        return

    output_console.delete(1.0, tk.END)
    process_csv_files(folder_path, output_console)


root = tk.Tk()
root.title("CSV Operation Summary App")
root.geometry("750x600")

frame = tk.Frame(root)
frame.pack(pady=10)

tk.Label(frame, text="📁 Select Folder Containing CSVs:").grid(row=0, column=0, padx=5)
folder_entry = tk.Entry(frame, width=50)
folder_entry.grid(row=0, column=1, padx=5)
tk.Button(frame, text="Browse", command=browse_folder).grid(row=0, column=2, padx=5)

tk.Button(root, text="Run Summary", command=run_processing, bg="green", fg="white").pack(pady=10)

output_console = scrolledtext.ScrolledText(root, width=100, height=30)
output_console.pack()

root.mainloop()