import pandas as pd
import os
import re

# === Tekla-Specific Operation Mapping ===
# For CREATE data (TotalTimeToCreateExchange)
tekla_create_operation_map = {
    "ExportIFCTeklaAPI": "IFC",
    "CreateMeshGeometry": "Mesh",
    "CreateExchangeElementForPrimitive": "Primitives"
}

# For READ data (TotalExchangeReadTime)
tekla_read_operation_map = {
    "LoadBrepItemInTekla": "IFC",          # LoadBrepItemInTekla: LoadBrepItemInTekla = IFC
    "LoadMeshInTekla": "Mesh",             # LoadMeshInTekla: LoadMeshItem = Mesh
    "LoadPrimitivesInTekla": "Primitives"  # LoadPrimitivesInTekla:Prep = Primitives
}
tekla_total_time_operation = "TotalTimeToCreateExchange"
tekla_read_time_operation = "TotalExchangeReadTime"

# === Tekla-Specific Utility Functions ===
def extract_model_name(file_name):
    """Extract model name from CSV filename using regex pattern."""
    match = re.match(r"metrics_(.*?)_Demo.*\.csv", file_name)
    if match:
        return match.group(1)
    return file_name

def match_operation(op_name, operation_map):
    """Match operation name to target operations using the specified mapping."""
    for internal in operation_map.keys():
        if internal in op_name:
            return internal
    return None

