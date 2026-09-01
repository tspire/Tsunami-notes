"""GUI implementation for Tsunami Notes."""

# pylint: disable=import-error, too-many-instance-attributes, broad-exception-caught

import os
import hashlib
import json
import random
import time
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

# Set CustomTkinter appearance to match the application palette.
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

COLORS = {
    "abyss": "#07111F",
    "surface": "#0B1829",
    "elevated": "#102238",
    "border": "#1D3A55",
    "muted": "#7892A8",
    "text": "#E7F4FA",
    "cyan": "#36D6D0",
    "cyan_hover": "#28B9B5",
    "danger": "#E36B78",
    "danger_hover": "#BE5260",
    "warning": "#E7B96C",
}


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

        self.title("Tsunami Notes")
        self.geometry("1120x760")
        self.minsize(860, 580)

        self.abyssal_black = COLORS["abyss"]
        self.neon_cyan = COLORS["cyan"]
        self.terminal_green = COLORS["text"]
        self.configure(fg_color=self.abyssal_black)

        self.keyboard_sound_enabled = BooleanVar(value=True)

        self._build_ui()
        self._refresh_list()
        self.status_var.set("Vault encrypted · Ready")

    def _build_ui(self):
        """Construct the UI widgets."""
        menubar = Menu(
            self,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            activebackground=COLORS["elevated"],
            activeforeground=COLORS["cyan"],
            borderwidth=0,
        )
        self.config(menu=menubar)

        settings_menu = Menu(
            menubar,
            tearoff=0,
            bg=COLORS["surface"],
            fg=COLORS["text"],
            activebackground=COLORS["elevated"],
            activeforeground=COLORS["cyan"],
            borderwidth=0,
        )
        menubar.add_cascade(label="Vault", menu=settings_menu)
        settings_menu.add_checkbutton(
            label="Keyboard Sounds", variable=self.keyboard_sound_enabled
        )
        settings_menu.add_separator()
        settings_menu.add_command(label="Export", command=self._cmd_export)
        settings_menu.add_command(label="Import", command=self._cmd_import)
        settings_menu.add_command(label="Trash", command=self._cmd_trash)
        settings_menu.add_command(label="Password", command=self._cmd_passwd)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(side="top", fill="x", padx=28, pady=(24, 16))
        brand = ctk.CTkFrame(header, fg_color="transparent")
        brand.pack(side="left")
        ctk.CTkLabel(
            brand,
            text="TSUNAMI",
            font=("DejaVu Sans", 22, "bold"),
            text_color=COLORS["text"],
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text="PRIVATE NOTES  /  AES-256 VAULT",
            font=("DejaVu Sans Mono", 10),
            text_color=COLORS["muted"],
        ).pack(anchor="w", pady=(1, 0))

        toolbar = ctk.CTkFrame(header, fg_color="transparent")
        toolbar.pack(side="right")

        btn_add = ctk.CTkButton(
            toolbar,
            text="+  New note",
            command=self.add_note,
            width=122,
            height=38,
            corner_radius=9,
            font=("DejaVu Sans", 13, "bold"),
            fg_color=COLORS["cyan"],
            text_color=COLORS["abyss"],
            hover_color=COLORS["cyan_hover"],
        )
        btn_add.pack(side="left", padx=(0, 8))

        btn_del = ctk.CTkButton(
            toolbar,
            text="Delete",
            command=self.delete_note,
            width=88,
            height=38,
            corner_radius=9,
            fg_color=COLORS["surface"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["danger"],
            hover_color=COLORS["elevated"],
        )
        btn_del.pack(side="right")

        btn_save = ctk.CTkButton(
            toolbar,
            text="Save",
            command=self.save_current_note,
            width=88,
            height=38,
            corner_radius=9,
            fg_color=COLORS["surface"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            hover_color=COLORS["elevated"],
        )
        btn_save.pack(side="left", padx=(0, 8))

        btn_protect = ctk.CTkButton(
            toolbar,
            text="Protect",
            command=self.protect_current_note,
            width=88,
            height=38,
            corner_radius=9,
            fg_color=COLORS["surface"],
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["warning"],
            hover_color=COLORS["elevated"],
        )
        btn_protect.pack(side="left", padx=(0, 8))

        main_frame = ctk.CTkFrame(
            self,
            fg_color=COLORS["surface"],
            corner_radius=16,
            border_width=1,
            border_color=COLORS["border"],
        )
        main_frame.pack(fill="both", expand=True, padx=28, pady=(0, 14))

        left_frame = ctk.CTkFrame(
            main_frame,
            width=292,
            fg_color=COLORS["surface"],
            corner_radius=16,
        )
        left_frame.pack(side="left", fill="y", padx=(1, 0), pady=1)
        left_frame.pack_propagate(False)

        list_header = ctk.CTkFrame(left_frame, fg_color="transparent")
        list_header.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(
            list_header,
            text="NOTES",
            font=("DejaVu Sans", 12, "bold"),
            text_color=COLORS["muted"],
        ).pack(side="left")
        self.note_count = ctk.CTkLabel(
            list_header,
            text="0",
            width=28,
            height=22,
            corner_radius=11,
            fg_color=COLORS["elevated"],
            text_color=COLORS["cyan"],
            font=("DejaVu Sans Mono", 11, "bold"),
        )
        self.note_count.pack(side="right")

        search = ctk.CTkEntry(
            left_frame,
            placeholder_text="Search notes…",
            height=38,
            corner_radius=9,
            fg_color=COLORS["abyss"],
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["muted"],
        )
        search.pack(fill="x", padx=16, pady=(0, 12))
        search.bind("<Return>", lambda _event: self._cmd_search(search.get()))

        self.listbox = ctk.CTkTextbox(
            left_frame,
            width=260,
            font=("DejaVu Sans", 13),
            fg_color=COLORS["surface"],
            text_color=COLORS["text"],
            border_width=0,
            corner_radius=0,
            spacing1=7,
            spacing3=7,
        )
        self.listbox.pack(fill="both", expand=True, padx=12, pady=(0, 14))
        self.listbox.bind("<Button-1>", self._on_list_click)
        self.listbox.configure(state="disabled")

        right_frame = ctk.CTkFrame(
            main_frame,
            fg_color=COLORS["elevated"],
            corner_radius=15,
        )
        right_frame.pack(side="right", fill="both", expand=True, padx=(0, 1), pady=1)

        editor_header = ctk.CTkFrame(right_frame, fg_color="transparent")
        editor_header.pack(fill="x", padx=30, pady=(26, 8))
        ctk.CTkLabel(
            editor_header,
            text="EDITOR",
            font=("DejaVu Sans", 11, "bold"),
            text_color=COLORS["muted"],
        ).pack(side="left")
        ctk.CTkLabel(
            editor_header,
            text="Ctrl+S to save",
            font=("DejaVu Sans Mono", 10),
            text_color=COLORS["muted"],
        ).pack(side="right")

        self.title_entry = ctk.CTkEntry(
            right_frame,
            placeholder_text="Untitled note",
            height=52,
            font=("DejaVu Sans", 24, "bold"),
            fg_color="transparent",
            text_color=COLORS["text"],
            placeholder_text_color=COLORS["muted"],
            border_width=0,
        )
        self.title_entry.pack(side="top", fill="x", padx=24, pady=(0, 4))

        self.body_text = ctk.CTkTextbox(
            right_frame,
            font=("DejaVu Sans", 15),
            fg_color="transparent",
            text_color=COLORS["text"],
            border_width=0,
            corner_radius=0,
            wrap="word",
            spacing1=3,
            spacing3=3,
        )
        self.body_text.pack(
            side="top", fill="both", expand=True, padx=30, pady=(0, 24)
        )

        self.body_text.bind("<KeyPress>", self._on_key_press)
        self.title_entry.bind("<KeyPress>", self._on_key_press)

        self.status_var = StringVar()
        status_bar = ctk.CTkFrame(self, fg_color="transparent")
        status_bar.pack(side="bottom", fill="x", padx=28, pady=(0, 14))
        ctk.CTkLabel(
            status_bar,
            text="●",
            text_color=COLORS["cyan"],
            font=("DejaVu Sans", 10),
        ).pack(side="left")
        ctk.CTkLabel(
            status_bar,
            textvariable=self.status_var,
            anchor="w",
            text_color=COLORS["muted"],
            font=("DejaVu Sans", 11),
        ).pack(side="left", padx=(7, 0))
        ctk.CTkLabel(
            status_bar,
            text="LOCAL  /  ENCRYPTED",
            text_color=COLORS["muted"],
            font=("DejaVu Sans Mono", 10),
        ).pack(side="right")

        self.overlay = Canvas(self, bg=self.abyssal_black, highlightthickness=0)
        self.overlay.place(x=0, y=0, relwidth=1, relheight=1)
        tk.Misc.lower(self.overlay)

        self.bind("<Control-s>", lambda _event: self.save_current_note())
        self.bind("<Control-n>", lambda _event: self.add_note())

    def _on_key_press(self, event):  # pylint: disable=unused-argument
        if self.keyboard_sound_enabled.get():
            play_sound("keyboard_click")

    def _refresh_list(self):
        notes = self.vault.get("notes", [])
        self.note_count.configure(text=str(len(notes)))
        self.listbox.configure(state="normal")
        self.listbox.delete("1.0", "end")
        if not notes:
            self.listbox.insert("end", "  No notes yet\n  Create one to begin.")
        for i, note in enumerate(notes):
            title = note.get("title", "(untitled)")
            if "password_hash" in note:
                title = f"◆  {title}"
            else:
                title = f"·  {title}"
            self.listbox.insert("end", f"  {title}\n")
        self.listbox.configure(state="disabled")

    def _on_list_click(self, event):
        index = self.listbox.index(f"@{event.x},{event.y}")
        line_num = int(index.split(".")[0]) - 1
        notes = self.vault.get("notes", [])
        if 0 <= line_num < len(notes):
            note = notes[line_num]
            if "password_hash" in note:
                pwd = simpledialog.askstring(
                    "Note Password", "Enter password for this note:", show="*"
                )
                if not pwd:
                    return
                salt, h = note["password_hash"].split(":")
                if hashlib.sha256((salt + pwd).encode()).hexdigest() != h:
                    messagebox.showerror("Error", "Incorrect note password.")
                    return
            self.current_index = line_num
            self.status_var.set(f"Editing · {note.get('title', 'Untitled')}")
            self.title_entry.delete(0, "end")
            self.title_entry.insert(0, note.get("title", ""))
            self.body_text.delete("1.0", "end")
            self.body_text.insert("1.0", note.get("body", ""))

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
            note["title"] = new_title
            note["body"] = new_body
            self._save_vault(anim="save")
            self._refresh_list()

    def protect_current_note(self):
        """Protect or unprotect the current note."""
        if self.current_index is not None:
            note = self.vault["notes"][self.current_index]
            pwd = simpledialog.askstring(
                "Protect Note", "Enter new password (leave empty to remove):", show="*"
            )
            if pwd is not None:
                if pwd == "":
                    note.pop("password_hash", None)
                    messagebox.showinfo("Success", "Note password removed.")
                else:
                    salt = os.urandom(16).hex()
                    h = hashlib.pbkdf2_hmac(
                        "sha256", pwd.encode(), salt.encode(), 100000
                    ).hex()
                    note["password_hash"] = f"{salt}:{h}"
                    messagebox.showinfo("Success", "Note password set.")
                self._save_vault()
                self._refresh_list()
            self.status_var.set("Note saved.")

    def _save_vault(self, anim=None):
        if anim:
            self._play_overlay_animation(anim)
        play_sound("zelda_secret")
        self.save_vault_fn(self.vault_path, self.password, self.vault)

    def _cmd_search(self, query=None):
        if query is None:
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
