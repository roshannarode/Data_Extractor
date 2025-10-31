import pandas as pd
import os
import re

# Operation mappings for different data types
CREATE_OPERATIONS = {
    "ExportIFCTeklaAPI": "IFC",
    "CreateMeshGeometry": "Mesh",
    "CreateExchangeElementForPrimitive": "Primitives"
}

READ_OPERATIONS = {
    "LoadBrepItemInTekla": "IFC",
    "LoadMeshInTekla": "Mesh",
    "LoadPrimitivesInTekla": "Primitives"
}

# Time operation names
CREATE_TIME_OPERATION = "TotalTimeToCreateExchange"
READ_TIME_OPERATION = "TotalExchangeReadTime"

def extract_model_name(file_name):
    """Extract model name from CSV filename."""
    match = re.match(r"metrics_(.*?)_Demo.*\.csv", file_name)
    return match.group(1) if match else file_name

def find_matching_operation(operation_name, operation_map):
    """Find which operation type matches the given operation name."""
    for key in operation_map:
        if key in operation_name:
            return key
    return None

def calculate_elements_per_minute(total_elements, time_minutes):
    """Calculate processing rate in elements per minute."""
    return round(total_elements / time_minutes, 2) if time_minutes > 0 else 0

def process_single_file(csv_file):
    """Process a single CSV file and return summary data."""
    try:
        df = pd.read_csv(csv_file)
        model_name = extract_model_name(os.path.basename(csv_file))
        
        # Initialize summary
        summary = {
            "Data/Model": model_name,
            "Mesh": 0,
            "IFC": 0,
            "Primitives": 0,
            "total_elements": 0,
            "milliseconds": 0,
            "minutes": 0,
            "element_per_min": 0
        }
        
        # Check what data is available
        has_create_data = not df[df['Operation Name'] == CREATE_TIME_OPERATION].empty
        has_read_data = not df[df['Operation Name'] == READ_TIME_OPERATION].empty
        
        # Prefer create data over read data
        if has_create_data:
            operation_map = CREATE_OPERATIONS
            time_operation = CREATE_TIME_OPERATION
        elif has_read_data:
            operation_map = READ_OPERATIONS
            time_operation = READ_TIME_OPERATION
        else:
            return summary  # No timing data available
        
        # Process operations and count elements
        for _, row in df.iterrows():
            matched_op = find_matching_operation(row['Operation Name'], operation_map)
            if matched_op:
                display_name = operation_map[matched_op]
                summary[display_name] += row['#Events']
        
        # Calculate total elements
        summary["total_elements"] = summary["Mesh"] + summary["IFC"] + summary["Primitives"]
        
        # Process timing data
        time_rows = df[df['Operation Name'] == time_operation]
        if not time_rows.empty:
            timing_ms = time_rows["Operation Time in Milliseconds"].sum()
            summary["milliseconds"] = int(timing_ms)
            summary["minutes"] = round(timing_ms / 60000, 2)
            summary["element_per_min"] = calculate_elements_per_minute(
                summary["total_elements"], summary["minutes"]
            )
        
        return summary
        
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")
        return None

def process_tekla_csv_files(file_paths, output_callback=None, status_callback=None):
    """
    Process Tekla CSV files and return summary DataFrame.
    
    Args:
        file_paths: List of CSV file paths to process
        output_callback: Optional function for logging messages
        status_callback: Optional function for status updates
        
    Returns:
        pandas.DataFrame: Summary of processed data
    """
    # Filter valid CSV files
    csv_files = [f for f in file_paths if f.endswith(".csv") and os.path.isfile(f)]
    
    if not csv_files:
        if output_callback:
            output_callback("No valid CSV files found.")
        return None
    
    # Process each file
    results = []
    for csv_file in csv_files:
        result = process_single_file(csv_file)
        if result:
            results.append(result)
    
    if not results:
        if output_callback:
            output_callback("No valid data found in CSV files.")
        return None
    
    # Create summary DataFrame
    summary_df = pd.DataFrame(results)
    
    # Ensure proper data types
    numeric_columns = ['Mesh', 'IFC', 'Primitives', 'total_elements', 'milliseconds']
    for col in numeric_columns:
        if col in summary_df.columns:
            summary_df[col] = summary_df[col].fillna(0).astype(int)
    
    float_columns = ['minutes', 'element_per_min']
    for col in float_columns:
        if col in summary_df.columns:
            summary_df[col] = summary_df[col].fillna(0.0)
    
    if status_callback:
        status_callback("Processing complete")
    
    return summary_df 