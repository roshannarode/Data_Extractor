import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
from data_processor import (
    process_tekla_csv_files,
    process_rhino_placeholder,
    resolve_file_paths,
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
        self.connector_dropdown['values'] = ("Tekla", "Rhino", "DYNAMO")
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

    def display_table(self, df):
        """Display results in table format"""
        # Clear existing table
        if self.table:
            self.table.destroy()
            
        if df is None or df.empty:
            return

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

    def run_processing(self):
        """Execute data processing"""
        # Reset state
        self.save_button.config(state="disabled")
        self.summary_df = None
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
                self.summary_df = process_rhino_placeholder()
                self._handle_processing_result()
            else:
                messagebox.showwarning("Warning", "Please select a valid connector.")
        except Exception as e:
            messagebox.showerror("Error", f"Processing failed:\n{str(e)}")

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

        output_path = save_summary_to_csv(self.summary_df, file_paths)
        if output_path:
            messagebox.showinfo("Success", f"CSV saved to:\n{output_path}")
        else:
            messagebox.showerror("Error", "Failed to save CSV file!")

    def show_about(self):
        """Show application information"""
        about_text = """Data Extractor Version 0.0.3

CSV file processing application for 
Tekla and Rhino connectors

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