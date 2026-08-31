"""GUI implementation for Tsunami Notes."""

# pylint: disable=cyclic-import

import tkinter as tk
from tkinter import messagebox, simpledialog


class TsunamiGUI(tk.Tk):
    """The main application window for Tsunami Notes."""

    def __init__(self, vault, vault_path, password):
        super().__init__()
        self.vault = vault
        self.vault_path = vault_path
        self.password = password
        self.current_index = None
        self.listbox = None
        self.title_entry = None
        self.body_text = None

        self.title("Tsunami Notes")
        self.geometry("800x600")

        self._build_ui()
        self._refresh_list()

    def _build_ui(self):
        """Construct the UI widgets."""
        toolbar = tk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        btn_add = tk.Button(toolbar, text="Add Note", command=self.add_note)
        btn_add.pack(side=tk.LEFT, padx=2, pady=2)

        btn_del = tk.Button(toolbar, text="Delete Note", command=self.delete_note)
        btn_del.pack(side=tk.LEFT, padx=2, pady=2)

        btn_save = tk.Button(toolbar, text="Save Note", command=self.save_current_note)
        btn_save.pack(side=tk.LEFT, padx=2, pady=2)

        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(paned, width=30)
        paned.add(self.listbox)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        right_frame = tk.Frame(paned)
        paned.add(right_frame)

        self.title_entry = tk.Entry(right_frame)
        self.title_entry.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        self.body_text = tk.Text(right_frame)
        self.body_text.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _refresh_list(self):
        """Refresh the list of notes in the Listbox."""
        self.listbox.delete(0, tk.END)
        for note in self.vault.get("notes", []):
            self.listbox.insert(tk.END, note.get("title", "(untitled)"))

    def on_select(self, event):  # pylint: disable=unused-argument
        """Handle listbox selection."""
        selection = self.listbox.curselection()
        if not selection:
            return

        index = selection[0]
        self.current_index = index
        note = self.vault.setdefault("notes", [])[index]

        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, note.get("title", ""))

        self.body_text.delete("1.0", tk.END)
        self.body_text.insert("1.0", note.get("body", ""))

    def add_note(self):
        """Prompt and add a new note."""
        title = simpledialog.askstring("New Note", "Enter note title:")
        if title is not None:
            self.vault.setdefault("notes", []).append({"title": title, "body": ""})
            self._save_vault()
            self._refresh_list()
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(tk.END)
            self.on_select(None)

    def delete_note(self):
        """Delete the currently selected note."""
        if self.current_index is not None:
            if messagebox.askyesno(
                "Confirm Delete", "Are you sure you want to delete this note?"
            ):
                self.vault["notes"].pop(self.current_index)
                self.current_index = None
                self.title_entry.delete(0, tk.END)
                self.body_text.delete("1.0", tk.END)
                self._save_vault()
                self._refresh_list()

    def save_current_note(self):
        """Save changes to the currently edited note."""
        if self.current_index is not None:
            new_title = self.title_entry.get()
            new_body = self.body_text.get("1.0", "end-1c")

            note = self.vault["notes"][self.current_index]
            note["title"] = new_title
            note["body"] = new_body
            self._save_vault()
            self._refresh_list()
            self.listbox.selection_set(self.current_index)

    def _save_vault(self):
        """Save the vault securely."""
        from .notes import save_vault  # pylint: disable=import-outside-toplevel

        save_vault(self.vault_path, self.password, self.vault)


def run_gui(vault, vault_path, password):
    """Launch the Tkinter GUI."""
    app = TsunamiGUI(vault, vault_path, password)
    app.mainloop()
