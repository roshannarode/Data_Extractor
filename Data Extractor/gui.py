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
        self.setup_menu_bar()
        self.setup_widgets()

    def setup_main_window(self):
        """Initialize the main window and styling."""
        self.root = tk.Tk()
        self.root.title("Data Extractor")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        self.root.minsize(600, 400)

        # Set window icon
        try:
            if os.path.exists("icon.ico"):
                self.root.iconbitmap("icon.ico")
        except:
            pass  # Continue without icon if there's any issue

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
        self.connector_dropdown['values'] = ("Tekla", "Rhino")
        self.connector_dropdown.current(0)
        self.connector_dropdown.pack(side=tk.LEFT)

        # Run Summary button
        self.run_button = ttk.Button(main_frame, text="▶ Run Summary", command=self.run_processing)
        self.run_button.pack(fill=tk.X, pady=(0, 10))

        # Output console
        self.output_console = scrolledtext.ScrolledText(main_frame, font=("Consolas", 10), 
                                                       wrap=tk.WORD, state=tk.DISABLED)
        self.output_console.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Save CSV button
        self.save_button = ttk.Button(main_frame, text="💾 Save CSV", 
                                     command=self.save_summary_csv, state="disabled")
        self.save_button.pack(fill=tk.X)

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo("About", "CSV Summary App\nVersion 2.0\n\nData Extractor Application\nAuthor: Roshan Narode")

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

    def write_to_console(self, message):
        """Write message to console output."""
        self.output_console.config(state=tk.NORMAL)
        self.output_console.insert(tk.END, message)
        self.output_console.see(tk.END)
        self.output_console.config(state=tk.DISABLED)
        self.output_console.update()

    def clear_console(self):
        """Clear console output."""
        self.output_console.config(state=tk.NORMAL)
        self.output_console.delete(1.0, tk.END)
        self.output_console.config(state=tk.DISABLED)

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

        self.clear_console()

        # Create callback functions for output
        def output_callback(message):
            self.write_to_console(message)

        def status_callback(message):
            self.write_to_console(f"Status: {message}\n")

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
            self.write_to_console(f"\n💾 CSV successfully saved to: {output_csv_path}\n")
        else:
            messagebox.showerror("Error", "Failed to save CSV file!")

    def run(self):
        """Start the GUI main loop."""
        self.root.mainloop()

    def get_root(self):
        """Return the root window (for external access if needed)."""
        return self.root 