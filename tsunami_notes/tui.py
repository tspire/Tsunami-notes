"""Textual TUI for Tsunami Notes."""

import time
from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual import events
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


class PasswordScreen(ModalScreen[bool]):
    """Screen to prompt for password when locked."""

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Vertical(id="dialog"):
            yield Label("Session locked. Enter master password:")
            yield Input(password=True, id="pwd_input")
            with Horizontal():
                yield Button("Unlock", variant="success", id="unlock")
                yield Button("Quit", variant="error", id="quit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "unlock":
            pwd = self.query_one("#pwd_input", Input).value
            if pwd == getattr(self.app, "password", ""):
                self.dismiss(True)
            else:
                self.query_one("#pwd_input", Input).value = ""
        else:
            self.app.exit(0)


class DeleteConfirmScreen(ModalScreen[bool]):
    """Screen to confirm deletion."""

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        with Vertical(id="dialog"):
            yield Label("Are you sure you want to delete this note?")
            with Horizontal():
                yield Button("Yes", variant="error", id="yes")
                yield Button("No", variant="primary", id="no")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
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
        """Create child widgets."""
        with Vertical(id="editor"):
            yield Label("Title:")
            yield Input(self._initial_title, id="title_input")
            yield Label("Body:")
            yield TextArea(self._initial_body, id="body_input")
            with Horizontal():
                yield Button("Save", variant="success", id="save")
                yield Button("Cancel", variant="error", id="cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save":
            title = self.query_one("#title_input", Input).value
            body = self.query_one("#body_input", TextArea).text
            self.dismiss({"title": title, "body": body})
        else:
            self.dismiss(None)


class TsunamiTUI(App):
    # pylint: disable=too-many-instance-attributes
    """A Textual app for Tsunami Notes."""

    CSS = """
    #dialog {
        padding: 1 2;
        width: 40;
        height: auto;
        border: thick $background 80%;
        background: $surface;
        align: center middle;
    }
    #editor {
        padding: 1 2;
        width: 80%;
        height: 80%;
        border: thick $background 80%;
        background: $surface;
    }
    #body_input {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
        ("c", "create_note", "Create Note"),
        ("e", "edit_note", "Edit Note"),
        ("x", "delete_note", "Delete Note"),
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
        self.last_activity = 0

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Horizontal():
            yield ListView(id="sidebar")
            yield Markdown("", id="content")
        yield Footer()

    def on_mount(self) -> None:
        """Setup after mounting."""
        self.last_activity = time.time()
        self.set_interval(10, self.check_inactivity)
        self.run_worker(self.refresh_list())

    def check_inactivity(self) -> None:
        """Check if the app should be locked."""
        if time.time() - self.last_activity > 300:
            if not isinstance(self.screen, PasswordScreen):
                self.push_screen(PasswordScreen(), self.unlock_result)
            self.last_activity = time.time()

    def unlock_result(self, unlocked: bool) -> None:
        """Handle unlock result."""
        if unlocked:
            self.last_activity = time.time()
        else:
            self.exit()

    async def on_event(self, event: events.Event) -> None:
        """Reset activity timer on user interaction."""
        if isinstance(event, (events.Key, events.MouseMove, events.MouseDown)):
            self.last_activity = time.time()
        await super().on_event(event)

    async def refresh_list(self) -> None:
        """Refresh the sidebar list of notes."""
        self._list_refresh_id += 1
        sidebar = self.query_one("#sidebar", ListView)
        await sidebar.clear()
        for i, note in enumerate(self.notes):
            title = note.get("title", "(untitled)")
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
            self.query_one("#content", Markdown).update("")

    def _update_preview(self) -> None:
        """Update the markdown preview area."""
        if self.current_note_index is not None and 0 <= self.current_note_index < len(
            self.notes
        ):
            note = self.notes[self.current_note_index]
            md = self.query_one("#content", Markdown)
            md.update(note.get("body", ""))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle note selection."""
        if event.item and event.item.id:
            idx_str = event.item.id.split("-")[1]
            self.current_note_index = int(idx_str)
            self._update_preview()

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

        def check_result(result: bool) -> None:
            if result:
                removed = self.notes.pop(self.current_note_index)
                self.vault.setdefault("trash", []).append(removed)
                self.save_vault()
                self.run_worker(self.refresh_list())

        self.push_screen(DeleteConfirmScreen(), check_result)

    def save_vault(self) -> None:
        """Persist vault changes to disk."""
        self.save_func(self.vault_path, self.password, self.vault)


def run_tui(vault: dict, vault_path: str, password: str, save_func) -> None:
    """Run the Textual application."""
    app = TsunamiTUI(vault, vault_path, password, save_func)
    app.run()