def calculate_elements_per_min(total_elements, time_minutes):
    """Calculate elements per minute based on total elements and time in minutes."""
    if time_minutes > 0:
        return round(total_elements / time_minutes, 2)
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

    # Track what data types are available across all files
    has_any_create_data = False
    has_any_read_data = False

    # First pass: determine what data types exist across all files
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            
            total_time_row = df[df['Operation Name'] == tekla_total_time_operation]
            read_time_row = df[df['Operation Name'] == tekla_read_time_operation]
            
            if not total_time_row.empty:
                has_any_create_data = True
            if not read_time_row.empty:
                has_any_read_data = True
                
        except Exception as e:
            log_output(f"❌ Error checking {csv_file}: {e}\n")

    # Determine which data type to show (create data takes precedence)
    show_create_data = has_any_create_data
    show_read_data = has_any_read_data and not has_any_create_data

    log_output(f"📊 Data availability analysis:\n")
    log_output(f"   - Create data found: {'Yes' if has_any_create_data else 'No'}\n")
    log_output(f"   - Read data found: {'Yes' if has_any_read_data else 'No'}\n")
    log_output(f"   - Will display: {'Create Data' if show_create_data else 'Read Data' if show_read_data else 'No timing data'}\n")
    
    if show_create_data:
        log_output(f"📊 Using CREATE operation mapping: {list(tekla_create_operation_map.keys())}\n\n")
    elif show_read_data:
        log_output(f"📊 Using READ operation mapping: {list(tekla_read_operation_map.keys())}\n\n")
    else:
        log_output(f"📊 No timing data available\n\n")

    # Second pass: process the data
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            model_name = extract_model_name(os.path.basename(csv_file))

            summary = {
                "Data/Model": model_name, 
                "Mesh": 0, 
                "IFC": 0, 
                "Primitives": 0
            }

            # Determine which operation mapping to use and process elements
            total_elements = 0
            if show_create_data:
                # Use CREATE operation mapping
                df['Matched_Operation'] = df['Operation Name'].apply(lambda op_name: match_operation(op_name, tekla_create_operation_map))
                matched_df = df[df['Matched_Operation'].notnull()]
                
                if not matched_df.empty:
                    op_summary = matched_df.groupby('Matched_Operation')['#Events'].sum().to_dict()
                    for op_key, count in op_summary.items():
                        display_name = tekla_create_operation_map.get(op_key)
                        if display_name in summary:
                            summary[display_name] = count
                
                total_elements = summary["Mesh"] + summary["IFC"] + summary["Primitives"]

            elif show_read_data:
                # Use READ operation mapping
                df['Matched_Operation'] = df['Operation Name'].apply(lambda op_name: match_operation(op_name, tekla_read_operation_map))
                matched_df = df[df['Matched_Operation'].notnull()]
                
                if not matched_df.empty:
                    op_summary = matched_df.groupby('Matched_Operation')['#Events'].sum().to_dict()
                    for op_key, count in op_summary.items():
                        display_name = tekla_read_operation_map.get(op_key)
                        if display_name in summary:
                            summary[display_name] = count
                
                total_elements = summary["Mesh"] + summary["IFC"] + summary["Primitives"]

            # Add total elements
            summary["total_elements"] = total_elements

            # Handle timing data based on what should be displayed
            timing_ms = 0
            time_minutes = 0
            
            total_time_row = df[df['Operation Name'] == tekla_total_time_operation]
            read_time_row = df[df['Operation Name'] == tekla_read_time_operation]
            
            if show_create_data and not total_time_row.empty:
                # Show create data
                timing_ms = total_time_row["Operation Time in Milliseconds"].sum()
                time_minutes = round(timing_ms / 60000, 2)
                summary["milliseconds"] = int(timing_ms)
                summary["minutes"] = time_minutes
                
            elif show_read_data and not read_time_row.empty:
                # Show read data (only if no create data available)
                timing_ms = read_time_row["Operation Time in Milliseconds"].sum()
                time_minutes = round(timing_ms / 60000, 2)
                summary["milliseconds"] = int(timing_ms)
                summary["minutes"] = time_minutes
            else:
                # No timing data found
                summary["milliseconds"] = 0
                summary["minutes"] = 0
            
            # Calculate elements per minute
            summary["element_per_min"] = calculate_elements_per_min(summary["total_elements"], time_minutes)

            model_data.append(summary)

        except Exception as e:
            log_output(f"❌ Error processing {csv_file}: {e}\n")

    if not model_data:
        log_output("⚠️ No matching operations found in any CSV files.\n")
        update_status("⚠️ No relevant data found")
        return None

    summary_df = pd.DataFrame(model_data)
    
    # Fill NaN values and set appropriate data types
    numeric_columns = ['Mesh', 'IFC', 'Primitives', 'total_elements', 'milliseconds', 'minutes', 'element_per_min']
    
    for col in numeric_columns:
        if col in summary_df.columns:
            summary_df[col] = summary_df[col].fillna(0)

    # Set integer types for specific columns
    int_columns = ['Mesh', 'IFC', 'Primitives', 'total_elements', 'milliseconds']
    
    for col in int_columns:
        if col in summary_df.columns:
            summary_df[col] = summary_df[col].astype(int)

    log_output("\n" + "="*120 + "\n")
    log_output("                                        TEKLA PROCESSING SUMMARY\n")
    log_output("="*120 + "\n\n")
    
    # Format the DataFrame for display
    formatted_df = summary_df.copy()
    
    # Build column order for display
    display_columns = ['Data/Model', 'Mesh', 'IFC', 'Primitives', 'total_elements', 'milliseconds', 'minutes', 'element_per_min']
    
    if show_create_data:
        log_output("📊 Displaying CREATE DATA (create time takes precedence)\n\n")
    elif show_read_data:
        log_output("📊 Displaying READ DATA (no create data available)\n\n")
    
    # Only include columns that exist in the DataFrame
    available_columns = [col for col in display_columns if col in formatted_df.columns]
    formatted_df = formatted_df[available_columns]
    
    # Format numbers with commas for better readability
    number_columns = ['Mesh', 'IFC', 'Primitives', 'total_elements', 'milliseconds']
    
    for col in number_columns:
        if col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(lambda x: f"{int(x):,}")
    
    # Display the formatted table
    log_output(f"{formatted_df.to_string(index=False, max_colwidth=20, justify='center')}\n\n")
    
    update_status("✅ Processing complete. Click 'Save CSV' to export.")

    return summary_df 