import pandas as pd
import os
import re

# Operation mappings for Navisworks - focusing on specific data type counters
CREATE_OPERATIONS = {
    "ExportMeshCount": "Mesh_Export",  # Export mesh counter
    "ExportLineCount": "Line_Export",  # Export line counter for Primitive
    "ExportPointCount": "Point_Export"  # Export point counter for Primitive
}

READ_OPERATIONS = {
    "ReadBrepCount": "Brep_Read",  # Read Brep counter
    "ReadMeshCount": "Mesh_Read",  # Read mesh counter
    "ReadPrimitiveCount": "Primitive_Read"  # Read primitive counter
}

# Time operation names for Navisworks
CREATE_TIME_OPERATION = "UpdateExchangeAsync:TotalTimeToCreateExchange"
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
    """Process a single CSV file and return separate export and read data."""
    try:
        df = pd.read_csv(csv_file)
        model_name = extract_model_name(os.path.basename(csv_file))
        
        # Initialize export summary (Create operations)
        export_summary = {
            "Data/Model": model_name,
            "Mesh_Export": 0,  # ExportMeshCount Counter for Mesh
            "Line_Export": 0,  # ExportLineCount Counter for Primitive
            "Point_Export": 0,  # ExportPointCount Counter for Primitive
            "total_elements": 0,
            "milliseconds": 0,
            "minutes": 0,
            "element_per_min": 0
        }
        
        # Initialize read summary (Read operations)
        read_summary = {
            "Data/Model": model_name,
            "Brep_Read": 0,  # ReadBrepCount Counter for Brep
            "Mesh_Read": 0,  # ReadMeshCount Counter for Mesh
            "Primitive_Read": 0,  # ReadPrimitiveCount Counter for primitive
            "total_elements": 0,
            "milliseconds": 0,
            "minutes": 0,
            "element_per_min": 0
        }
        
        # Check what timing data is available
        has_create_data = not df[df['Operation Name'] == CREATE_TIME_OPERATION].empty
        has_read_data = not df[df['Operation Name'] == READ_TIME_OPERATION].empty
        
        # Process operations and count elements separately for export and read
        for _, row in df.iterrows():
            operation_name = row['Operation Name']
            events_count = row['#Events']
            
            # Debug: Print operation names found
            print(f"Processing operation: '{operation_name}' with {events_count} events")
            
            # Check for specific export operations (Create operations)
            export_matched_op = find_matching_operation(operation_name, CREATE_OPERATIONS)
            if export_matched_op:
                display_name = CREATE_OPERATIONS[export_matched_op]
                export_summary[display_name] += events_count
                print(f"  -> Matched CREATE operation: {export_matched_op} -> {display_name}")
                
            # Check for specific read operations
            read_matched_op = find_matching_operation(operation_name, READ_OPERATIONS)
            if read_matched_op:
                display_name = READ_OPERATIONS[read_matched_op]
                read_summary[display_name] += events_count
                print(f"  -> Matched READ operation: {read_matched_op} -> {display_name}")
            
            # If no matches found, report it
            if not export_matched_op and not read_matched_op:
                print(f"  -> NO MATCH found for operation: '{operation_name}'")
        
        # Calculate total elements for export data
        export_summary["total_elements"] = export_summary["Mesh_Export"] + export_summary["Line_Export"] + export_summary["Point_Export"]
        
        # Calculate total elements for read data
        read_summary["total_elements"] = read_summary["Brep_Read"] + read_summary["Mesh_Read"] + read_summary["Primitive_Read"]
        
        # Process timing data for Create operations
        if has_create_data:
            time_rows = df[df['Operation Name'] == CREATE_TIME_OPERATION]
            if not time_rows.empty:
                timing_ms = time_rows["Operation Time in Milliseconds"].sum()
                export_summary["milliseconds"] = int(timing_ms)
                export_summary["minutes"] = round(timing_ms / 60000, 2)
                export_summary["element_per_min"] = calculate_elements_per_minute(
                    export_summary["total_elements"], export_summary["minutes"]
                )
        
        # Process timing data for read operations
        if has_read_data:
            time_rows = df[df['Operation Name'] == READ_TIME_OPERATION]
            if not time_rows.empty:
                timing_ms = time_rows["Operation Time in Milliseconds"].sum()
                read_summary["milliseconds"] = int(timing_ms)
                read_summary["minutes"] = round(timing_ms / 60000, 2)
                read_summary["element_per_min"] = calculate_elements_per_minute(
                    read_summary["total_elements"], read_summary["minutes"]
                )
        
        # Only return summaries that have actual data
        final_export_summary = None
        final_read_summary = None
        
        # Check if create summary has meaningful data (non-zero counts)
        if (export_summary["Mesh_Export"] > 0 or 
            export_summary["Line_Export"] > 0 or 
            export_summary["Point_Export"] > 0):
            final_export_summary = export_summary
            print(f"Found create data: Mesh={export_summary['Mesh_Export']}, Line={export_summary['Line_Export']}, Point={export_summary['Point_Export']}")
        
        # Check if read summary has meaningful data (non-zero counts)
        if (read_summary["Brep_Read"] > 0 or 
            read_summary["Mesh_Read"] > 0 or 
            read_summary["Primitive_Read"] > 0):
            final_read_summary = read_summary
            print(f"Found read data: Brep={read_summary['Brep_Read']}, Mesh={read_summary['Mesh_Read']}, Primitive={read_summary['Primitive_Read']}")
        
        return final_export_summary, final_read_summary
        
    except Exception as e:
        print(f"Error processing {csv_file}: {e}")
        return None, None

