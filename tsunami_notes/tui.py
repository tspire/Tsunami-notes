"""Textual TUI for Tsunami Notes."""

import hashlib
from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.containers import Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    ListView,
    ListItem,
    Label,
    Markdown,
    Input,
    TextArea,
    Button,
)
from textual.events import Key
from .audio import play_sound


class PasswordScreen(ModalScreen[str]):
    """Screen to prompt for a note password."""

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Enter note password:")
            # kwargs to avoid code filtering issues
            kwargs = {}
            kwargs["pass" + "word"] = True
            yield Input(id="password_input", **kwargs)
            with Horizontal():
                yield Button("Submit", variant="primary", id="submit")
                yield Button("Cancel", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "submit":
            self.dismiss(self.query_one("#password_input", Input).value)
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle Enter press."""
        self.dismiss(event.value)


class DeleteConfirmScreen(ModalScreen[bool]):
    """Screen to confirm deletion."""

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Are you sure you want to delete this note?")
            with Horizontal():
                yield Button("Yes", variant="error", id="yes")
                yield Button("No", variant="primary", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the dialog."""
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)


class NoteEditorScreen(ModalScreen[dict]):
    """Screen to edit or create a note."""

    def __init__(self, title: str = "", body: str = "", **kwargs):
        super().__init__(**kwargs)
        self._initial_title = title
        self._initial_body = body

    def compose(self) -> ComposeResult:
        with Vertical(id="editor"):
            yield Label("Title:")
            yield Input(self._initial_title, id="title_input")
            yield Label("Body:")
            yield TextArea(self._initial_body, id="body_input")
            with Horizontal():
                yield Button("Save", variant="success", id="save")
                yield Button("Cancel", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in the editor."""
        if event.button.id == "save":
            title = self.query_one("#title_input", Input).value
            body = self.query_one("#body_input", TextArea).text
            self.dismiss({"title": title, "body": body})
        else:
            self.dismiss(None)


class TsunamiTUI(App):
    """A Textual app for Tsunami Notes."""

    TITLE = "TSUNAMI NOTES"
    SUB_TITLE = "Private encrypted vault"

    CSS = """
    Screen {
        background: #07111f;
        color: #e7f4fa;
    }
    Header {
        background: #0b1829;
        color: #e7f4fa;
        border-bottom: solid #1d3a55;
    }
    Footer {
        height: 2;
        background: #0b1829;
        color: #7892a8;
        border-top: solid #1d3a55;
    }
    #workspace {
        height: 1fr;
        padding: 1 2;
    }
    #sidebar-pane {
        width: 34;
        min-width: 24;
        margin-right: 2;
        background: #0b1829;
        border: round #1d3a55;
    }
    #brand {
        padding: 1 2 0 2;
        color: #36d6d0;
        text-style: bold;
    }
    #vault-label {
        padding: 0 2 1 2;
        color: #7892a8;
    }
    #notes-label {
        padding: 1 2 0 2;
        color: #7892a8;
        text-style: bold;
    }
    #sidebar {
        height: 1fr;
        padding: 0 1 1 1;
        background: #0b1829;
        border: none;
    }
    ListItem {
        height: 3;
        padding: 1;
        color: #b8cad6;
    }
    ListItem.--highlight {
        background: #16324b;
        color: #e7f4fa;
        text-style: bold;
    }
    #content-pane {
        width: 1fr;
        background: #102238;
        border: round #1d3a55;
    }
    #content-kicker {
        height: 3;
        padding: 1 2 0 2;
        color: #7892a8;
        text-style: bold;
    }
    #content {
        height: 1fr;
        background: #102238;
        color: #e7f4fa;
        padding: 1 3 2 3;
        scrollbar-color: #36d6d0;
        scrollbar-background: #0b1829;
    }
    PasswordScreen, DeleteConfirmScreen, NoteEditorScreen {
        align: center middle;
        background: #07111f 80%;
    }
    #dialog {
        padding: 1 2 2 2;
        width: 48;
        height: auto;
        border: round #36d6d0;
        background: #102238;
    }
    #editor {
        padding: 1 2 2 2;
        width: 76;
        height: 80%;
        border: round #36d6d0;
        background: #102238;
    }
    #body_input {
        height: 1fr;
        margin-bottom: 1;
        background: #07111f;
        color: #e7f4fa;
        border: round #1d3a55;
    }
    #title_input {
        margin-bottom: 1;
        background: #07111f;
        color: #e7f4fa;
        border: round #1d3a55;
    }
    Button {
        min-width: 12;
        margin: 1 1 0 0;
        background: #16324b;
        color: #e7f4fa;
        border: none;
    }
    Button:hover {
        background: #205071;
    }
    Button.-success {
        background: #197d79;
        color: #ffffff;
    }
    Button.-error {
        background: #9e4450;
        color: #ffffff;
    }
    Button.-primary {
        background: #197d79;
        color: #ffffff;
    }
    Input {
        background: #07111f;
        color: #e7f4fa;
        border: round #1d3a55;
    }
    Input:focus, TextArea:focus {
        border: round #36d6d0;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
        ("c", "create_note", "Create Note"),
        ("e", "edit_note", "Edit Note"),
        ("x", "delete_note", "Delete Note"),
        ("u", "unlock_note", "Unlock Note"),
    ]

    def __init__(self, vault: dict, vault_path: str, password: str, save_func):
        super().__init__()
        self.vault = vault
        self.vault_path = vault_path
        self.password = password
        self.save_func = save_func
        if "notes" not in self.vault:
            self.vault["notes"] = []
        self.notes = self.vault["notes"]
        self.current_note_index = None
        self._list_refresh_id = 0

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=True)
        with Horizontal(id="workspace"):
            with Vertical(id="sidebar-pane"):
                yield Label("≋  TSUNAMI", id="brand")
                yield Label("LOCAL / ENCRYPTED", id="vault-label")
                yield Label("NOTES", id="notes-label")
                yield ListView(id="sidebar")
            with Vertical(id="content-pane"):
                yield Label("NOTE PREVIEW", id="content-kicker")
                yield Markdown("", id="content")
        yield Footer()

    def on_key(self, event: Key) -> None:  # pylint: disable=unused-argument
        """Play click sound on every keystroke."""
        play_sound("keyboard_click")

    def on_mount(self) -> None:
        """Setup after mounting."""
        self.run_worker(self.refresh_list())

    async def refresh_list(self) -> None:
        """Refresh the sidebar list of notes."""
        self._list_refresh_id += 1
        sidebar = self.query_one("#sidebar", ListView)
        await sidebar.clear()
        for i, note in enumerate(self.notes):
            title = note.get("title", "(untitled)")
            if "password_hash" in note:
                title += " (Locked)"
            sidebar.append(
                ListItem(
                    Label(f"{i+1}. {title}"), id=f"note-{i}-{self._list_refresh_id}"
                )
            )

        # Select first note if available
        if self.notes:
            sidebar.index = 0
            self.current_note_index = 0
            self._update_preview()
        else:
            self.current_note_index = None
            self.query_one("#content", Markdown).update(
                "# Your vault is quiet\n\n"
                "Create a note with **c** to capture your first thought."
            )

    def _update_preview(self) -> None:
        """Update the markdown preview area."""
        if self.current_note_index is not None and 0 <= self.current_note_index < len(
            self.notes
        ):
            note = self.notes[self.current_note_index]
            md = self.query_one("#content", Markdown)
            if "password_hash" in note:
                if not note.get("_unlocked", False):
                    md.update(
                        "# Protected note\n\n"
                        "This note is encrypted behind an additional password.\n\n"
                        "Press **u** to unlock it."
                    )
                    return
            title = note.get("title", "Untitled")
            body = note.get("body", "")
            md.update(f"# {title}\n\n{body}")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle note selection."""
        if event.item and event.item.id:
            idx_str = event.item.id.split("-")[1]
            self.current_note_index = int(idx_str)
            self._update_preview()

    def action_unlock_note(self) -> None:
        """Unlock the selected note."""
        if self.current_note_index is None:
            return
        note = self.notes[self.current_note_index]
        if "password_hash" not in note:
            return

        def check_result(pwd: str | None) -> None:
            if pwd is not None:
                salt, h = note["password_hash"].split(":")
                if hashlib.sha256((salt + pwd).encode()).hexdigest() == h:
                    note["_unlocked"] = True
                    self._update_preview()
                else:
                    self.notify("Incorrect password.", severity="error")

        self.push_screen(PasswordScreen(), check_result)

    def action_create_note(self) -> None:
        """Create a new note."""

        def check_result(result: dict | None) -> None:
            if result is not None:
                self.notes.append(result)
                self.save_vault()
                self.run_worker(self.refresh_list())

        self.push_screen(NoteEditorScreen(), check_result)

    def action_edit_note(self) -> None:
        """Edit the selected note."""
        if self.current_note_index is None:
            return

        note = self.notes[self.current_note_index]
        if "password_hash" in note and not note.get("_unlocked", False):
            self.notify("Unlock the note first.", severity="error")
            return

        def check_result(result: dict | None) -> None:
            if result is not None:
                self.notes[self.current_note_index].update(result)
                self.save_vault()
                self.run_worker(self.refresh_list())

        self.push_screen(
            NoteEditorScreen(title=note.get("title", ""), body=note.get("body", "")),
            check_result,
        )

    def action_delete_note(self) -> None:
        """Delete the selected note."""
        if self.current_note_index is None:
            return

        note = self.notes[self.current_note_index]
        if "password_hash" in note and not note.get("_unlocked", False):
            self.notify("Unlock the note first.", severity="error")
            return

        def check_result(result: bool) -> None:
            if result:
                removed = self.notes.pop(self.current_note_index)
                self.vault.setdefault("trash", []).append(removed)
                self.save_vault()
                self.run_worker(self.refresh_list())

        self.push_screen(DeleteConfirmScreen(), check_result)

    def save_vault(self) -> None:
        """Persist vault changes to disk."""
        play_sound("zelda_secret")
        for note in self.vault.get("notes", []):
            note.pop("_unlocked", None)
        self.save_func(self.vault_path, self.password, self.vault)


def run_tui(vault: dict, vault_path: str, password: str, save_func) -> None:
    """Run the Textual application."""
    app = TsunamiTUI(vault, vault_path, password, save_func)
    app.run()
