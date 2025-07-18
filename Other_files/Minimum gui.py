import toga
from toga.style import Pack
from toga.style.pack import COLUMN

class TestApp(toga.App):
    def startup(self):
        self.main_window = toga.MainWindow(title="My Toga App")

        box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        label = toga.Label("Hello from Toga!", style=Pack(padding=(0, 5)))
        box.add(label)

        self.main_window.content = box
        self.main_window.show()

def main():
    return TestApp("toga-example", "org.beeware.toga.example")

if __name__ == '__main__':
    main().main_loop()
