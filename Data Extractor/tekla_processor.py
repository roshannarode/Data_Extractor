import pandas as pd
import os
import re

# === Tekla-Specific Operation Mapping ===
tekla_operation_name_map = {
    "ExportIFCTeklaAPI": "IFC",
    "CreateMeshGeometry": "Mesh",
    "CreateExchangeElementForPrimitive": "Primitives"
}
tekla_target_operations = list(tekla_operation_name_map.keys())
tekla_total_time_operation = "TotalTimeToCreateExchange"
tekla_read_time_operation = "TotalExchangeReadTime"  # Added read time operation

# === Tekla-Specific Utility Functions ===
def extract_model_name(file_name):
    """Extract model name from CSV filename using regex pattern."""
    match = re.match(r"metrics_(.*?)_Demo.*\.csv", file_name)
    if match:
        return match.group(1)
    return file_name

def match_operation(op_name):
    """Match operation name to target operations."""
    for internal in tekla_target_operations:
        if internal in op_name:
            return internal
    return None

def calculate_elements_per_min(total_elements, create_time_minutes):
    """Calculate elements per minute based on total elements and create time in minutes."""
    if create_time_minutes > 0:
        return round(total_elements / create_time_minutes, 2)
    return 0

# === Tekla Processing Logic ===
def process_tekla_csv_files(file_paths, output_callback=None, status_callback=None):
    """
    Process Tekla CSV files and return summary DataFrame.
    
    Args:
        file_paths: List of CSV file paths to process
        output_callback: Function to call for output messages (optional)
        status_callback: Function to call for status updates (optional)
    
    Returns:
        pandas.DataFrame: Summary of processed data
    """
    def log_output(message):
        if output_callback:
            output_callback(message)
    
    def update_status(message):
        if status_callback:
            status_callback(message)
    
    log_output("⏳ Processing Tekla files...\n\n")
    model_data = []
    update_status("Processing...")

    csv_files = [f for f in file_paths if f.endswith(".csv") and os.path.isfile(f)]

    if not csv_files:
        log_output("❌ No valid CSV files selected.\n")
        update_status("⚠️ No valid CSV files")
        return None

    for csv_file in csv_files:
        try:
            log_output(f"📄 Processing: {os.path.basename(csv_file)}\n")

            df = pd.read_csv(csv_file)
            model_name = extract_model_name(os.path.basename(csv_file))
            df['Matched Operation'] = df['Operation Name'].apply(match_operation)
            matched_df = df[df['Matched Operation'].notnull()]

            summary = {
                "Data/Model": model_name, 
                "Mesh": 0, 
                "IFC": 0, 
                "Primitives": 0, 
                "milliseconds": 0,
                "read_time_ms": 0,
                "create_time_ms": 0,
                "has_create_time": False,
                "has_read_time": False
            }

            if not matched_df.empty:
                op_summary = matched_df.groupby('Matched Operation')['#Events'].sum().to_dict()
                for op_key, count in op_summary.items():
                    display_name = tekla_operation_name_map.get(op_key)
                    if display_name:
                        summary[display_name] = count

            # Priority logic: Create time takes precedence over read time
            total_time_row = df[df['Operation Name'] == tekla_total_time_operation]
            read_time_row = df[df['Operation Name'] == tekla_read_time_operation]
            
            if not total_time_row.empty:
                # CSV contains create time - use create time and ignore read time
                total_time_ms = total_time_row["Operation Time in Milliseconds"].sum()
                summary["milliseconds"] = int(total_time_ms)
                summary["create_time_ms"] = int(total_time_ms)
                summary["has_create_time"] = True
                summary["has_read_time"] = False
            elif not read_time_row.empty:
                # CSV only contains read time - use read time
                read_time_ms = read_time_row["Operation Time in Milliseconds"].sum()
                summary["read_time_ms"] = int(read_time_ms)
                summary["milliseconds"] = int(read_time_ms)  # Use read time as main time
                summary["has_read_time"] = True
                summary["has_create_time"] = False

            model_data.append(summary)

        except Exception as e:
            log_output(f"❌ Error processing {csv_file}: {e}\n")

    if not model_data:
        log_output("⚠️ No matching operations found in any CSV files.\n")
        update_status("⚠️ No relevant data found")
        return None

    summary_df = pd.DataFrame(model_data)
    summary_df["minutes"] = (summary_df["milliseconds"] / 60000).round(2)
    
    # Conditionally calculate time minutes based on what data is available
    if summary_df["has_create_time"].any():
        summary_df["create_time_minutes"] = (summary_df["create_time_ms"] / 60000).round(2)
    
    if summary_df["has_read_time"].any():
        summary_df["read_time_minutes"] = (summary_df["read_time_ms"] / 60000).round(2)
    
    # Calculate total elements (sum of all operation counts)
    summary_df["total_elements"] = (
        summary_df["Mesh"] + 
        summary_df["IFC"] + 
        summary_df["Primitives"]
    )
    
    # Calculate elements per minute
    summary_df["element_per_min"] = summary_df.apply(
        lambda row: calculate_elements_per_min(row["total_elements"], row["minutes"]), 
        axis=1
    )
    
    # Base data types that always exist
    base_types = {
        "Mesh": int, 
        "IFC": int, 
        "Primitives": int, 
        "milliseconds": int,
        "read_time_ms": int,
        "create_time_ms": int,
        "total_elements": int
    }
    
    summary_df = summary_df.fillna(0).astype(base_types)

    log_output("\n" + "="*120 + "\n")
    log_output("                                        TEKLA PROCESSING SUMMARY\n")
    log_output("="*120 + "\n\n")
    
    # Format the DataFrame for better readability
    formatted_df = summary_df.copy()
    
    # Determine which timing columns to show based on data availability
    has_create = summary_df["has_create_time"].any()
    has_read = summary_df["has_read_time"].any()
    
    # Build dynamic column order based on available timing data
    column_order = ['Data/Model', 'Mesh', 'IFC', 'Primitives', 'total_elements']
    
    if has_create:
        # Show create time columns
        column_order.extend(['create_time_ms', 'create_time_minutes'])
    elif has_read:
        # Show read time columns only if no create time
        column_order.extend(['read_time_ms', 'read_time_minutes'])
    
    # Always include general timing and performance columns
    column_order.extend(['milliseconds', 'minutes', 'element_per_min'])
    
    # Only include columns that exist in the DataFrame and exclude helper columns
    available_columns = [col for col in column_order if col in formatted_df.columns]
    formatted_df = formatted_df[available_columns]
    
    # Format numbers with commas for better readability
    number_columns = ['Mesh', 'IFC', 'Primitives', 'total_elements', 'milliseconds']
    if has_create:
        number_columns.append('create_time_ms')
    elif has_read:
        number_columns.append('read_time_ms')
    
    for col in number_columns:
        if col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(lambda x: f"{int(x):,}")
    
    # Display with better formatting
    log_output(f"{formatted_df.to_string(index=False, max_colwidth=15, justify='center')}\n\n")
    
    update_status("✅ Processing complete. Click 'Save CSV Now' to export.")

    return summary_df 