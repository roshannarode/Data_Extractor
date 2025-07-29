import json
import os
import re

# Operation mappings for different data types - updated for JSON format
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

def extract_model_name_from_json(json_data, fallback_filename):
    """Extract model name from JSON ExchangeName field."""
    try:
        # Try to get ExchangeName from Context.Exchanges
        context = json_data.get("Context", {})
        exchanges = context.get("Exchanges", [])
        
        for exchange in exchanges:
            exchange_info = exchange.get("ExchangeInfo", {})
            exchange_name = exchange_info.get("ExchangeName")
            if exchange_name:
                return exchange_name
        
        # If no ExchangeName found, use filename as fallback
        return os.path.splitext(fallback_filename)[0]
        
    except Exception:
        # If any error occurs, use filename as fallback
        return os.path.splitext(fallback_filename)[0]

def find_matching_operation(operation_name, operation_map):
    """Find which operation type matches the given operation name."""
    for key in operation_map:
        if key in operation_name:
            return key
    return None

def calculate_elements_per_minute(total_elements, time_minutes):
    """Calculate processing rate in elements per minute."""
    return round(total_elements / time_minutes, 2) if time_minutes > 0 else 0

def process_single_file(json_file):
    """Process a single JSON file and return summary data."""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        model_name = extract_model_name_from_json(data, os.path.basename(json_file))
        
        # Check Status field first
        status = data.get("Status", "")
        if status == "CompletedWithErrors":
            # Return error information instead of processing data
            errors = data.get("Errors", [])
            error_summary = []
            
            # Collect error messages
            for error in errors:
                message = error.get("Message", "Unknown error")
                method = error.get("MethodName", "")
                if method:
                    error_summary.append(f"{method}: {message}")
                else:
                    error_summary.append(message)
            
            # If no specific errors in array, show general error
            if not error_summary:
                error_summary.append("Processing completed with errors (no details available)")
            
            return {
                "Data/Model": model_name,
                "Status": "ERROR",
                "Error_Details": "; ".join(error_summary[:3]),  # Limit to first 3 errors to avoid clutter
                "Mesh": 0,
                "IFC": 0,
                "Primitives": 0,
                "total_elements": 0,
                "milliseconds": 0,
                "minutes": 0,
                "element_per_min": 0
            }
        
        # Initialize summary for successful processing
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
        
        # Get performance metrics if available
        performance_metrics = data.get("PerformanceMetrics", [])
        if not performance_metrics:
            return summary  # No performance data available
        
        # Check OperationType to determine which operations to use
        operation_type = data.get("OperationType", "")
        
        if operation_type == "CreateExchange":
            operation_map = CREATE_OPERATIONS
            time_operation = CREATE_TIME_OPERATION
            summary["Operation_Type"] = "Create"
        elif operation_type == "LoadExchange":  # Exact match only, not "LoadLatestExchange"
            operation_map = READ_OPERATIONS
            time_operation = READ_TIME_OPERATION
            summary["Operation_Type"] = "Load"
        else:
            # Skip processing for other operation types (like LoadLatestExchange)
            return None
        
        # Process operations and count elements from performance metrics
        for metric in performance_metrics:
            operation_name = metric.get("OperationName", "")
            events = metric.get("Events", 0)
            
            matched_op = find_matching_operation(operation_name, operation_map)
            if matched_op:
                display_name = operation_map[matched_op]
                summary[display_name] += events
        
        # Get element counts from Context.Exchanges if available
        context = data.get("Context", {})
        exchanges = context.get("Exchanges", [])
        for exchange in exchanges:
            element_counts = exchange.get("ElementCounts", {})
            if element_counts:
                # Map JSON element types to our categories
                summary["IFC"] += element_counts.get("BRep", 0)
                # CurveSet could be considered as primitives
                summary["Primitives"] += element_counts.get("CurveSet", 0)
                # Add other element types if they exist
                total_from_exchange = element_counts.get("TotalElements", 0)
                if total_from_exchange > summary["total_elements"]:
                    summary["total_elements"] = total_from_exchange
        
        # If we didn't get total from exchanges, calculate from individual counts
        if summary["total_elements"] == 0:
            summary["total_elements"] = summary["Mesh"] + summary["IFC"] + summary["Primitives"]
        
        # Process timing data
        for metric in performance_metrics:
            if metric.get("OperationName") == time_operation:
                timing_ms = metric.get("ElapsedMilliseconds", 0)
                summary["milliseconds"] += int(timing_ms)
        
        # Calculate minutes and rate
        if summary["milliseconds"] > 0:
            summary["minutes"] = round(summary["milliseconds"] / 60000, 2)
            summary["element_per_min"] = calculate_elements_per_minute(
                summary["total_elements"], summary["minutes"]
            )
        
        return summary
        
    except Exception as e:
        print(f"Error processing {json_file}: {e}")
        return None

