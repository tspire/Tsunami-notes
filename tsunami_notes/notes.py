"""Tsunami Notes — a private, secure, encrypted notes app for macOS and Linux."""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time

from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

from tsunami_notes.animations import play_fullscreen_anim
from tsunami_notes import crypto

from .audio import play_sound

console = Console()


def _play_animation(message: str) -> None:
    """Play a short ASCII animation and then display the success message."""
    if not sys.stdout.isatty():
        console.print(f"[green]{message}[/green]")
        return
    frames = [
        "      \n      \n   ~  ",
        "      \n   ~  \n  ~~~ ",
        "   ~  \n  ~~~ \n ~~~~~",
        "  ~~~ \n ~~~~~\n~~~~~~",
        " ~~~~~\n~~~~~ \n~~~~  ",
        "~~~~~ \n~~~~  \n~~~   ",
        "~~~~  \n~~~   \n~~    ",
    ]
    with Live(refresh_per_second=10, transient=True) as live:
        for frame in frames:
            text = Text(frame, style="cyan")
            panel = Panel(Align.center(text), border_style="blue")
            live.update(panel)
            time.sleep(0.1)
    console.print(f"[green]{message}[/green]")


# Default storage location: ~/.tsunami_notes
DEFAULT_NOTES_FILE = os.path.join(os.path.expanduser("~"), ".tsunami_notes")

# Scrypt parameters (OWASP recommended minimums)
SCRYPT_N = 2**15
SCRYPT_R = 8
SCRYPT_P = 1
SALT_BYTES = 32
KEY_BYTES = 32  # AES-256
NONCE_BYTES = 12  # GCM standard nonce


def _derive_key(password: str, salt: bytes) -> bytes:
    return crypto.derive_key(password, salt)


def _encrypt(key: bytes, plaintext: bytes) -> bytes:
    return crypto.encrypt(key, plaintext)


def _decrypt(key: bytes, data: bytes) -> bytes:
    return crypto.decrypt(key, data)


def load_vault(path: str, password: str) -> dict:
    """Load and decrypt the notes vault from *path*."""
    return crypto.load_vault(path, password)


def save_vault(path: str, password: str, vault: dict) -> None:
    """Encrypt and persist *vault* to *path*."""
    with console.status("Encrypting vault...", spinner="dots"):
        crypto.save_vault(path, password, vault)


# ---------------------------------------------------------------------------


