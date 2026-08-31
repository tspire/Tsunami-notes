"""GUI implementation for Tsunami Notes."""

# pylint: disable=import-error

import os
import json
import tkinter as tk  # pylint: disable=import-error
from tkinter import (
    ttk,
    messagebox,
    simpledialog,
    filedialog,
)  # pylint: disable=import-error


class TsunamiGUI(tk.Tk):
    """The main application window for Tsunami Notes."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, vault, vault_path, password, save_vault_fn):
        super().__init__()
        self.vault = vault
        self.vault_path = vault_path
        self.password = password
        self.save_vault_fn = save_vault_fn
        self.current_index = None
        self.listbox = None
        self.title_entry = None
        self.body_text = None
        self.status_var = tk.StringVar()

        self.title("Tsunami Notes")
        self.geometry("800x600")

        self._build_ui()
        self._refresh_list()
        self.status_var.set("Ready")

    def _build_ui(self):
        """Construct the UI widgets."""
        # Menu Bar
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="list", command=self._cmd_list)
        settings_menu.add_command(label="add", command=self._cmd_add)
        settings_menu.add_command(label="view", command=self._cmd_view)
        settings_menu.add_command(label="edit", command=self._cmd_edit)
        settings_menu.add_command(label="delete", command=self._cmd_delete)
        settings_menu.add_command(label="search", command=self._cmd_search)
        settings_menu.add_command(label="export", command=self._cmd_export)
        settings_menu.add_command(label="import", command=self._cmd_import)
        settings_menu.add_command(label="trash", command=self._cmd_trash)
        settings_menu.add_command(label="interactive", command=self._cmd_interactive)
        settings_menu.add_command(label="passwd", command=self._cmd_passwd)

        # Toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        btn_add = ttk.Button(toolbar, text="Add Note", command=self.add_note)
        btn_add.pack(side=tk.LEFT, padx=2, pady=2)

        btn_del = ttk.Button(toolbar, text="Delete Note", command=self.delete_note)
        btn_del.pack(side=tk.LEFT, padx=2, pady=2)

        btn_save = ttk.Button(toolbar, text="Save Note", command=self.save_current_note)
        btn_save.pack(side=tk.LEFT, padx=2, pady=2)

        # PanedWindow for main content
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left pane (Listbox with scrollbar)
        left_frame = ttk.Frame(paned)
        paned.add(left_frame, weight=1)

        list_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(
            left_frame, width=30, yscrollcommand=list_scroll.set, font=("Helvetica", 11)
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.config(command=self.listbox.yview)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)

        # Right pane (Editor with scrollbar)
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=3)

        self.title_entry = ttk.Entry(right_frame, font=("Helvetica", 14, "bold"))
        self.title_entry.pack(side=tk.TOP, fill=tk.X, padx=2, pady=(0, 5))

        text_frame = ttk.Frame(right_frame)
        text_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        text_scroll = ttk.Scrollbar(text_frame, orient=tk.VERTICAL)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.body_text = tk.Text(
            text_frame,
            yscrollcommand=text_scroll.set,
            font=("Consolas", 11),
            wrap=tk.WORD,
        )
        self.body_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scroll.config(command=self.body_text.yview)

        # Status Bar
        status_bar = ttk.Label(
            self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def _refresh_list(self):
        """Refresh the list of notes in the Listbox."""
        self.listbox.delete(0, tk.END)
        for i, note in enumerate(self.vault.get("notes", [])):
            self.listbox.insert(tk.END, f"{i+1}. {note.get('title', '(untitled)')}")

    def on_select(self, event):  # pylint: disable=unused-argument
        """Handle listbox selection."""
        selection = self.listbox.curselection()
        if not selection:
            return

        index = selection[0]
        self.current_index = index
        note = self.vault["notes"][index]

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
            last_index = self.listbox.size() - 1
            self.listbox.selection_set(last_index)
            # manually trigger on_select behavior to avoid reliance on event loop
            self.current_index = last_index
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, title)
            self.body_text.delete("1.0", tk.END)
            self.status_var.set("Note added.")

    def delete_note(self):
        """Delete the currently selected note."""
        if self.current_index is not None:
            if messagebox.askyesno(
                "Confirm Delete", "Are you sure you want to delete this note?"
            ):
                notes = self.vault.get("notes", [])
                if 0 <= self.current_index < len(notes):
                    notes.pop(self.current_index)
                self.current_index = None
                self.title_entry.delete(0, tk.END)
                self.body_text.delete("1.0", tk.END)
                self._save_vault()
                self._refresh_list()
                self.status_var.set("Note deleted.")
        else:
            self.status_var.set("Please select a note to delete.")

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
            self.status_var.set("Note saved.")

    def _save_vault(self):
        """Save the vault securely."""
        self.save_vault_fn(self.vault_path, self.password, self.vault)

    def _cmd_list(self):
        self._refresh_list()
        self.status_var.set(f"Loaded {len(self.vault.get('notes', []))} notes.")

    def _cmd_add(self):
        self.add_note()

    def _cmd_view(self):
        idx_str = simpledialog.askstring("View Note", "Enter note index (1-based):")
        if idx_str and idx_str.isdigit():
            idx = int(idx_str) - 1
            notes = self.vault.get("notes", [])
            if 0 <= idx < len(notes):
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(idx)
                self.current_index = idx
                note = notes[idx]
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, note.get("title", ""))
                self.body_text.delete("1.0", tk.END)
                self.body_text.insert("1.0", note.get("body", ""))
            else:
                messagebox.showerror("Error", "Invalid index.")

    def _cmd_edit(self):
        idx_str = simpledialog.askstring(
            "Edit Note", "Enter note index (1-based) to edit:"
        )
        if idx_str and idx_str.isdigit():
            idx = int(idx_str) - 1
            notes = self.vault.get("notes", [])
            if 0 <= idx < len(notes):
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(idx)
                self.current_index = idx
                note = notes[idx]
                self.title_entry.delete(0, tk.END)
                self.title_entry.insert(0, note.get("title", ""))
                self.body_text.delete("1.0", tk.END)
                self.body_text.insert("1.0", note.get("body", ""))
            else:
                messagebox.showerror("Error", "Invalid index.")

    def _cmd_delete(self):
        idx_str = simpledialog.askstring("Delete Note", "Enter note index (1-based):")
        if idx_str and idx_str.isdigit():
            idx = int(idx_str) - 1
            notes = self.vault.get("notes", [])
            if 0 <= idx < len(notes):
                if messagebox.askyesno(
                    "Confirm Delete", "Are you sure you want to delete this note?"
                ):
                    trash = self.vault.setdefault("trash", [])
                    trash.append(notes.pop(idx))
                    self._save_vault()
                    self._refresh_list()
                    self.current_index = None
                    self.title_entry.delete(0, tk.END)
                    self.body_text.delete("1.0", tk.END)
            else:
                messagebox.showerror("Error", "Invalid index.")

    def _cmd_search(self):
        query = simpledialog.askstring("Search", "Enter keyword:")
        if query:
            results = []
            notes = self.vault.get("notes", [])
            for idx, note in enumerate(notes, start=1):
                title = note.get("title", "")
                body = note.get("body", "")
                if query.lower() in title.lower() or query.lower() in body.lower():
                    results.append(f"[{idx}] {title}")
            if results:
                messagebox.showinfo("Search Results", "\n".join(results))
            else:
                messagebox.showinfo("Search Results", "No matches found.")

    def _cmd_export(self):
        path = filedialog.asksaveasfilename(
            title="Export to JSON", defaultextension=".json"
        )
        if path:
            try:
                fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(self.vault, f, indent=2, ensure_ascii=False)
                self.status_var.set(f"Vault exported to {path}.")
            except Exception as e:  # pylint: disable=broad-exception-caught
                messagebox.showerror("Export Error", str(e))

    def _cmd_import(self):
        path = filedialog.askopenfilename(
            title="Import JSON", filetypes=[("JSON Files", "*.json"), ("All", "*.*")]
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                imported_notes = data.get("notes", [])
                if not imported_notes:
                    self.status_var.set("No notes found in the import file.")
                    return
                self.vault.setdefault("notes", []).extend(imported_notes)
                self._save_vault()
                self._refresh_list()
                self.status_var.set(f"Imported {len(imported_notes)} notes.")
            except Exception as e:  # pylint: disable=broad-exception-caught
                messagebox.showerror("Import Error", f"Failed to read {path}: {e}")

    def _cmd_trash(self):
        trash = self.vault.get("trash", [])
        if not trash:
            messagebox.showinfo("Trash", "Trash is empty.")
            return

        msg = (
            f"{len(trash)} items in trash.\n"
            "Enter 'empty' to empty, or index (1-based) to restore:"
        )
        action = simpledialog.askstring("Trash", msg)
        if action == "empty":
            self.vault["trash"] = []
            self._save_vault()
            messagebox.showinfo("Trash", "Trash emptied.")
        elif action and action.isdigit():
            idx = int(action) - 1
            if 0 <= idx < len(trash):
                notes = self.vault.setdefault("notes", [])
                notes.append(trash.pop(idx))
                self._save_vault()
                self._refresh_list()
                messagebox.showinfo("Trash", "Item restored.")
            else:
                messagebox.showerror("Error", "Invalid index.")

    def _cmd_interactive(self):
        messagebox.showinfo(
            "Interactive", "Please run 'tsunami interactive' in your terminal."
        )

    def _cmd_passwd(self):
        new_pwd = simpledialog.askstring(
            "Password", "Enter new master password:", show="*"
        )
        if new_pwd:
            confirm = simpledialog.askstring(
                "Password", "Confirm new master password:", show="*"
            )
            if new_pwd == confirm:
                self.password = new_pwd
                self._save_vault()
                messagebox.showinfo("Password", "Master password changed successfully.")
            else:
                messagebox.showerror("Error", "Passwords do not match.")


def run_gui(vault, vault_path, password, save_vault_fn):
    """Launch the Tkinter GUI."""
    app = TsunamiGUI(vault, vault_path, password, save_vault_fn)
    app.mainloop()