def process_tekla_json_files(file_paths, output_callback=None, status_callback=None):
    """
    Process Tekla JSON files and return summary DataFrames.
    
    Args:
        file_paths: List of JSON file paths to process
        output_callback: Optional function for logging messages
        status_callback: Optional function for status updates
        
    Returns:
        dict: Dictionary with 'create' and 'load' DataFrames, or None if no data
    """
    import pandas as pd
    
    # Filter valid JSON files
    json_files = [f for f in file_paths if f.endswith(".json") and os.path.isfile(f)]
    
    if not json_files:
        if output_callback:
            output_callback("No valid JSON files found.")
        return None
    
    # Process each file
    create_results = []
    load_results = []
    error_results = []
    
    for json_file in json_files:
        result = process_single_file(json_file)
        if result:
            if result.get("Status") == "ERROR":
                # This is an error result - add to error results
                error_result = {k: v for k, v in result.items() if k != "Operation_Type"}
                error_results.append(error_result)
            elif result.get("Operation_Type") == "Create":
                # Remove Operation_Type before adding to results
                create_result = {k: v for k, v in result.items() if k != "Operation_Type"}
                create_results.append(create_result)
            elif result.get("Operation_Type") == "Load":
                # Remove Operation_Type before adding to results
                load_result = {k: v for k, v in result.items() if k != "Operation_Type"}
                load_results.append(load_result)
    
    # Create separate DataFrames
    result_dict = {}
    
    if create_results or error_results:
        # Combine create results with error results
        all_create_results = create_results + error_results
        if all_create_results:
            create_df = pd.DataFrame(all_create_results)
            result_dict['create'] = _format_dataframe(create_df)
    
    if load_results:
        load_df = pd.DataFrame(load_results)
        result_dict['load'] = _format_dataframe(load_df)
    
    # If we only have errors and no valid data, still return them
    if not result_dict and error_results:
        error_df = pd.DataFrame(error_results)
        result_dict['create'] = _format_dataframe(error_df)
    
    if not result_dict:
        if output_callback:
            output_callback("No valid data found in JSON files with CreateExchange or LoadExchange operation types.")
        return None
    
    if status_callback:
        status_callback("Processing complete")
    
    return result_dict

def _format_dataframe(df):
    """Helper function to format DataFrame with proper data types."""
    import pandas as pd
    
    # Ensure proper data types
    numeric_columns = ['Mesh', 'IFC', 'Primitives', 'total_elements', 'milliseconds']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)
    
    float_columns = ['minutes', 'element_per_min']
    for col in float_columns:
        if col in df.columns:
            df[col] = df[col].fillna(0.0)
    
    # Ensure string columns are properly formatted
    string_columns = ['Data/Model', 'Status', 'Error_Details']
    for col in string_columns:
        if col in df.columns:
            df[col] = df[col].fillna("")
    
    return df

# Keep backward compatibility with the old function name
def process_tekla_csv_files(file_paths, output_callback=None, status_callback=None):
    """Legacy function - redirects to JSON processing"""
    return process_tekla_json_files(file_paths, output_callback, status_callback) 