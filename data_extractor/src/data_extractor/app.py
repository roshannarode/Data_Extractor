"""
Project Zero
"""
import toga

from data_extractor.hi import build_gui
from data_extractor.tekla_processor import process_tekla_csv_files
import os

summary_df_global = None  # Make sure this is declared at the module level


class Data_extractor(toga.App):
    def startup(self):
        self.main_box, self.ui = build_gui(self)
        self.main_window = toga.MainWindow(title=self.formal_name)
        self.main_window.content = self.main_box
        self.main_window.show()

    async def browse_folder(self, widget):
        # Construct full path to AppData\Roaming
        user_profile = os.getenv('USERPROFILE')  # C:\Users\<YourName>
        appdata_roaming = os.path.join(user_profile, "AppData", "Roaming")

        # Fallback if USERPROFILE isn't set
        if not os.path.isdir(appdata_roaming):
            appdata_roaming = os.path.expanduser("~")

        # Open folder dialog with AppData\Roaming as default
        folder_path = await self.main_window.select_folder_dialog(
            title="Select Folder",
            initial_directory=appdata_roaming
        )

        if folder_path:
            self.ui['folder_input'].value = folder_path

    def run_processing(self, widget):
        self.ui['save_btn'].enabled = False
        self.ui['console'].value = ""
        folder_path = self.ui['folder_input'].value
        connector = self.ui['connector_choice'].value

        if not os.path.isdir(folder_path):
            self.ui['status'].text = "Invalid folder selected!"
            return

        if connector == "Tekla":
            global summary_df_global
            summary_df_global = process_tekla_csv_files(folder_path, self.ui)
        else:
            self.log("🛠️ Rhino processing not implemented.")
            self.ui['status'].text = "Rhino logic placeholder."

    def log(self, msg):
        self.ui['console'].value += msg + "\n"

    def save_csv(self, widget):
        global summary_df_global
        if summary_df_global is None or summary_df_global.empty:
            self.ui['status'].text = "⚠️ No data to save!"
            return

        folder_path = self.ui['folder_input'].value
        output_path = os.path.join(folder_path, "final_model_summary.csv")
        summary_df_global.to_csv(output_path, index=False)
        self.log(f"💾 CSV saved to: {output_path}")
        self.ui['status'].text = "✅ CSV saved!"


def main():
    return Data_extractor("Data Extractor", "org.example.dataextractor")