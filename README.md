# Data Extractor Version 2

A modular data extraction application for processing CSV files from different connectors (Tekla, Rhino) and generating summary reports.

## Project Structure

The application has been refactored into multiple files for better organization:

- **`app.py`** - Main entry point to start the application
- **`gui.py`** - GUI components and user interface logic
- **`data_processor.py`** - Data processing logic for different connectors
- **`requirements.txt`** - Python dependencies

## Installation

1. Make sure you have Python 3.6+ installed
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To start the application, run:

```bash
python app.py
```

## Features

- **File Selection**: Choose individual CSV files or an entire folder
- **Multiple Connectors**: Support for Tekla and Rhino data processing
- **Real-time Processing**: Live console output during processing
- **CSV Export**: Save processed summaries as CSV files
- **Modern GUI**: Clean and intuitive user interface

## Supported Operations

### Tekla Connector
- IFC Export operations
- Mesh geometry creation
- Primitive element creation
- Processing time analysis

### Rhino Connector
- Placeholder for future Rhino-specific processing logic

## File Formats

The application processes CSV files with the following expected structure:
- `Operation Name` column
- `#Events` column  
- `Operation Time in Milliseconds` column

## Output

The application generates a summary CSV file (`final_model_summary.csv`) containing:
- Model/Data name
- Operation counts (Mesh, IFC, Primitives)
- Processing time in milliseconds and minutes

## 🚀 Building Executable

To create a standalone executable (.exe) with version info and icon:

### Quick Build (Automated)
```bash
python build_exe.py
```

### Manual Build
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name=DataExtractor --version-file=version_info.txt --icon=icon.ico app.py
```

The executable will be created in the `dist/` folder.

📖 **For detailed build instructions and troubleshooting, see [BUILD_GUIDE.md](BUILD_GUIDE.md)** 