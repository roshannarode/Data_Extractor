import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from data_processor import (
    process_tekla_csv_files,
    process_rhino_placeholder,
    resolve_file_paths,
    save_summary_to_csv
)

class DataExtractorGUI:
    def __init__(self):
        self.summary_df = None  # Store result DataFrame for saving
        self.setup_main_window()
        self.setup_widgets()

    def setup_main_window(self):
        """Initialize the main window and styling."""
        self.root = tk.Tk()
        self.root.title("Data Extractor")
        self.root.geometry("1400x900")
        self.root.resizable(True, True)
        self.root.minsize(1200, 800)  # Set minimum size

        # Set window icon
        try:
            if os.path.exists("icon.ico"):
                self.root.iconbitmap("icon.ico")
        except:
            pass  # Continue without icon if there's any issue

        # Set up styling
        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("clam")
        except:
            self.style.theme_use("default")

    def setup_widgets(self):
        """Create and configure all GUI widgets."""
        self.setup_top_frame()
        self.setup_run_button()
        self.setup_console()
        self.setup_bottom_frame()
        self.setup_status_label()

    def setup_top_frame(self):
        """Create the top frame with file selection and connector options."""
        self.top_frame = ttk.Frame(self.root, padding=20)
        self.top_frame.pack(fill=tk.X, padx=10, pady=10)

        # File selection
        ttk.Label(self.top_frame, text="📄 Select CSV Files or Folder:", 
                 font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        self.folder_entry = ttk.Entry(self.top_frame, width=80)
        self.folder_entry.grid(row=0, column=1, padx=5)
        
        ttk.Button(self.top_frame, text="Browse", 
                  command=self.browse_files_or_folder).grid(row=0, column=2, padx=3)

        # Connector selection
        ttk.Label(self.top_frame, text="🔌 Select Connector:", 
                 font=("Segoe UI", 10, "bold")).grid(row=1, column=0, padx=5, pady=10, sticky="w")
        
        self.connector_var = tk.StringVar()
        self.connector_dropdown = ttk.Combobox(self.top_frame, textvariable=self.connector_var, 
                                              state="readonly", width=77)
        self.connector_dropdown['values'] = ("Tekla", "Rhino")
        self.connector_dropdown.current(0)
        self.connector_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="w")

    def setup_run_button(self):
        """Create the main run button."""
        ttk.Button(self.root, text="▶ Run Summary", 
                  command=self.run_processing).pack(pady=10)

    def setup_console(self):
        """Create the console output area."""
        self.output_console = scrolledtext.ScrolledText(self.root, width=140, height=35, 
                                                       font=("Consolas", 11), wrap=tk.NONE)
        self.output_console.pack(padx=15, pady=10, fill=tk.BOTH, expand=True)

    def setup_bottom_frame(self):
        """Create the bottom frame with save button."""
        self.bottom_frame = ttk.Frame(self.root, padding=10)
        self.bottom_frame.pack()

        self.save_button = ttk.Button(self.bottom_frame, text="💾 Save CSV Now", 
                                     command=self.save_summary_csv, state="disabled")
        self.save_button.grid(row=0, column=0, padx=5)

    def setup_status_label(self):
        """Create the status label."""
        self.status_label = ttk.Label(self.root, text="", font=("Segoe UI", 9, "italic"), 
                                     foreground="green")
        self.status_label.pack(pady=5)

    # === Event Handlers ===
    
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

    def run_processing(self):
        """Handle the main processing run."""
        # Disable save button and clear console
        self.save_button.config(state="disabled")
        self.summary_df = None
        
        entry_value = self.folder_entry.get().strip()
        selected_connector = self.connector_var.get()
        file_paths = resolve_file_paths(entry_value)

        if not file_paths:
            messagebox.showerror("Error", "Please select valid CSV files or a folder containing CSV files!")
            return

        self.output_console.delete(1.0, tk.END)

        # Create callback functions for output and status updates
        def output_callback(message):
            self.output_console.insert(tk.END, message)
            self.output_console.update()

        def status_callback(message):
            self.status_label.config(text=message)
            self.status_label.update()

        # Process based on selected connector
        if selected_connector == "Tekla":
            self.summary_df = process_tekla_csv_files(file_paths, output_callback, status_callback)
            if self.summary_df is not None:
                self.save_button.config(state="normal")
        elif selected_connector == "Rhino":
            self.summary_df = process_rhino_placeholder(output_callback, status_callback)
        else:
            messagebox.showwarning("Warning", "Please select a valid connector.")

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
            self.output_console.insert(tk.END, f"\n💾 CSV successfully saved to: {output_csv_path}\n")
            self.output_console.update()
            self.status_label.config(text="✅ CSV saved")
        else:
            messagebox.showerror("Error", "Failed to save CSV file!")

    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()

    def get_root(self):
        """Return the root window (for external access if needed)."""
        return self.root 