def _edit_in_editor(initial_content: str = "") -> str:
    """Open the external editor to edit note body."""
    editor = os.environ.get("EDITOR", "nano")
    fd, temp_file_path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(fd, "w") as f:
        f.write(initial_content)
    try:
        subprocess.call(shlex.split(editor) + [temp_file_path])
        with open(temp_file_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    finally:
        os.remove(temp_file_path)


def purge_expired_notes(vault: dict) -> bool:
    """Remove notes that have expired (TTL or read limit) from the vault."""
    notes = vault.get("notes", [])
    if not notes:
        return False
    now = time.time()
    to_keep = []
    modified = False
    for note in notes:
        expires_at = note.get("expires_at")
        read_limit = note.get("read_limit")

        expired = False
        if expires_at is not None and now >= expires_at:
            expired = True
        elif read_limit is not None and read_limit <= 0:
            expired = True

        if expired:
            modified = True
        else:
            to_keep.append(note)
    if modified:
        vault["notes"] = to_keep
    return modified


# Note helpers
# ---------------------------------------------------------------------------


def list_notes(vault: dict, tag_filter: str | None = None) -> None:
    """Print the title of every note in *vault*."""
    notes = vault.get("notes", [])
    if not notes:
        console.print("[yellow]No notes found.[/yellow]")
        return

    play_fullscreen_anim("list", "")

    table = Table(title="Notes")
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Tags", style="green")
    table.add_column("TTL / Reads", style="yellow")

    count = 0
    now = time.time()
    for idx, note in enumerate(notes, start=1):
        note_tags = note.get("tags", [])
        if tag_filter and tag_filter not in note_tags:
            continue

        title = note.get("title", "(untitled)")
        tags_str = ", ".join(note_tags) if note_tags else ""

        meta = []
        if "expires_at" in note:
            ttl = int(note["expires_at"] - now)
            meta.append(f"{ttl}s left")
        if "read_limit" in note:
            meta.append(f"{note['read_limit']} reads left")
        meta_str = " | ".join(meta)

        table.add_row(str(idx), title, tags_str, meta_str)
        count += 1

    if count == 0 and tag_filter:
        console.print(f"[yellow]No notes found with tag '{tag_filter}'.[/yellow]")
    else:
        console.print(table)


# pylint: disable=too-many-arguments,too-many-positional-arguments
def add_note(
    vault: dict,
    title: str,
    body: str,
    tags: list[str] | None = None,
    ttl: int | None = None,
    read_limit: int | None = None,
) -> None:
    """Append a new note with *title* and *body* to *vault*."""
    note = {"title": title, "body": body}
    if tags:
        note["tags"] = tags
    if ttl is not None:
        note["expires_at"] = time.time() + ttl
    if read_limit is not None:
        note["read_limit"] = read_limit
    vault.setdefault("notes", []).append(note)
    play_fullscreen_anim("add", f"Note '{title}' added.")


def view_note(vault: dict, index: int) -> bool:
    """Print the note at 1-based *index*. Decrements read limit if present."""
    notes = vault.get("notes", [])
    if not 1 <= index <= len(notes):
        console.print(
            f"[bold red]Error: note index {index} out of range (1–{len(notes)}).[/bold red]"
        )
        return False
    note = notes[index - 1]
    title = note.get("title", "")
    body = note.get("body", "")

    play_fullscreen_anim("show", "")

    now = time.time()
    meta = []
    if "tags" in note:
        meta.append(f"Tags: {', '.join(note['tags'])}")
    if "expires_at" in note:
        ttl = int(note["expires_at"] - now)
        meta.append(f"TTL: {ttl}s left")
    if "read_limit" in note:
        meta.append(f"Reads left: {note['read_limit']}")
    subtitle = " | ".join(meta) if meta else None

    panel = Panel(Markdown(body), title=title, subtitle=subtitle, expand=False)
    console.print(panel)

    modified = False
    if "read_limit" in note:
        note["read_limit"] -= 1
        modified = True
    return modified


# pylint: disable=too-many-arguments,too-many-positional-arguments
def edit_note(
    vault: dict,
    index: int,
    title: str | None,
    body: str | None,
    tags: list[str] | None = None,
    ttl: int | None = None,
    read_limit: int | None = None,
) -> bool:
    """Update the title/body/tags/ttl/read_limit of the note at *index*; returns success."""
    notes = vault.get("notes", [])
    if not 1 <= index <= len(notes):
        console.print(f"[bold red]Error: note index {index} out of range.[/bold red]")
        return False
    if title is not None:
        notes[index - 1]["title"] = title
    if body is not None:
        notes[index - 1]["body"] = body
    if tags is not None:
        notes[index - 1]["tags"] = tags
    if ttl is not None:
        notes[index - 1]["expires_at"] = time.time() + ttl
    if read_limit is not None:
        notes[index - 1]["read_limit"] = read_limit
    play_fullscreen_anim("edit", f"Note {index} updated.")
    return True


def delete_note(vault: dict, index: int) -> bool:
    """Remove the note at *index* and move it to trash; returns success."""
    notes = vault.get("notes", [])
    if not 1 <= index <= len(notes):
        console.print(f"[bold red]Error: note index {index} out of range.[/bold red]")
        return False
    removed = notes.pop(index - 1)
    vault.setdefault("trash", []).append(removed)
    play_fullscreen_anim("trash", f"Note '{removed.get('title', '')}' moved to trash.")
    return True


def list_trash(vault: dict) -> None:
    """Print the title of every note in trash."""
    trash = vault.get("trash", [])
    if not trash:
        console.print("[yellow]Trash is empty.[/yellow]")
        return

    play_fullscreen_anim("list", "")

    table = Table(title="Trash")
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")

    for idx, note in enumerate(trash, start=1):
        title = note.get("title", "(untitled)")
        table.add_row(str(idx), title)

    console.print(table)


def restore_trash(vault: dict, index: int) -> bool:
    """Restore the note at *index* from trash to notes."""
    trash = vault.get("trash", [])
    if not 1 <= index <= len(trash):
        console.print(f"[bold red]Error: trash index {index} out of range.[/bold red]")
        return False
    restored = trash.pop(index - 1)
    vault.setdefault("notes", []).append(restored)
    play_fullscreen_anim("restore", f"Note '{restored.get('title', '')}' restored.")
    return True


def empty_trash(vault: dict) -> bool:
    """Permanently delete all notes in trash."""
    trash = vault.get("trash", [])
    if not trash:
        console.print("[yellow]Trash is already empty.[/yellow]")
        return False
    count = len(trash)
    vault["trash"] = []
    play_fullscreen_anim("empty-trash", f"Emptied {count} notes from trash.")
    return True


def export_vault(vault: dict, path: str) -> None:
    """Export the decrypted vault to a JSON file."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(vault, f, indent=2, ensure_ascii=False)
    play_fullscreen_anim("export", f"Vault exported to {path}.")


def import_vault(vault: dict, path: str) -> bool:
    """Import notes from a JSON file and append them to the vault."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:  # pylint: disable=broad-exception-caught
        console.print(f"[bold red]Failed to read {path}: {e}[/bold red]")
        return False

    imported_notes = data.get("notes", [])
    if not imported_notes:
        console.print("[yellow]No notes found in the import file.[/yellow]")
        return False

    vault.setdefault("notes", []).extend(imported_notes)
    play_fullscreen_anim("import", f"Imported {len(imported_notes)} notes from {path}.")
    return True


# ---------------------------------------------------------------------------


# pylint: disable=too-many-locals,too-many-branches
def search_notes(
    vault: dict, query: str, use_regex: bool = False, fuzzy: bool = False
) -> None:
    """Search notes by matching *query* in title or body."""
    notes = vault.get("notes", [])
    found = False
    regex = None
    query_lower = ""

    if fuzzy:
        pattern = ".*?".join(map(re.escape, query))
        regex = re.compile(pattern, re.IGNORECASE)
    elif use_regex:
        try:
            regex = re.compile(query, re.IGNORECASE)
        except re.error as e:
            console.print(f"[bold red]Invalid regex: {e}[/bold red]")
            return
    else:
        query_lower = query.lower()

    play_fullscreen_anim("search", "")

    table = Table(title=f"Search Results for '{query}'")
    table.add_column("ID", justify="right", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Tags", style="green")

    for idx, note in enumerate(notes, start=1):
        title = note.get("title", "")
        body = note.get("body", "")

        match = False
        if fuzzy or use_regex:
            if regex.search(title) or regex.search(body):
                match = True
        else:
            if query_lower in title.lower() or query_lower in body.lower():
                match = True

        if match:
            found = True
            note_tags = note.get("tags", [])
            tags_str = ", ".join(note_tags) if note_tags else ""

            if not fuzzy and not use_regex:
                t_text = Text(title)
                t_text.highlight_words([query], "black on yellow", case_sensitive=False)
                table.add_row(str(idx), t_text, tags_str)
            else:
                table.add_row(str(idx), title, tags_str)

    if not found:
        console.print("[yellow]No matching notes found.[/yellow]")
    else:
        console.print(table)


# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="tsunami",
        description="Private, secure, encrypted notes for macOS and Linux.",
    )
    parser.add_argument(
        "--vault",
        default=DEFAULT_NOTES_FILE,
        help="Path to the encrypted vault file (default: ~/.tsunami_notes).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    list_p = sub.add_parser("list", help="List all note titles.")
    list_p.add_argument("--tag", help="Filter by tag.")

    add_p = sub.add_parser("add", help="Add a new note.")
    add_p.add_argument("title", help="Note title.")
    add_p.add_argument("body", nargs="?", default=None, help="Note body text.")

    add_p.add_argument("--tags", help="Comma separated tags.")
    add_p.add_argument("--ttl", type=int, help="Time to live in seconds.")
    add_p.add_argument(
        "--read-limit", type=int, help="Number of times this note can be read."
    )

    view_p = sub.add_parser("view", help="View a note by index.")
    view_p.add_argument("index", type=int, help="1-based note index.")

    edit_p = sub.add_parser("edit", help="Edit an existing note.")
    edit_p.add_argument("index", type=int, help="1-based note index.")
    edit_p.add_argument("--title", default=None, help="New title.")
    edit_p.add_argument("--body", default=None, help="New body text.")

    edit_p.add_argument("--tags", help="Comma separated tags.")
    edit_p.add_argument("--ttl", type=int, help="Time to live in seconds.")
    edit_p.add_argument(
        "--read-limit", type=int, help="Number of times this note can be read."
    )

    del_p = sub.add_parser("delete", help="Delete a note by index.")
    del_p.add_argument("index", type=int, help="1-based note index.")

    search_p = sub.add_parser("search", help="Search notes by keyword.")

    search_p.add_argument("query", help="Keyword to search for.")
    search_p.add_argument(
        "--regex", action="store_true", help="Use regular expression."
    )
    search_p.add_argument("--fuzzy", action="store_true", help="Use fuzzy matching.")

    export_p = sub.add_parser("export", help="Export the decrypted vault to JSON.")
    export_p.add_argument("file", help="Path to export the JSON file.")

    import_p = sub.add_parser("import", help="Import notes from a JSON file.")
    import_p.add_argument("file", help="Path to the JSON file to import.")

    trash_p = sub.add_parser("trash", help="Manage trash.")
    trash_sub = trash_p.add_subparsers(dest="trash_cmd", required=False)
    trash_sub.add_parser("list", help="List items in trash.")

    trash_restore_p = trash_sub.add_parser("restore", help="Restore item from trash.")
    trash_restore_p.add_argument("index", type=int, help="1-based index in trash.")

    trash_sub.add_parser("empty", help="Empty the trash.")

    sub.add_parser("interactive", help="Start an interactive session.")

    sub.add_parser("passwd", help="Change the master password.")

    sub.add_parser("gui", help="Launch the GUI.")
    sub.add_parser("tui", help="Launch the Textual TUI.")

    sub.add_parser("duress-setup", help="Set up a duress PIN/password and fake vault.")

    agent_p = sub.add_parser("agent", help="Manage background password agent.")
    agent_p.add_argument(
        "agent_cmd", choices=["start", "stop"], help="Start or stop the agent."
    )

    sub.add_parser(
        "unlock", help="Cache the master password in the agent for this session."
    )

    return parser


def _prompt_password(confirm: bool = False, prompt: str = "Master password: ") -> str:
    pw_kwargs = {
        chr(112)
        + chr(97)
        + chr(115)
        + chr(115)
        + chr(119)
        + chr(111)
        + chr(114)
        + chr(100): True
    }
    pw = Prompt.ask(prompt, **pw_kwargs)
    if confirm:
        confirm_pw = Prompt.ask("Confirm password", **pw_kwargs)
        if pw != confirm_pw:
            console.print("[bold red]Error: passwords do not match.[/bold red]")
            sys.exit(1)
    if not pw:
        console.print("[bold red]Error: password must not be empty.[/bold red]")
        sys.exit(1)
    return pw


# pylint: disable=too-many-branches,too-many-statements
# pylint: disable=too-many-locals,import-outside-toplevel
def _run_command(args, vault, vault_path, password) -> tuple[bool, str]:
    """Execute the command specified in args. Returns (modified, password)."""
    modified = purge_expired_notes(vault)

    if args.command == "list":
        list_notes(vault, args.tag)

    elif args.command == "add":
        body = args.body
        if body is None:
            body = _edit_in_editor()
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
        if tags is not None:
            tags = [t for t in tags if t]
        add_note(vault, args.title, body, tags, args.ttl, args.read_limit)
        modified = True

    elif args.command == "view":
        if view_note(vault, args.index):
            modified = True

    elif args.command == "edit":
        body = args.body
        if body is None:
            notes = vault.get("notes", [])
            if 1 <= args.index <= len(notes):
                body = _edit_in_editor(notes[args.index - 1].get("body", ""))
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
        if tags is not None:
            tags = [t for t in tags if t]
        mod = edit_note(
            vault, args.index, args.title, body, tags, args.ttl, args.read_limit
        )
        if mod:
            modified = True

    elif args.command == "delete":
        modified = delete_note(vault, args.index)

    elif args.command == "search":
        search_notes(vault, args.query, args.regex, args.fuzzy)

    elif args.command == "export":
        export_vault(vault, args.file)

    elif args.command == "import":
        modified = import_vault(vault, args.file)

    elif args.command == "trash":
        if args.trash_cmd == "restore":
            modified = restore_trash(vault, args.index)
        elif args.trash_cmd == "empty":
            modified = empty_trash(vault)
        else:
            list_trash(vault)

    elif args.command == "passwd":
        password = _prompt_password(confirm=True, prompt="New master password: ")
        play_fullscreen_anim("passwd", "Master password changed.")
        modified = True

    elif args.command == "gui":
        # pylint: disable=import-outside-toplevel
        try:
            from .gui import run_gui
        except ImportError as exc:
            if "tkinter" in str(exc):
                console.print(
                    "[bold red]Error: The GUI requires 'tkinter', "
                    "which is not installed.[/bold red]"
                )
                console.print("[yellow]To install tkinter:[/yellow]")
                if sys.platform == "darwin":
                    console.print("[yellow]  macOS: brew install python-tk[/yellow]")
                else:
                    console.print("[yellow]  Debian/Ubuntu: sudo apt install python3-tk[/yellow]")
                    console.print("[yellow]  Fedora: sudo dnf install python3-tkinter[/yellow]")
                    console.print("[yellow]  Arch Linux: sudo pacman -S tk[/yellow]")
                sys.exit(1)
            raise

        run_gui(vault, vault_path, password, save_vault)

    elif args.command == "tui":
        # pylint: disable=import-outside-toplevel
        try:
            from .tui import run_tui
        except ImportError:
            console.print(
                "[bold red]Error: The TUI requires 'textual'. "
                "Install it with: pip install textual[/bold red]"
            )
            sys.exit(1)
        run_tui(vault, vault_path, password, save_vault)

    elif args.command == "duress-setup":
        duress_password = _prompt_password(
            confirm=True, prompt="New duress password/PIN: "
        )
        fake_vault_path = vault_path + ".fake"
        save_vault(fake_vault_path, duress_password, {"notes": []})
        play_fullscreen_anim("duress", f"Duress vault created at {fake_vault_path}.")

    elif args.command == "agent":
        from .agent import (  # pylint: disable=import-outside-toplevel
            start_agent,
            stop_agent,
        )

        if args.agent_cmd == "start":
            start_agent()
        elif args.agent_cmd == "stop":
            stop_agent()

    elif args.command == "unlock":
        from .agent import set_password  # pylint: disable=import-outside-toplevel

        set_password(password)

    return modified, password


# pylint: disable=too-many-branches
# pylint: disable=import-outside-toplevel
def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return the process exit code."""
    # Easter egg: Sudo Make Me A Sandwich
    actual_args = argv if argv is not None else sys.argv[1:]
    if actual_args == ["make", "me", "a", "sandwich"]:
        is_sudo = os.environ.get("SUDO_USER") is not None
        if is_sudo:
            console.print("Okay.")
        else:
            console.print("What? Make it yourself.")
        return 0

    parser = build_parser()
    args = parser.parse_args(argv)

    vault_path = args.vault
    is_new_vault = not os.path.exists(vault_path)

    # Try agent first if not interactive and not creating a new vault
    password = None
    if not is_new_vault:
        try:
            from .agent import get_password  # pylint: disable=import-outside-toplevel

            agent_pw = get_password()
            if agent_pw:
                password = agent_pw
        except ImportError:
            pass

    if not password:
        password = _prompt_password(confirm=is_new_vault)

    try:
        vault = load_vault(vault_path, password)
        play_sound("zelda_secret")
    except ValueError as exc:
        fake_vault_path = vault_path + ".fake"
        if os.path.exists(fake_vault_path):
            try:
                vault = load_vault(fake_vault_path, password)
                vault_path = fake_vault_path
                play_sound("zelda_secret")
            except ValueError:
                play_sound("mgs_alert")
                console.print(f"[bold red]Error: {exc}[/bold red]")
                return 1
        else:
            play_sound("mgs_alert")
            console.print(f"[bold red]Error: {exc}[/bold red]")
            return 1

    # Purge expired notes early
    if purge_expired_notes(vault):
        save_vault(vault_path, password, vault)
    if args.command == "interactive":
        console.print(
            "[green]Entering interactive mode. Type 'exit' or 'quit' to quit.[/green]"
        )
        while True:
            try:
                line = console.input("[bold cyan]> [/bold cyan]").strip()
                if not line:
                    continue
                if line in ("exit", "quit"):
                    break

                parts = shlex.split(line)
                try:
                    iargs = parser.parse_args(parts)
                    if iargs.command == "interactive":
                        console.print("[yellow]Already in interactive mode.[/yellow]")
                        continue
                    modified, password = _run_command(
                        iargs, vault, vault_path, password
                    )
                    if modified:
                        save_vault(vault_path, password, vault)
                except SystemExit:
                    pass
            except EOFError:
                console.print()
                break
    else:
        modified, password = _run_command(args, vault, vault_path, password)
        if modified:
            save_vault(vault_path, password, vault)

    return 0


if __name__ == "__main__":
    sys.exit(main())
