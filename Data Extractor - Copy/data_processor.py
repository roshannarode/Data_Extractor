import pandas as pd
import os

# Import specialized processors
from tekla_processor import process_tekla_json_files
from rhino_processor import process_rhino_files
from navisworks_processor import process_navisworks_files

def resolve_file_paths(entry_value, file_extension=None):
    """
    Convert user input into list of file paths.
    
    Args:
        entry_value: Directory path, single file, or semicolon-separated files
        file_extension: Specific file extension to filter for (e.g., '.csv', '.json')
                       If None, looks for both CSV and JSON files
        
    Returns:
        list: List of file paths
    """
    # Determine valid extensions
    if file_extension:
        valid_extensions = [file_extension]
    else:
        valid_extensions = ['.csv', '.json']
    
    if os.path.isdir(entry_value):
        # Directory - get all files with valid extensions
        files = []
        for f in os.listdir(entry_value):
            file_path = os.path.join(entry_value, f)
            if any(f.lower().endswith(ext) for ext in valid_extensions) and os.path.isfile(file_path):
                files.append(file_path)
        return files
    elif ";" in entry_value:
        # Multiple files separated by semicolon
        files = []
        for f in entry_value.split(";"):
            f = f.strip()
            if os.path.isfile(f) and any(f.lower().endswith(ext) for ext in valid_extensions):
                files.append(f)
        return files
    elif os.path.isfile(entry_value):
        # Single file - check if it has valid extension
        if any(entry_value.lower().endswith(ext) for ext in valid_extensions):
            return [entry_value]
    return []

def resolve_tekla_file_paths(entry_value):
    """
    Resolve file paths specifically for Tekla (JSON files).
    
    Args:
        entry_value: Directory path, single file, or semicolon-separated files
        
    Returns:
        list: List of JSON file paths
    """
    return resolve_file_paths(entry_value, '.json')

def resolve_csv_file_paths(entry_value):
    """
    Resolve file paths specifically for CSV files (Rhino, Navisworks).
    
    Args:
        entry_value: Directory path, single file, or semicolon-separated files
        
    Returns:
        list: List of CSV file paths
    """
    return resolve_file_paths(entry_value, '.csv')

def save_summary_to_csv(summary_df, file_paths):
    """
    Save summary DataFrame to CSV file.
    
    Args:
        summary_df: DataFrame to save
        file_paths: List of file paths to determine output location
        
    Returns:
        str: Path where CSV was saved, or None if failed
    """
    if summary_df is None or summary_df.empty or not file_paths:
        return None

    # Use directory of first file for output location
    folder_path = os.path.dirname(file_paths[0])
    output_path = os.path.join(folder_path, "final_model_summary.csv")
    
    try:
        summary_df.to_csv(output_path, index=False)
        return output_path
    except Exception as e:
        print(f"Error saving CSV: {e}")
        return None

# Updated function to use new JSON processor for Tekla
def process_tekla_csv_files(file_paths, output_callback=None, status_callback=None):
    """
    Process Tekla files (now JSON format).
    Legacy function name maintained for compatibility.
    Returns dict with 'create' and 'load' DataFrames or None.
    """
    return process_tekla_json_files(file_paths, output_callback, status_callback)

# Legacy compatibility - re-export main functions
__all__ = [
    'process_tekla_csv_files',
    'process_tekla_json_files',
    'process_rhino_files',
    'process_navisworks_files',
    'resolve_file_paths',
    'resolve_tekla_file_paths',
    'resolve_csv_file_paths',
    'save_summary_to_csv'
] 