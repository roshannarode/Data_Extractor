import os
import pandas as pd
from tabulate import tabulate
from utils import extract_model_name, match_operation, operation_name_map

def process_tekla_csv_files(folder_path, ui):
    ui['status'].text = "Processing..."
    ui['console'].value += "⏳ Processing Tekla files...\n"

    all_csvs = []
    for sub in ["", "Create Exchange Data", "Read Exchange Data"]:
        path = os.path.join(folder_path, sub)
        if os.path.isdir(path):
            all_csvs += [os.path.join(path, f) for f in os.listdir(path) if f.endswith(".csv")]

    create_csvs, read_csvs = [], []
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
            ui['console'].value += f"❌ Could not inspect {os.path.basename(csv_file)}: {e}\n"

    model_summary = {}

    for create_file in create_csvs:
        try:
            model = extract_model_name(os.path.basename(create_file))
            df = pd.read_csv(create_file)
            df['Matched Operation'] = df['Operation Name'].apply(match_operation)
            summary = model_summary.get(model, default_summary(model))

            matched = df[df['Matched Operation'].notnull()]
            if not matched.empty:
                op_summary = matched.groupby('Matched Operation')['#Events'].sum().to_dict()
                for op_key, count in op_summary.items():
                    display = operation_name_map.get(op_key)
                    if display:
                        summary[display] += count

            total_create = df[df['Operation Name'] == "TotalTimeToCreateExchange"]
            if not total_create.empty:
                summary["CreateTime(ms)"] += int(total_create["Operation Time in Milliseconds"].sum())

            model_summary[model] = summary
            ui['console'].value += f"📄 Processed Create: {os.path.basename(create_file)}\n"
        except Exception as e:
            ui['console'].value += f"❌ Error in Create CSV: {e}\n"

    for read_file in read_csvs:
        try:
            model = extract_model_name(os.path.basename(read_file))
            df = pd.read_csv(read_file)
            summary = model_summary.get(model, default_summary(model))

            total_read = df[df['Operation Name'] == "TotalTimeToLoadExchange"]
            if not total_read.empty:
                summary["LoadTime(ms)"] += int(total_read["Operation Time in Milliseconds"].sum())

            model_summary[model] = summary
            ui['console'].value += f"📄 Processed Read: {os.path.basename(read_file)}\n"
        except Exception as e:
            ui['console'].value += f"❌ Error in Read CSV: {e}\n"

    if not model_summary:
        ui['status'].text = "⚠️ Nothing to summarize"
        return None

    df = pd.DataFrame(model_summary.values())
    df["TotalTime(min)"] = ((df["CreateTime(ms)"] + df["LoadTime(ms)"]) / 60000).round(2)
    df = df.fillna(0).astype({
        "Mesh": int, "IFC": int, "Primitives": int,
        "CreateTime(ms)": int, "LoadTime(ms)": int
    })

    ui['console'].value += "\n================= FINAL SUMMARY =================\n"
    ui['console'].value += tabulate(df, headers="keys", tablefmt="github", showindex=False)
    ui['status'].text = "✅ Done. Click 'Save CSV' to export."
    ui['save_btn'].enabled = True
    return df

def default_summary(model):
    return {
        "Data/Model": model,
        "Mesh": 0, "IFC": 0, "Primitives": 0,
        "CreateTime(ms)": 0, "LoadTime(ms)": 0
    }
