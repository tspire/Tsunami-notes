"""Textual TUI for Tsunami Notes."""

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Header, Footer, ListView, ListItem, Label, Markdown


class TsunamiTUI(App):
    """A Textual app for Tsunami Notes."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
    ]

    def __init__(self, vault: dict, vault_path: str, password: str, save_func):
        super().__init__()
        self.vault = vault
        self.vault_path = vault_path
        self.password = password
        self.save_func = save_func
        self.notes = vault.get("notes", [])

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Horizontal():
            yield ListView(id="sidebar")
            yield Markdown("", id="content")
        yield Footer()

    def on_mount(self) -> None:
        """Setup after mounting."""
        sidebar = self.query_one("#sidebar", ListView)
        for i, note in enumerate(self.notes):
            title = note.get("title", "(untitled)")
            sidebar.append(ListItem(Label(f"{i+1}. {title}"), id=f"note-{i}"))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle note selection."""
        idx_str = event.item.id.split("-")[1]
        note = self.notes[int(idx_str)]
        md = self.query_one("#content", Markdown)
        md.update(note.get("body", ""))


def run_tui(vault: dict, vault_path: str, password: str, save_func) -> None:
    """Run the Textual application."""
    app = TsunamiTUI(vault, vault_path, password, save_func)
    app.run()
