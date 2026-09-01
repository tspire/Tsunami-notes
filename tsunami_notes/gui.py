"""GUI implementation for Tsunami Notes."""

# pylint: disable=import-error, too-many-instance-attributes, broad-exception-caught

import os
import json
import random
import time
import re
import tkinter as tk
from tkinter import (
    Menu,
    messagebox,
    simpledialog,
    filedialog,
    Canvas,
    BooleanVar,
    StringVar,
)
import customtkinter as ctk

from .audio import play_sound

# Set CustomTkinter appearance to match Cyber-Oceanic
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")


class TsunamiGUI(ctk.CTk):
    """The main application window for Tsunami Notes."""

    def _show_error(self, title, message):
        play_sound("navi_listen")
        messagebox.showerror(title, message)

    def _show_info(self, title, message):
        messagebox.showinfo(title, message)

    def __init__(self, vault, vault_path, password, save_vault_fn):
        super().__init__()
        self.vault = vault
        self.vault_path = vault_path
        self.password = password
        self.save_vault_fn = save_vault_fn
        self.current_index = None

        self.title("Tsunami Notes - Cyber Oceanic Edition")
        self.geometry("900x650")

        # Colors
        self.abyssal_black = "#050a0f"
        self.neon_cyan = "#00ffff"
        self.terminal_green = "#00ff00"
        self.configure(fg_color=self.abyssal_black)

        self.keyboard_sound_enabled = BooleanVar(value=True)
        self.focus_mode_enabled = BooleanVar(value=False)
        self.typing_timer = None
        self.is_typing = False
        self.last_activity = time.time()
        self.filtered_indices = []

        self.bind_all("<Any-KeyPress>", self._reset_timer)
        self.bind_all("<Any-Button>", self._reset_timer)
        self.bind_all("<Motion>", self._reset_timer)
        self.after(10000, self._check_inactivity)

        self._build_ui()
        self._refresh_list()
        self.status_var.set("System Ready.")

    def _reset_timer(self, event=None):  # pylint: disable=unused-argument
        self.last_activity = time.time()

    def _check_inactivity(self):
        if time.time() - getattr(self, "last_activity", time.time()) > 300:
            self.withdraw()
            # pylint: disable=import-outside-toplevel
            from .audio import stop_focus_mode

            stop_focus_mode()
            pwd = simpledialog.askstring(
                "Locked", "Session locked. Enter master password:", show="*"
            )
            if pwd == self.password:
                self.deiconify()
                self.last_activity = time.time()
            else:
                self.destroy()
                return
        self.after(10000, self._check_inactivity)

    def _build_ui(self):  # pylint: disable=too-many-statements
        """Construct the UI widgets."""
        # Menu Bar
        menubar = Menu(self, bg=self.abyssal_black, fg=self.neon_cyan)
        self.config(menu=menubar)

        settings_menu = Menu(
            menubar, tearoff=0, bg=self.abyssal_black, fg=self.terminal_green
        )
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_checkbutton(
            label="Keyboard Sounds", variable=self.keyboard_sound_enabled
        )
        settings_menu.add_checkbutton(
            label="Focus Mode",
            variable=self.focus_mode_enabled,
            command=self._on_focus_mode_toggle,
        )
        settings_menu.add_separator()
        settings_menu.add_command(label="Revisions", command=self._cmd_revisions)
        settings_menu.add_command(label="Export", command=self._cmd_export)
        settings_menu.add_command(label="Import", command=self._cmd_import)
        settings_menu.add_command(label="Trash", command=self._cmd_trash)
        settings_menu.add_command(label="Password", command=self._cmd_passwd)

        # Toolbar
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(side="top", fill="x", padx=10, pady=10)

        btn_add = ctk.CTkButton(
            toolbar,
            text="Add Note",
            command=self.add_note,
            fg_color="#004444",
            text_color=self.neon_cyan,
            hover_color="#008888",
        )
        btn_add.pack(side="left", padx=5)

        btn_del = ctk.CTkButton(
            toolbar,
            text="Delete Note",
            command=self.delete_note,
            fg_color="#440000",
            text_color="red",
            hover_color="#880000",
        )
        btn_del.pack(side="left", padx=5)

        btn_save = ctk.CTkButton(
            toolbar,
            text="Save Note",
            command=self.save_current_note,
            fg_color="#004400",
            text_color=self.terminal_green,
            hover_color="#008800",
        )
        btn_save.pack(side="left", padx=5)

        ttk_label = tk.Label(
            toolbar, text="Search:", bg=self.abyssal_black, fg=self.neon_cyan
        )
        ttk_label.pack(side="left", padx=(15, 2))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._refresh_list())
        search_entry = ctk.CTkEntry(
            toolbar,
            textvariable=self.search_var,
            fg_color="#0a192f",
            text_color=self.terminal_green,
            border_color=self.neon_cyan,
        )
        search_entry.pack(side="left", padx=2, pady=2)

        # Main Content
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Left pane (Listbox)
        left_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="y", padx=(0, 10))

        self.listbox = ctk.CTkTextbox(
            left_frame,
            width=250,
            font=("Consolas", 14),
            fg_color="#0a192f",
            text_color=self.neon_cyan,
            border_color=self.neon_cyan,
            border_width=2,
        )
        self.listbox.pack(side="left", fill="both", expand=True)
        # We will use this as a clickable list by binding tags
        self.listbox.bind("<Button-1>", self._on_list_click)
        self.listbox.configure(state="disabled")

        # Right pane (Editor)
        right_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        right_frame.pack(side="right", fill="both", expand=True)

        self.title_entry = ctk.CTkEntry(
            right_frame,
            font=("Helvetica", 16, "bold"),
            fg_color="#0a192f",
            text_color=self.terminal_green,
            border_color=self.neon_cyan,
            border_width=2,
        )
        self.title_entry.pack(side="top", fill="x", pady=(0, 10))

        self.body_text = ctk.CTkTextbox(
            right_frame,
            font=("Consolas", 14),
            fg_color="#0a192f",
            text_color=self.terminal_green,
            border_color=self.neon_cyan,
            border_width=2,
        )
        self.body_text.pack(side="top", fill="both", expand=True)

        self.body_text.bind("<KeyPress>", self._on_key_press)
        self.body_text.bind("<KeyRelease>", self._highlight_markdown)
        self.title_entry.bind("<KeyPress>", self._on_key_press)

        self.body_text.tag_configure("bold", font=("Consolas", 14, "bold"))
        self.body_text.tag_configure("italic", font=("Consolas", 14, "italic"))

        # Status Bar
        self.status_var = StringVar()
        status_bar = ctk.CTkLabel(
            self,
            textvariable=self.status_var,
            anchor="w",
            text_color=self.neon_cyan,
            font=("Consolas", 12),
        )
        status_bar.pack(side="bottom", fill="x", padx=10, pady=(0, 5))

        # Canvas for Overlay Animations

        self.overlay = Canvas(self, bg=self.abyssal_black, highlightthickness=0)
        self.overlay.place(x=0, y=0, relwidth=1, relheight=1)
        tk.Misc.lower(self.overlay)  # Hide it initially by pushing it back

    def _on_focus_mode_toggle(self):
        from .audio import stop_focus_mode  # pylint: disable=import-outside-toplevel

        if not self.focus_mode_enabled.get():
            stop_focus_mode()
            self.is_typing = False
        self.last_activity = time.time()
        if self.typing_timer:
            self.after_cancel(self.typing_timer)
            self.typing_timer = None

    def _stop_typing(self):
        from .audio import stop_focus_mode  # pylint: disable=import-outside-toplevel

        self.is_typing = False
        self.last_activity = time.time()
        stop_focus_mode()

    def _on_key_press(self, event):  # pylint: disable=unused-argument
        if self.keyboard_sound_enabled.get() and not self.focus_mode_enabled.get():
            play_sound("keyboard_click")
        elif self.focus_mode_enabled.get():
            if not self.is_typing:
                self.is_typing = True
                play_sound("keyboard_click")  # Should be typing sound

            if self.typing_timer:
                self.after_cancel(self.typing_timer)
            self.typing_timer = self.after(3000, self._stop_typing)

    def _highlight_markdown(self, event=None):  # pylint: disable=unused-argument
        self.body_text.tag_remove("bold", "1.0", "end")
        self.body_text.tag_remove("italic", "1.0", "end")

        content = self.body_text.get("1.0", "end")
        bold_pattern = r"\*\*(.*?)\*\*"
        italic_pattern = r"\*(.*?)\*"

        def apply_tag(pattern, tag_name):
            for match in re.finditer(pattern, content):
                start_idx = match.start()
                end_idx = match.end()
                start_str = f"1.0+{start_idx}c"
                end_str = f"1.0+{end_idx}c"
                self.body_text.tag_add(tag_name, start_str, end_str)

        apply_tag(bold_pattern, "bold")
        apply_tag(italic_pattern, "italic")

    def _refresh_list(self):
        self.listbox.configure(state="normal")
        self.listbox.delete("1.0", "end")
        query = self.search_var.get().lower() if hasattr(self, "search_var") else ""
        self.filtered_indices = []
        display_idx = 1
        for i, note in enumerate(self.vault.get("notes", [])):
            title = note.get("title", "(untitled)")
            body = note.get("body", "")
            if query in title.lower() or query in body.lower():
                self.filtered_indices.append(i)
                self.listbox.insert("end", f"{display_idx}. {title}\n")
                display_idx += 1
        self.listbox.configure(state="disabled")

    def _on_list_click(self, event):
        index = self.listbox.index(f"@{event.x},{event.y}")
        line_num = int(index.split(".")[0]) - 1
        if 0 <= line_num < len(self.filtered_indices):
            actual_idx = self.filtered_indices[line_num]
            self.current_index = actual_idx
            note = self.vault["notes"][actual_idx]
            self.title_entry.delete(0, "end")
            self.title_entry.insert(0, note.get("title", ""))
            self.body_text.delete("1.0", "end")
            self.body_text.insert("1.0", note.get("body", ""))
            self._highlight_markdown()

    def _play_overlay_animation(self, anim_type):
        tk.Misc.lift(self.overlay)
        self.overlay.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()

        if anim_type == "delete":
            # Simple whirlpool-ish particle effect
            particles = []
            for _ in range(100):
                x = random.randint(0, width)
                y = random.randint(0, height)
                p = self.overlay.create_text(
                    x,
                    y,
                    text=random.choice(["~", "@", "O"]),
                    fill=self.neon_cyan,
                    font=("Consolas", 16),
                )
                particles.append((p, x, y))

            for _ in range(20):
                for p, px, py in particles:
                    dx = (width / 2) - px
                    dy = (height / 2) - py
                    self.overlay.move(p, dx * 0.1, dy * 0.1)
                self.update()
                time.sleep(0.02)
        elif anim_type == "save":
            # Matrix rain effect
            columns = width // 15
            drops = [random.randint(0, height) for _ in range(columns)]
            for _ in range(15):
                self.overlay.delete("all")
                for i in range(columns):
                    x = i * 15
                    y = drops[i]
                    self.overlay.create_text(
                        x,
                        y,
                        text=random.choice(
                            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*"
                        ),
                        fill=self.terminal_green,
                        font=("Consolas", 14),
                    )
                    drops[i] = (drops[i] + 20) % height
                self.update()
                time.sleep(0.03)

        self.overlay.delete("all")
        tk.Misc.lower(self.overlay)

    def add_note(self):
        """Prompt and add a new note."""
        title = simpledialog.askstring("New Note", "Enter note title:")
        if title is not None:
            self.vault.setdefault("notes", []).append({"title": title, "body": ""})
            self._save_vault(anim="save")
            self._refresh_list()
            self.current_index = len(self.vault["notes"]) - 1
            self.title_entry.delete(0, "end")
            self.title_entry.insert(0, title)
            self.body_text.delete("1.0", "end")
            self.status_var.set("Note added.")

    def delete_note(self):
        """Delete the currently selected note."""
        if self.current_index is not None:
            if messagebox.askyesno(
                "Confirm Delete", "Are you sure you want to delete this note?"
            ):
                self._play_overlay_animation("delete")
                notes = self.vault.get("notes", [])
                if 0 <= self.current_index < len(notes):
                    trash_item = notes.pop(self.current_index)
                    self.vault.setdefault("trash", []).append(trash_item)
                self.current_index = None
                self.title_entry.delete(0, "end")
                self.body_text.delete("1.0", "end")
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

            # Save revision
            if note.get("title") != new_title or note.get("body") != new_body:
                rev = {
                    "title": note.get("title", ""),
                    "body": note.get("body", ""),
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                }
                note.setdefault("revisions", []).append(rev)

            note["title"] = new_title
            note["body"] = new_body
            self._save_vault(anim="save")
            self._refresh_list()
            self.status_var.set("Note saved.")

    def _save_vault(self, anim=None):
        if anim:
            self._play_overlay_animation(anim)
        play_sound("zelda_secret")
        self.save_vault_fn(self.vault_path, self.password, self.vault)

    def _cmd_revisions(self):
        if self.current_index is None:
            self._show_info("Revisions", "Select a note first.")
            return

        note = self.vault["notes"][self.current_index]
        revisions = note.get("revisions", [])
        if not revisions:
            self._show_info("Revisions", "No revisions found for this note.")
            return

        results = []
        for idx, rev in enumerate(revisions, start=1):
            results.append(f"[{idx}] {rev.get('timestamp', 'Unknown')}")

        rev_idx = simpledialog.askstring(
            "Revisions",
            "Revisions:\n" + "\n".join(results) + "\n\nEnter index to rollback:",
        )
        if rev_idx and rev_idx.isdigit():
            idx = int(rev_idx) - 1
            if 0 <= idx < len(revisions):
                rev = revisions[idx]
                note["title"] = rev.get("title", note["title"])
                note["body"] = rev.get("body", note["body"])
                self._save_vault(anim="save")
                self._refresh_list()

                self.title_entry.delete(0, "end")
                self.title_entry.insert(0, note["title"])
                self.body_text.delete("1.0", "end")
                self.body_text.insert("1.0", note["body"])
                self._highlight_markdown()
                self._show_info("Revisions", "Note rolled back successfully.")
            else:
                self._show_error("Error", "Invalid index.")

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
                self._show_info("Search Results", "\n".join(results))
            else:
                self._show_info("Search Results", "No matches found.")

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
            except Exception as e:
                self._show_error("Export Error", str(e))

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
                self._save_vault(anim="save")
                self._refresh_list()
                self.status_var.set(f"Imported {len(imported_notes)} notes.")
            except Exception as e:
                self._show_error("Import Error", f"Failed to read {path}: {e}")

    def _cmd_trash(self):
        trash = self.vault.get("trash", [])
        if not trash:
            self._show_info("Trash", "Trash is empty.")
            return

        msg = (
            f"{len(trash)} items in trash.\n"
            "Enter 'empty' to empty, or index (1-based) to restore:"
        )
        action = simpledialog.askstring("Trash", msg)
        if action == "empty":
            self.vault["trash"] = []
            self._save_vault()
            self._show_info("Trash", "Trash emptied.")
        elif action and action.isdigit():
            idx = int(action) - 1
            if 0 <= idx < len(trash):
                notes = self.vault.setdefault("notes", [])
                notes.append(trash.pop(idx))
                self._save_vault(anim="save")
                self._refresh_list()
                self._show_info("Trash", "Item restored.")
            else:
                self._show_error("Error", "Invalid index.")

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
                self._save_vault(anim="save")
                self._show_info("Password", "Master password changed successfully.")
            else:
                self._show_error("Error", "Passwords do not match.")


def run_gui(vault, vault_path, password, save_vault_fn):
    """Launch the Tkinter GUI."""
    app = TsunamiGUI(vault, vault_path, password, save_vault_fn)
    app.mainloop()
