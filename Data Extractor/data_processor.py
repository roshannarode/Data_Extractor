import pandas as pd
import os

# Import specialized processors
from tekla_processor import process_tekla_csv_files
from rhino_processor import process_rhino_placeholder, process_rhino_files

# === Exchange Read Time Extraction ===
def extract_exchange_read_time_from_csv(csv_file_path):
    """
    Extract TotalExchangeReadTime, create time, and load time data from a single CSV file.
    
    Args:
        csv_file_path: Path to the CSV file
    
    Returns:
        dict: Dictionary containing time data or None if not found
              Format: {
                  'file_name': str,
                  'read_time_ms': int,
                  'read_time_seconds': float,
                  'create_time_ms': int,
                  'create_time_seconds': float,
                  'load_time_ms': int,
                  'load_time_seconds': float,
                  'found': bool
              }
    """
    try:
        if not os.path.isfile(csv_file_path) or not csv_file_path.endswith('.csv'):
            return None
        
        df = pd.read_csv(csv_file_path)
        
        # Look for different time operations
        read_time_row = df[df['Operation Name'] == 'TotalExchangeReadTime']
        create_time_row = df[df['Operation Name'] == 'TotalTimeToCreateExchange']
        load_time_row = df[df['Operation Name'] == 'TotalTimeToLoadExchange']
        
        result = {
            'file_name': os.path.basename(csv_file_path),
            'read_time_ms': 0,
            'read_time_seconds': 0.0,
            'create_time_ms': 0,
            'create_time_seconds': 0.0,
            'load_time_ms': 0,
            'load_time_seconds': 0.0,
            'found': False
        }
        
        found_any = False
        
        # Extract read time
        if not read_time_row.empty:
            read_time_ms = read_time_row['Operation Time in Milliseconds'].iloc[0]
            result.update({
                'read_time_ms': int(read_time_ms),
                'read_time_seconds': round(read_time_ms / 1000, 2)
            })
            found_any = True
        
        # Extract create time
        if not create_time_row.empty:
            create_time_ms = create_time_row['Operation Time in Milliseconds'].iloc[0]
            result.update({
                'create_time_ms': int(create_time_ms),
                'create_time_seconds': round(create_time_ms / 1000, 2)
            })
            found_any = True
        
        # Extract load time
        if not load_time_row.empty:
            load_time_ms = load_time_row['Operation Time in Milliseconds'].iloc[0]
            result.update({
                'load_time_ms': int(load_time_ms),
                'load_time_seconds': round(load_time_ms / 1000, 2)
            })
            found_any = True
        
        result['found'] = found_any
        return result
        
    except Exception as e:
        print(f"Error processing {csv_file_path}: {e}")
        return None

def extract_exchange_read_time_batch(file_paths_or_directory):
    """
    Extract TotalExchangeReadTime data from multiple CSV files or a directory.
    
    Args:
        file_paths_or_directory: List of file paths, single file path, or directory path
    
    Returns:
        list: List of dictionaries with read time data for each file
    """
    # Resolve file paths
    if isinstance(file_paths_or_directory, str):
        file_paths = resolve_file_paths(file_paths_or_directory)
    else:
        file_paths = file_paths_or_directory
    
    results = []
    
    for file_path in file_paths:
        if file_path.endswith('.csv'):
            read_time_data = extract_exchange_read_time_from_csv(file_path)
            if read_time_data:
                results.append(read_time_data)
    
    return results

def create_exchange_read_time_summary(file_paths_or_directory, save_to_csv=False, output_path=None):
    """
    Create a summary DataFrame of exchange read times, create times, and load times from CSV files.
    
    Args:
        file_paths_or_directory: List of file paths, single file path, or directory path
        save_to_csv: Whether to save the summary to a CSV file
        output_path: Custom output path for the CSV file (optional)
    
    Returns:
        pandas.DataFrame: Summary of exchange times
    """
    read_time_data = extract_exchange_read_time_batch(file_paths_or_directory)
    
    if not read_time_data:
        print("No time data found in the provided files.")
        return None
    
    # Create DataFrame
    summary_df = pd.DataFrame(read_time_data)
    
    # Filter to only files where data was found
    summary_df = summary_df[summary_df['found'] == True]
    
    if summary_df.empty:
        print("No time data found in any of the files.")
        return None
    
    # Calculate additional metrics in minutes
    summary_df['read_time_minutes'] = (summary_df['read_time_ms'] / 60000).round(2)
    summary_df['create_time_minutes'] = (summary_df['create_time_ms'] / 60000).round(2)
    summary_df['load_time_minutes'] = (summary_df['load_time_ms'] / 60000).round(2)
    
    # Reorder columns for better readability (like old format)
    summary_df = summary_df[[
        'file_name', 
        'read_time_ms', 'read_time_seconds', 'read_time_minutes',
        'create_time_ms', 'create_time_seconds', 'create_time_minutes',
        'load_time_ms', 'load_time_seconds', 'load_time_minutes'
    ]]
    
    if save_to_csv:
        if output_path is None:
            # Use the directory of the first file
            if isinstance(file_paths_or_directory, str) and os.path.isdir(file_paths_or_directory):
                output_path = os.path.join(file_paths_or_directory, "exchange_time_summary.csv")
            else:
                first_file = file_paths_or_directory[0] if isinstance(file_paths_or_directory, list) else file_paths_or_directory
                output_path = os.path.join(os.path.dirname(first_file), "exchange_time_summary.csv")
        
        summary_df.to_csv(output_path, index=False)
        print(f"Exchange time summary saved to: {output_path}")
    
    return summary_df

# === Shared Utility Functions ===
def resolve_file_paths(entry_value):
    """Resolve file paths from entry value (directory, single file, or multiple files)."""
    if os.path.isdir(entry_value):
        return [os.path.join(entry_value, f) for f in os.listdir(entry_value) if f.endswith(".csv")]
    elif ";" in entry_value:
        return [f for f in entry_value.split(";") if os.path.isfile(f)]
    elif os.path.isfile(entry_value):
        return [entry_value]
    return []

# === CSV Saving ===
def save_summary_to_csv(summary_df, file_paths):
    """
    Save summary DataFrame to CSV file.
    
    Args:
        summary_df: DataFrame to save
        file_paths: List of file paths to determine output location
    
    Returns:
        str: Path where CSV was saved, or None if failed
    """
    if summary_df is None or summary_df.empty:
        return None

    if not file_paths:
        return None

    folder_path = os.path.dirname(file_paths[0])
    output_csv_path = os.path.join(folder_path, "final_model_summary.csv")
    summary_df.to_csv(output_csv_path, index=False)
    
    return output_csv_path

# === Legacy Compatibility Exports ===
# Re-export functions to maintain compatibility with existing code
__all__ = [
    'process_tekla_csv_files',
    'process_rhino_placeholder', 
    'process_rhino_files',
    'resolve_file_paths',
    'save_summary_to_csv',
    'extract_exchange_read_time_from_csv',
    'extract_exchange_read_time_batch',
    'create_exchange_read_time_summary'
] 