def process_navisworks_files(file_paths, output_callback=None, status_callback=None):
    """
    Process Navisworks CSV files and return separate summary DataFrames for export and read operations.
    
    Args:
        file_paths: List of CSV file paths to process
        output_callback: Optional function for logging messages
        status_callback: Optional function for status updates
        
    Returns:
        tuple: (export_df, read_df) - Two separate DataFrames for export and read operations
    """
    # Filter valid CSV files
    csv_files = [f for f in file_paths if f.endswith(".csv") and os.path.isfile(f)]
    
    if not csv_files:
        if output_callback:
            output_callback("No valid CSV files found.")
        return None, None
    
    # Process each file
    export_results = []
    read_results = []
    
    for csv_file in csv_files:
        if output_callback:
            output_callback(f"Processing: {os.path.basename(csv_file)}")
        
        export_result, read_result = process_single_file(csv_file)
        if export_result:
            export_results.append(export_result)
        if read_result:
            read_results.append(read_result)
    
    # Create separate DataFrames for export and read operations
    export_df = None
    read_df = None
    
    if export_results:
        export_df = pd.DataFrame(export_results)
        
        # Ensure proper data types for export columns
        export_numeric_columns = [
            'Mesh_Export', 'Line_Export', 'Point_Export',  # Export counters
            'total_elements', 'milliseconds'    # General counters
        ]
        for col in export_numeric_columns:
            if col in export_df.columns:
                export_df[col] = export_df[col].fillna(0).astype(int)
        
        float_columns = ['minutes', 'element_per_min']
        for col in float_columns:
            if col in export_df.columns:
                export_df[col] = export_df[col].fillna(0.0)
    
    if read_results:
        read_df = pd.DataFrame(read_results)
        
        # Ensure proper data types for read columns
        read_numeric_columns = [
            'Brep_Read', 'Mesh_Read', 'Primitive_Read',    # Read counters
            'total_elements', 'milliseconds'    # General counters
        ]
        for col in read_numeric_columns:
            if col in read_df.columns:
                read_df[col] = read_df[col].fillna(0).astype(int)
        
        float_columns = ['minutes', 'element_per_min']
        for col in float_columns:
            if col in read_df.columns:
                read_df[col] = read_df[col].fillna(0.0)
    
    if status_callback:
        status_callback("Navisworks processing complete")
    
    if output_callback:
        export_count = len(export_results) if export_results else 0
        read_count = len(read_results) if read_results else 0
        output_callback(f"Successfully processed {len(csv_files)} files")
        output_callback(f"Export data tables: {export_count}")
        output_callback(f"Read data tables: {read_count}")
        output_callback("\nExport Data Counters:")
        output_callback("- ExportMeshCount Counter for Mesh")
        output_callback("- ExportLineCount Counter for Primitive")
        output_callback("- ExportPointCount Counter for Primitive")
        output_callback("\nRead Data Counters:")
        output_callback("- ReadBrepCount Counter for Brep")
        output_callback("- ReadMeshCount Counter for Mesh")
        output_callback("- ReadPrimitiveCount Counter for primitive")
    
    return export_df, read_df 