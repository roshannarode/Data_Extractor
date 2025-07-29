import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
from data_processor import (
    process_tekla_csv_files,
    process_rhino_files,
    process_navisworks_files,
    resolve_tekla_file_paths,
    resolve_csv_file_paths,
    save_summary_to_csv
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
        self.create_df = None
        self.load_df = None
        self.root = tk.Tk()
        self.setup_window()
        self.setup_interface()

    def setup_window(self):
        """Configure main window properties"""
        self.root.title("Data Extractor")
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
        
        # Create separate frames for Create and Load tables
        self.create_frame = ttk.LabelFrame(self.table_frame, text="Create Exchange Operations", padding=5)
        self.load_frame = ttk.LabelFrame(self.table_frame, text="Load Exchange Operations", padding=5)
        
        self.create_table = None
        self.load_table = None

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
        connector = self.connector_var.get()
        
        if connector == "Tekla":
            # For Tekla, browse JSON files
            files = filedialog.askopenfilenames(
                title="Select Tekla JSON files",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
        else:
            # For Rhino and Navisworks, browse CSV files
            files = filedialog.askopenfilenames(
                title="Select CSV files", 
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
        
        if files:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, ";".join(files))
        else:
            folder = filedialog.askdirectory()
            if folder:
                self.folder_entry.delete(0, tk.END)
                self.folder_entry.insert(0, folder)

    def display_tables(self, data_dict):
        """Display results in separate tables for Create and Load operations"""
        # Clear existing tables
        if self.create_table:
            self.create_table.destroy()
        if self.load_table:
            self.load_table.destroy()
            
        # Hide frames initially
        self.create_frame.pack_forget()
        self.load_frame.pack_forget()
            
        if data_dict is None:
            return

        tables_displayed = 0

        # Display Create table if data exists
        if 'create' in data_dict and not data_dict['create'].empty:
            self._create_single_table(data_dict['create'], self.create_frame, 'create')
            self.create_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
            tables_displayed += 1

        # Display Load table if data exists  
        if 'load' in data_dict and not data_dict['load'].empty:
            self._create_single_table(data_dict['load'], self.load_frame, 'load')
            self.load_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
            tables_displayed += 1

    def _create_single_table(self, df, parent_frame, table_type):
        """Create a single table in the specified frame"""
        columns = list(df.columns)
        
        if table_type == 'create':
            self.create_table = ttk.Treeview(parent_frame, columns=columns, show="headings", height=6)
            table = self.create_table
        else:
            self.load_table = ttk.Treeview(parent_frame, columns=columns, show="headings", height=6)
            table = self.load_table
        
        # Configure columns
        for col in columns:
            table.heading(col, text=col)
            if col == "Data/Model":
                table.column(col, anchor=tk.W, width=150, stretch=True)
            else:
                table.column(col, anchor=tk.CENTER, width=120, stretch=True)

        # Add data rows
        for _, row in df.iterrows():
            table.insert("", tk.END, values=list(row))
            
        # Add scrollbar
        scrollbar = ttk.Scrollbar(parent_frame, orient=tk.VERTICAL, command=table.yview)
        table.configure(yscrollcommand=scrollbar.set)
        
        table.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def run_processing(self):
        """Execute data processing"""
        # Reset state
        self.save_button.config(state="disabled")
        self.summary_df = None
        self.create_df = None
        self.load_df = None
        if self.create_table:
            self.create_table.destroy()
            self.create_table = None
        if self.load_table:
            self.load_table.destroy()
            self.load_table = None

        # Get user inputs
        entry_value = self.folder_entry.get().strip()
        connector = self.connector_var.get()

        # Validate inputs
        if not entry_value:
            messagebox.showerror("Error", "Please select files or folder first!")
            return

        # Resolve file paths based on connector type
        if connector == "Tekla":
            file_paths = resolve_tekla_file_paths(entry_value)
            file_type_msg = "JSON files"
        else:
            file_paths = resolve_csv_file_paths(entry_value)
            file_type_msg = "CSV files"
            
        if not file_paths:
            messagebox.showerror("Error", f"No {file_type_msg} found: {entry_value}")
            return

        # Process based on connector type
        try:
            if connector == "Tekla":
                result = process_tekla_csv_files(file_paths)
                if result and isinstance(result, dict):
                    self.create_df = result.get('create')
                    self.load_df = result.get('load')
                    self.summary_df = result  # Keep for compatibility
                else:
                    self.summary_df = result
                self._handle_processing_result(connector)
            elif connector == "Rhino":
                self.summary_df = process_rhino_files(file_paths)
                self._handle_processing_result(connector)
            elif connector == "Navisworks":
                self.summary_df = process_navisworks_files(file_paths)
                self._handle_processing_result(connector)
            else:
                messagebox.showwarning("Warning", "Please select a valid connector.")
        except Exception as e:
            messagebox.showerror("Error", f"Processing failed:\n{str(e)}")

    def _handle_processing_result(self, connector=None):
        """Handle the result of data processing"""
        if connector == "Tekla":
            # Handle Tekla's new format with separate Create/Load tables
            if isinstance(self.summary_df, dict) and (self.create_df is not None or self.load_df is not None):
                self.save_button.config(state="normal")
                self.display_tables(self.summary_df)
            else:
                file_requirements = ("Check your JSON files contain:\n"
                                   "- OperationType: 'CreateExchange' or 'LoadExchange'\n"
                                   "- PerformanceMetrics array\n"
                                   "- OperationName, ElapsedMilliseconds, Events fields\n"
                                   "- Context.Exchanges with ElementCounts")
                messagebox.showwarning("No Data", f"No valid data found. {file_requirements}")
        else:
            # Handle other connectors (Rhino, Navisworks) with single table
            if self.summary_df is not None and not self.summary_df.empty:
                self.save_button.config(state="normal")
                self.display_tables({'create': self.summary_df})  # Display as single table
            else:
                file_requirements = ("Check your CSV files contain:\n"
                                   "- Operation Name\n- #Events\n- Operation Time in Milliseconds")
                messagebox.showwarning("No Data", f"No valid data found. {file_requirements}")

    def save_csv(self):
        """Save results to CSV file(s)"""
        entry_value = self.folder_entry.get().strip()
        connector = self.connector_var.get()
        
        # Get file paths using appropriate resolver
        if connector == "Tekla":
            file_paths = resolve_tekla_file_paths(entry_value)
        else:
            file_paths = resolve_csv_file_paths(entry_value)
            
        if not file_paths:
            messagebox.showerror("Error", "Invalid file selection!")
            return

        if connector == "Tekla" and isinstance(self.summary_df, dict):
            # Save separate files for Create and Load operations
            saved_files = []
            
            if self.create_df is not None and not self.create_df.empty:
                create_output = self._save_df_to_csv(self.create_df, file_paths, "create_exchange_summary.csv")
                if create_output:
                    saved_files.append(f"Create: {create_output}")
            
            if self.load_df is not None and not self.load_df.empty:
                load_output = self._save_df_to_csv(self.load_df, file_paths, "load_exchange_summary.csv")
                if load_output:
                    saved_files.append(f"Load: {load_output}")
            
            if saved_files:
                message = "CSV files saved:\n" + "\n".join(saved_files)
                messagebox.showinfo("Success", message)
            else:
                messagebox.showerror("Error", "Failed to save CSV files!")
        else:
            # Handle other connectors or fallback
            if self.summary_df is None or (hasattr(self.summary_df, 'empty') and self.summary_df.empty):
                messagebox.showwarning("No Data", "No summary available to save.")
                return
                
            output_path = save_summary_to_csv(self.summary_df, file_paths)
            if output_path:
                messagebox.showinfo("Success", f"CSV saved to:\n{output_path}")
            else:
                messagebox.showerror("Error", "Failed to save CSV file!")

    def _save_df_to_csv(self, df, file_paths, filename):
        """Helper method to save a DataFrame to CSV"""
        if df is None or df.empty or not file_paths:
            return None

        # Use directory of first file for output location
        folder_path = os.path.dirname(file_paths[0])
        output_path = os.path.join(folder_path, filename)
        
        try:
            df.to_csv(output_path, index=False)
            return output_path
        except Exception as e:
            print(f"Error saving CSV: {e}")
            return None

    def show_about(self):
        """Show application information"""
        about_text = """Data Extractor Version 0.0.3

CSV file processing application for 
Tekla, Rhino, and Navisworks connectors

Author: Roshan Narode"""
        
        about_window = tk.Toplevel(self.root)
        about_window.title("About")
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