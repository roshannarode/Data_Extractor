import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import pandas as pd
from data_processor import (
    process_tekla_csv_files,
    process_rhino_files,
    process_navisworks_files,
    resolve_file_paths,
    save_summary_to_csv,
    save_navisworks_separate_csvs,
    APP_VERSION
)

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class DataExtractorGUI:
    def __init__(self):
        self.summary_df = None
        self.export_df = None  # Store export data separately for Navisworks
        self.read_df = None    # Store read data separately for Navisworks
        self.is_navisworks_dual = False  # Track if we have dual Navisworks tables
        self.root = tk.Tk()
        self.setup_window()
        self.setup_interface()

    def setup_window(self):
        """Configure main window properties"""
        self.root.title(f"Data Extractor v{APP_VERSION}")
        self.root.geometry("1000x600")
        self.root.resizable(True, True)
        self.root.minsize(1000, 600)

        
        # Set icon if available
        self._set_window_icon()
        
        # Center window and apply theme
        self._center_window()
        self._apply_theme()

    def _set_window_icon(self):
        """Set window icon if icon file exists"""
        try:
            icon_path = get_resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass  # Continue without icon

    def _center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _apply_theme(self):
        """Apply visual theme to the application"""
        self.style = ttk.Style(self.root)
        themes = ["vista", "clam", "default"]
        for theme in themes:
            try:
                self.style.theme_use(theme)
                break
            except:
                continue

    def setup_interface(self):
        """Create all GUI components"""
        self._create_menu()
        self._create_main_widgets()

    def _create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Folder...", command=self.browse_files)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def _create_main_widgets(self):
        """Create main application widgets"""
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # File selection section
        self._create_file_section(main_frame)
        
        # Connector selection section
        self._create_connector_section(main_frame)
        
        # Run button
        self.run_button = ttk.Button(main_frame, text="▶ Run Summary", 
                                   command=self.run_processing)
        self.run_button.pack(fill=tk.X, pady=(0, 10))

        # Results table area
        self.table_frame = ttk.Frame(main_frame)
        self.table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.table = None

        # Save button
        self.save_button = ttk.Button(main_frame, text="💾 Save CSV", 
                                    command=self.save_csv, state="disabled")
        self.save_button.pack(fill=tk.X)

    def _create_file_section(self, parent):
        """Create file selection widgets"""
        folder_frame = ttk.Frame(parent)
        folder_frame.pack(fill=tk.X, pady=(5, 10))

        ttk.Label(folder_frame, text="Select Folder:").pack(side=tk.LEFT, padx=(0, 10))
        self.folder_entry = ttk.Entry(folder_frame)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        ttk.Button(folder_frame, text="Browse", 
                  command=self.browse_files).pack(side=tk.RIGHT)

    def _create_connector_section(self, parent):
        """Create connector selection widgets"""
        connector_frame = ttk.Frame(parent)
        connector_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(connector_frame, text="Connector:").pack(side=tk.LEFT, padx=(0, 10))
        self.connector_var = tk.StringVar()
        self.connector_dropdown = ttk.Combobox(connector_frame, 
                                             textvariable=self.connector_var, 
                                             state="readonly", width=20)
        self.connector_dropdown['values'] = ("Tekla", "Rhino", "Navisworks")
        self.connector_dropdown.current(0)
        self.connector_dropdown.pack(side=tk.LEFT)

    def browse_files(self):
        """Handle file/folder browsing"""
        # Try files first, then folder
        files = filedialog.askopenfilenames(filetypes=[("CSV files", "*.csv")])
        if files:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, ";".join(files))
        else:
            folder = filedialog.askdirectory()
            if folder:
                self.folder_entry.delete(0, tk.END)
                self.folder_entry.insert(0, folder)

    def display_table(self, df, title=None):
        """Display results in table format"""
        # Clear existing table
        if self.table:
            self.table.destroy()
            
        if df is None or df.empty:
            return

        # Create new table with optional title
        if title:
            title_label = ttk.Label(self.table_frame, text=title, font=("Segoe UI", 12, "bold"))
            title_label.pack(pady=(0, 5))

        # Create new table
        columns = list(df.columns)
        self.table = ttk.Treeview(self.table_frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            self.table.heading(col, text=col)
            if col == "Data/Model":
                self.table.column(col, anchor=tk.W, width=150, stretch=True)
            else:
                self.table.column(col, anchor=tk.CENTER, width=120, stretch=True)

        # Add data rows
        for _, row in df.iterrows():
            self.table.insert("", tk.END, values=list(row))
            
        self.table.pack(fill=tk.BOTH, expand=True)

    def display_dual_tables(self, export_df, read_df):
        """Display create and read data in separate tables"""
        # Clear existing table
        if self.table:
            self.table.destroy()
            self.table = None
            
        # Clear any existing widgets in table_frame
        for widget in self.table_frame.winfo_children():
            widget.destroy()

        # Create container for both tables
        dual_container = ttk.Frame(self.table_frame)
        dual_container.pack(fill=tk.BOTH, expand=True)
        
        # Create table section
        if export_df is not None and not export_df.empty:
            export_frame = ttk.LabelFrame(dual_container, text="Create Data", padding=5)
            export_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
            
            export_columns = list(export_df.columns)
            export_table = ttk.Treeview(export_frame, columns=export_columns, show="headings", height=8)
            
            # Configure create table columns
            for col in export_columns:
                export_table.heading(col, text=col)
                if col == "Data/Model":
                    export_table.column(col, anchor=tk.W, width=150, stretch=True)
                else:
                    export_table.column(col, anchor=tk.CENTER, width=100, stretch=True)
            
            # Add create data rows
            for _, row in export_df.iterrows():
                export_table.insert("", tk.END, values=list(row))
                
            export_table.pack(fill=tk.BOTH, expand=True)
            
            # Add scrollbars for create table
            export_scrollbar_y = ttk.Scrollbar(export_frame, orient=tk.VERTICAL, command=export_table.yview)
            export_table.configure(yscrollcommand=export_scrollbar_y.set)
            export_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
            
        # Read table section  
        if read_df is not None and not read_df.empty:
            read_frame = ttk.LabelFrame(dual_container, text="Read Data", padding=5)
            read_frame.pack(fill=tk.BOTH, expand=True)
            
            read_columns = list(read_df.columns)
            read_table = ttk.Treeview(read_frame, columns=read_columns, show="headings", height=8)
            
            # Configure read table columns
            for col in read_columns:
                read_table.heading(col, text=col)
                if col == "Data/Model":
                    read_table.column(col, anchor=tk.W, width=150, stretch=True)
                else:
                    read_table.column(col, anchor=tk.CENTER, width=100, stretch=True)
            
            # Add read data rows
            for _, row in read_df.iterrows():
                read_table.insert("", tk.END, values=list(row))
                
            read_table.pack(fill=tk.BOTH, expand=True)
            
            # Add scrollbars for read table
            read_scrollbar_y = ttk.Scrollbar(read_frame, orient=tk.VERTICAL, command=read_table.yview)
            read_table.configure(yscrollcommand=read_scrollbar_y.set)
            read_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

    def run_processing(self):
        """Execute data processing"""
        # Reset state
        self.save_button.config(state="disabled")
        self.summary_df = None
        self.export_df = None
        self.read_df = None
        self.is_navisworks_dual = False
        if self.table:
            self.table.destroy()
            self.table = None

        # Get user inputs
        entry_value = self.folder_entry.get().strip()
        connector = self.connector_var.get()

        # Validate inputs
        if not entry_value:
            messagebox.showerror("Error", "Please select files or folder first!")
            return

        file_paths = resolve_file_paths(entry_value)
        if not file_paths:
            messagebox.showerror("Error", f"No CSV files found: {entry_value}")
            return

        # Process based on connector type
        try:
            if connector == "Tekla":
                self.summary_df = process_tekla_csv_files(file_paths)
                self._handle_processing_result()
            elif connector == "Rhino":
                self.summary_df = process_rhino_files(file_paths)
                self._handle_processing_result()
            elif connector == "Navisworks":
                # Navisworks returns tuple (export_df, read_df)
                result = process_navisworks_files(file_paths)
                self._handle_navisworks_result(result)
            else:
                messagebox.showwarning("Warning", "Please select a valid connector.")
        except Exception as e:
            messagebox.showerror("Error", f"Processing failed:\n{str(e)}")

    def _handle_navisworks_result(self, result):
        """Handle Navisworks processing result (tuple of export and read DataFrames)"""
        if result is None or (result[0] is None and result[1] is None):
            messagebox.showwarning("No Data", 
                                 "No valid data found. Check your CSV files contain:\n"
                                 "- Operation Name\n- #Events\n- Operation Time in Milliseconds")
            return
            
        export_df, read_df = result
        
        # Check what data is available
        has_export_data = export_df is not None and not export_df.empty
        has_read_data = read_df is not None and not read_df.empty
        
        # Automatically decide which table(s) to show based on available data
        if has_export_data and has_read_data:
            # Both tables have data - show both in separate tables
            self.display_dual_tables(export_df, read_df)
            self.export_df = export_df
            self.read_df = read_df
            self.is_navisworks_dual = True
            
            # For saving purposes, combine the data
            export_copy = export_df.copy()
            read_copy = read_df.copy()
            export_copy['Data_Type'] = 'Export'
            read_copy['Data_Type'] = 'Read'
            self.summary_df = pd.concat([export_copy, read_copy], ignore_index=True)
            
            self.save_button.config(state="normal")
            print(f"Navisworks: Displaying separate tables - Create: {len(export_df)} rows, Read: {len(read_df)} rows")
            
        elif has_export_data:
            # Only create data available - show single create table
            self.export_df = export_df
            self.read_df = None
            self.is_navisworks_dual = True  # Use separate save even for single table
            self.summary_df = export_df
            self.save_button.config(state="normal") 
            self.display_table(export_df, "Create Data")
            
            print(f"Navisworks: Displaying create data - {len(export_df)} rows")
            
        elif has_read_data:
            # Only read data available - show single read table
            self.export_df = None
            self.read_df = read_df
            self.is_navisworks_dual = True  # Use separate save even for single table
            self.summary_df = read_df
            self.save_button.config(state="normal")
            self.display_table(read_df, "Read Data")
            
            print(f"Navisworks: Displaying read data - {len(read_df)} rows")
            
        else:
            # No data in either table
            messagebox.showwarning("No Data", "No export or read data found in the processed files.")

    def _handle_processing_result(self):
        """Handle the result of data processing"""
        if self.summary_df is not None and not self.summary_df.empty:
            self.save_button.config(state="normal")
            self.display_table(self.summary_df)
        else:
            messagebox.showwarning("No Data", 
                                 "No valid data found. Check your CSV files contain:\n"
                                 "- Operation Name\n- #Events\n- Operation Time in Milliseconds")

    def save_csv(self):
        """Save results to CSV file"""
        if self.summary_df is None or self.summary_df.empty:
            messagebox.showwarning("No Data", "No summary available to save.")
            return

        file_paths = resolve_file_paths(self.folder_entry.get().strip())
        if not file_paths:
            messagebox.showerror("Error", "Invalid file selection!")
            return

        if self.is_navisworks_dual:
            # Save Navisworks data to separate CSV files
            export_path, read_path = save_navisworks_separate_csvs(self.export_df, self.read_df, file_paths)
            
            success_messages = []
            error_messages = []
            
            if export_path:
                success_messages.append(f"Create data: {export_path}")
            else:
                error_messages.append("Failed to save Create CSV!")
                
            if read_path:
                success_messages.append(f"Read data: {read_path}")
            else:
                error_messages.append("Failed to save Read CSV!")
            
            if success_messages:
                message = "Navisworks CSV files saved:\n" + "\n".join(success_messages)
                messagebox.showinfo("Success", message)
            
            if error_messages:
                error_message = "\n".join(error_messages)
                messagebox.showerror("Error", error_message)
        else:
            # Standard single CSV save for other connectors
            output_path = save_summary_to_csv(self.summary_df, file_paths)
            if output_path:
                messagebox.showinfo("Success", f"CSV saved to:\n{output_path}")
            else:
                messagebox.showerror("Error", "Failed to save CSV file!")

    def show_about(self):
        """Show application information"""
        about_text = f"""Data Extractor Version {APP_VERSION}

CSV file processing application for 
Tekla, Rhino, and Navisworks connectors

Author: Roshan Narode"""
        
        about_window = tk.Toplevel(self.root)
        about_window.title(f"About Data Extractor {APP_VERSION}")
        about_window.geometry("350x200")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
        
        ttk.Label(about_window, text=about_text, justify="center", 
                 font=("Segoe UI", 10)).pack(pady=30)
        ttk.Button(about_window, text="OK", 
                  command=about_window.destroy).pack(pady=10)

    def run(self):
        """Start the application"""
        self.root.mainloop()

    def get_root(self):
        """Get root window reference"""
        return self.root 