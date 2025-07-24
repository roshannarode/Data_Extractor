import pandas as pd
import os

# Import specialized processors
from tekla_processor import process_tekla_csv_files
from rhino_processor import process_rhino_files

def resolve_file_paths(entry_value):
    """
    Convert user input into list of CSV file paths.
    
    Args:
        entry_value: Directory path, single file, or semicolon-separated files
        
    Returns:
        list: List of CSV file paths
    """
    if os.path.isdir(entry_value):
        # Directory - get all CSV files
        return [os.path.join(entry_value, f) 
                for f in os.listdir(entry_value) 
                if f.endswith(".csv")]
    elif ";" in entry_value:
        # Multiple files separated by semicolon
        return [f.strip() for f in entry_value.split(";") 
                if os.path.isfile(f.strip())]
    elif os.path.isfile(entry_value):
        # Single file
        return [entry_value]
    return []

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

# Legacy compatibility - re-export main functions
__all__ = [
    'process_tekla_csv_files',
    'process_rhino_files',
    'resolve_file_paths',
    'save_summary_to_csv'
] 