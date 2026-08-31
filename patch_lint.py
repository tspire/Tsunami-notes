import re
with open("tsunami_notes/gui.py", "r") as f:
    content = f.read()

# Fix unused event in _on_key_press
content = content.replace("def _on_key_press(self, event):", "def _on_key_press(self, event):  # pylint: disable=unused-argument")

# Fix missing docstrings and line too long
content = content.replace("def add_note(self):", "def add_note(self):\n        \"\"\"Prompt and add a new note.\"\"\"")
content = content.replace("def delete_note(self):", "def delete_note(self):\n        \"\"\"Delete the currently selected note.\"\"\"")
content = content.replace("def save_current_note(self):", "def save_current_note(self):\n        \"\"\"Save changes to the currently edited note.\"\"\"")
content = content.replace("def run_gui(vault, vault_path, password, save_vault_fn):", "def run_gui(vault, vault_path, password, save_vault_fn):\n    \"\"\"Launch the Tkinter GUI.\"\"\"")
content = content.replace(
    "confirm = simpledialog.askstring(\"Password\", \"Confirm new master password:\", show=\"*\")",
    "confirm = simpledialog.askstring(\n                \"Password\", \"Confirm new master password:\", show=\"*\"\n            )"
)

# Move Canvas import
content = content.replace("from tkinter import Menu, messagebox, simpledialog, filedialog", "from tkinter import Menu, messagebox, simpledialog, filedialog, Canvas")
content = content.replace("        from tkinter import Canvas\n        self.overlay = Canvas(", "        self.overlay = Canvas(")

with open("tsunami_notes/gui.py", "w") as f:
    f.write(content)

with open("tsunami_notes/tui.py", "r") as f:
    content = f.read()

content = content.replace("def on_key(self, event: Key) -> None:", "def on_key(self, event: Key) -> None:  # pylint: disable=unused-argument")
with open("tsunami_notes/tui.py", "w") as f:
    f.write(content)
