import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
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
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class DataExtractorGUI:
    def __init__(self):
        self.summary_df = None  # Store result DataFrame for saving
        self.setup_main_window()
        self.setup_menu_bar()
        self.setup_widgets()

    def setup_main_window(self):
        """Initialize the main window and styling."""
        self.root = tk.Tk()
        self.root.title("Data Extractor")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        self.root.minsize(800, 600)

        # Set window icon
        try:
            icon_path = get_resource_path("icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            pass  # Continue without icon if there's any issue
        
        # Force window to appear on top and in center
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(lambda: self.root.attributes('-topmost', False))
        
        # Center the window on screen
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

        # Configure style
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("vista")  # Windows-like theme
        except:
            try:
                self.style.theme_use("clam")
            except:
                self.style.theme_use("default")

    def setup_menu_bar(self):
        """Create the menu bar."""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)

        # File menu
        self.file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Open Folder...", command=self.browse_files_or_folder)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)

        # Help menu
        self.help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=self.help_menu)
        self.help_menu.add_command(label="About", command=self.show_about)

    def setup_widgets(self):
        """Create and configure all GUI widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Select Folder section
        folder_frame = ttk.Frame(main_frame)
        folder_frame.pack(fill=tk.X, pady=(5, 10))

        ttk.Label(folder_frame, text="Select Folder:").pack(side=tk.LEFT, padx=(0, 10))
        self.folder_entry = ttk.Entry(folder_frame)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.browse_button = ttk.Button(folder_frame, text="Browse", command=self.browse_files_or_folder)
        self.browse_button.pack(side=tk.RIGHT)

        # Connector section
        connector_frame = ttk.Frame(main_frame)
        connector_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(connector_frame, text="Connector:").pack(side=tk.LEFT, padx=(0, 10))
        self.connector_var = tk.StringVar()
        self.connector_dropdown = ttk.Combobox(connector_frame, textvariable=self.connector_var, 
                                              state="readonly", width=20)
        self.connector_dropdown['values'] = ("Tekla", "Rhino" , "DYNAMO")
        self.connector_dropdown.current(0)
        self.connector_dropdown.pack(side=tk.LEFT)

        # Run Summary button
        self.run_button = ttk.Button(main_frame, text="▶ Run Summary", command=self.run_processing)
        self.run_button.pack(fill=tk.X, pady=(0, 10))

        # Table output area (Treeview)
        self.table_frame = ttk.Frame(main_frame)
        self.table_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.table = None  # Will be created after processing

        # Save CSV button
        self.save_button = ttk.Button(main_frame, text="💾 Save CSV", 
                                     command=self.save_summary_csv, state="disabled")
        self.save_button.pack(fill=tk.X)

    def show_about(self):
        """Show about dialog."""
        about_text = """Data Extractor Version 0.0.3

Data Extractor Application for processing 
CSV files from Tekla and Rhino connectors

Author: Roshan Narode
"""
        
        # Create custom about dialog with icon
        about_window = tk.Toplevel(self.root)
        about_window.title("About")
        about_window.geometry("400x300")
        about_window.resizable(False, False)
        
        # Set icon for about dialog
        try:
            icon_path = get_resource_path("icon.ico")
            if os.path.exists(icon_path):
                about_window.iconbitmap(icon_path)
        except:
            pass
        
        # Center the about window
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Add content
        ttk.Label(about_window, text=about_text, justify="center", 
                 font=("Segoe UI", 10)).pack(pady=30)
        
        ttk.Button(about_window, text="OK", 
                  command=about_window.destroy).pack(pady=10)

    def browse_files_or_folder(self):
        """Handle file/folder browsing."""
        # Try to open files first
        file_selected = filedialog.askopenfilenames(filetypes=[("CSV files", "*.csv")])
        if file_selected:
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, ";".join(file_selected))
        else:
            # If no files selected, try folder
            folder_selected = filedialog.askdirectory()
            if folder_selected:
                self.folder_entry.delete(0, tk.END)
                self.folder_entry.insert(0, folder_selected)

    def clear_table(self):
        if self.table is not None:
            self.table.destroy()
            self.table = None

    def display_table(self, df):
        self.clear_table()
        if df is None or df.empty:
            return
        columns = list(df.columns)
        self.table = ttk.Treeview(self.table_frame, columns=columns, show="headings")
        for col in columns:
            self.table.heading(col, text=col)
            self.table.column(col, anchor=tk.CENTER, width=120, stretch=True)
        for _, row in df.iterrows():
            self.table.insert("", tk.END, values=list(row))
        self.table.pack(fill=tk.BOTH, expand=True)
        # Resize columns to fit content
        self.table.update_idletasks()
        for col in columns:
            max_width = max(
                [self.table.bbox(item, column=columns.index(col))[2] if self.table.bbox(item, column=columns.index(col)) else 0 for item in self.table.get_children()] + [len(str(col)) * 10, 120]
            )
            self.table.column(col, width=max_width)
        # Resize the table frame to fit the table
        self.table_frame.update_idletasks()

    def run_processing(self):
        """Handle the main processing run."""
        # Disable save button and clear table
        self.save_button.config(state="disabled")
        self.summary_df = None
        self.clear_table()
        
        # Get input values
        entry_value = self.folder_entry.get().strip()
        selected_connector = self.connector_var.get()
        
        # Check if folder/file path is provided
        if not entry_value:
            messagebox.showerror("Error", "Please select a folder or CSV files first using the Browse button!")
            return
        
        # Resolve file paths
        file_paths = resolve_file_paths(entry_value)
        
        if not file_paths:
            messagebox.showerror("Error", f"No CSV files found in the selected location: {entry_value}")
            return
        
        try:
            # Only process and display the table, no other output
            if selected_connector == "Tekla":
                self.summary_df = process_tekla_csv_files(file_paths)
                
                if self.summary_df is not None and not self.summary_df.empty:
                    self.save_button.config(state="normal")
                    self.display_table(self.summary_df)
                    # Processing complete silently - no popup needed
                else:
                    messagebox.showwarning("No Data", "No valid data found in the CSV files. Please check that your CSV files contain the expected columns:\n- Operation Name\n- #Events\n- Operation Time in Milliseconds")
                    
            elif selected_connector == "Rhino":
                self.summary_df = process_rhino_placeholder()
                
                if self.summary_df is not None and not self.summary_df.empty:
                    self.save_button.config(state="normal")
                    self.display_table(self.summary_df)
                    # Processing complete silently - no popup needed
                else:
                    messagebox.showinfo("Info", "Rhino processing is not yet implemented. This is a placeholder.")
                    
            else:
                messagebox.showwarning("Warning", "Please select a valid connector (Tekla or Rhino).")
                
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during processing:\n{str(e)}")

    def save_summary_csv(self):
        """Handle CSV saving."""
        if self.summary_df is None or self.summary_df.empty:
            messagebox.showwarning("No Data", "No summary available to save.")
            return

        entry_value = self.folder_entry.get().strip()
        file_paths = resolve_file_paths(entry_value)

        if not file_paths:
            messagebox.showerror("Error", "Invalid file or folder selection!")
            return

        output_csv_path = save_summary_to_csv(self.summary_df, file_paths)
        
        if output_csv_path:
            self.write_to_console(f"\n💾 CSV successfully saved to: {output_csv_path}\n")
        else:
            messagebox.showerror("Error", "Failed to save CSV file!")

    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()

    def get_root(self):
        """Return the root window (for external access if needed)."""
        return self.root 