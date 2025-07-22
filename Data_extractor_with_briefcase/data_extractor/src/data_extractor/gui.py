import toga
from toga.style import Pack
from toga.style.pack import ROW, COLUMN

def build_gui(app):
    ui = {}

    main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

    folder_row = toga.Box(style=Pack(direction=ROW, padding=5))
    ui['folder_input'] = toga.TextInput(readonly=True, style=Pack(flex=1))
    browse_btn = toga.Button("📁 Browse", on_press=app.browse_folder, style=Pack(padding_left=5))
    folder_row.add(toga.Label("Select Folder:", style=Pack(width=120)))
    folder_row.add(ui['folder_input'])
    folder_row.add(browse_btn)
    main_box.add(folder_row)

    connector_row = toga.Box(style=Pack(direction=ROW, padding=5))
    ui['connector_choice'] = toga.Selection(items=["Tekla", "Rhino"], style=Pack(width=200))
    connector_row.add(toga.Label("Connector:", style=Pack(width=120)))
    connector_row.add(ui['connector_choice'])
    main_box.add(connector_row)

    run_btn = toga.Button("▶ Run Summary", on_press=app.run_processing, style=Pack(padding=10))
    main_box.add(run_btn)

    ui['console'] = toga.MultilineTextInput(readonly=True, style=Pack(height=300, padding=5))
    main_box.add(ui['console'])

    ui['save_btn'] = toga.Button("💾 Save CSV", on_press=app.save_csv, enabled=False, style=Pack(padding=5))
    main_box.add(ui['save_btn'])

    ui['status'] = toga.Label("", style=Pack(padding_top=10, color="green"))
    main_box.add(ui['status'])

    return main_box, ui
