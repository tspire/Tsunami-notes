"""Tsunami Notes — a private, secure, encrypted notes app for Ubuntu."""

import argparse
import getpass
import json
import os
import secrets
import shlex
import subprocess
import tempfile
import sys

from rich.console import Console
from rich.markdown import Markdown

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

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
    """Derive a 256-bit key from *password* using Scrypt."""
    kdf = Scrypt(salt=salt, length=KEY_BYTES, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    return kdf.derive(password.encode("utf-8"))


def _encrypt(key: bytes, plaintext: bytes) -> bytes:
    """Encrypt *plaintext* with AES-256-GCM; returns nonce + ciphertext."""
    nonce = secrets.token_bytes(NONCE_BYTES)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    return nonce + ciphertext


def _decrypt(key: bytes, data: bytes) -> bytes:
    """Decrypt data produced by :func:`_encrypt`."""
    nonce, ciphertext = data[:NONCE_BYTES], data[NONCE_BYTES:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None)


def load_vault(path: str, password: str) -> dict:
    """Load and decrypt the notes vault from *path*.

    Returns an empty vault dict when the file does not exist yet.
    Raises ``ValueError`` on wrong password or corrupted data.
    """
    if not os.path.exists(path):
        return {"notes": []}

    with open(path, "rb") as fh:
        raw = fh.read()

    # Layout: salt (32 B) | encrypted JSON
    salt = raw[:SALT_BYTES]
    encrypted = raw[SALT_BYTES:]

    key = _derive_key(password, salt)
    try:
        plaintext = _decrypt(key, encrypted)
    except Exception as exc:
        raise ValueError("Wrong password or corrupted vault.") from exc

    return json.loads(plaintext.decode("utf-8"))


def _open_secure(path: str):
    """Open *path* for writing with 0o600 permissions, created atomically."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    return os.fdopen(fd, "wb")


def save_vault(path: str, password: str, vault: dict) -> None:
    """Encrypt and persist *vault* to *path*."""
    salt = secrets.token_bytes(SALT_BYTES)
    key = _derive_key(password, salt)
    plaintext = json.dumps(vault, ensure_ascii=False).encode("utf-8")
    encrypted = _encrypt(key, plaintext)

    # Write atomically to avoid partial-write corruption
    tmp_path = path + ".tmp"
    # Remove stale temp file if present (e.g. from a previous crash)
    try:
        os.remove(tmp_path)
    except FileNotFoundError:
        pass
    with _open_secure(tmp_path) as fh:
        fh.write(salt + encrypted)
    os.replace(tmp_path, path)

    # Re-apply restrictive permissions on the final path (replace may inherit
    # the source inode mode, which is already 0o600, but be explicit).
    os.chmod(path, 0o600)


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


# Note helpers
# ---------------------------------------------------------------------------


def list_notes(vault: dict, tag_filter: str | None = None) -> None:
    """Print the title of every note in *vault*."""
    notes = vault.get("notes", [])
    if not notes:
        print("No notes found.")
        return
    count = 0
    for idx, note in enumerate(notes, start=1):
        if tag_filter:
            note_tags = note.get("tags", [])
            if tag_filter not in note_tags:
                continue
        title = note.get("title", "(untitled)")
        count += 1
        print(f"  [{idx}] {title}")
    if count == 0 and tag_filter:
        print(f"No notes found with tag '{tag_filter}'.")


def add_note(vault: dict, title: str, body: str, tags: list[str] | None = None) -> None:
    """Append a new note with *title* and *body* to *vault*."""
    note = {"title": title, "body": body}
    if tags:
        note["tags"] = tags
    vault.setdefault("notes", []).append(note)
    print(f"Note '{title}' added.")


def view_note(vault: dict, index: int) -> None:
    """Print the note at 1-based *index*."""
    notes = vault.get("notes", [])
    if not 1 <= index <= len(notes):
        print(f"Error: note index {index} out of range (1–{len(notes)}).")
        return
    note = notes[index - 1]
    title = note.get("title", "")
    body = note.get("body", "")
    print(f"Title : {title}")
    print("Body  :")
    console = Console()
    console.print(Markdown(body))


def edit_note(
    vault: dict,
    index: int,
    title: str | None,
    body: str | None,
    tags: list[str] | None = None,
) -> bool:
    """Update the title/body of the note at *index*; returns success."""
    notes = vault.get("notes", [])
    if not 1 <= index <= len(notes):
        print(f"Error: note index {index} out of range.")
        return False
    if title is not None:
        notes[index - 1]["title"] = title
    if body is not None:
        notes[index - 1]["body"] = body
    if tags is not None:
        notes[index - 1]["tags"] = tags
    print(f"Note {index} updated.")
    return True


def delete_note(vault: dict, index: int) -> bool:
    """Remove the note at *index* and move it to trash; returns success."""
    notes = vault.get("notes", [])
    if not 1 <= index <= len(notes):
        print(f"Error: note index {index} out of range.")
        return False
    removed = notes.pop(index - 1)
    vault.setdefault("trash", []).append(removed)
    print(f"Note '{removed.get('title', '')}' moved to trash.")
    return True


def list_trash(vault: dict) -> None:
    """Print the title of every note in trash."""
    trash = vault.get("trash", [])
    if not trash:
        print("Trash is empty.")
        return
    for idx, note in enumerate(trash, start=1):
        title = note.get("title", "(untitled)")
        print(f"  [{idx}] {title}")


def restore_trash(vault: dict, index: int) -> bool:
    """Restore the note at *index* from trash to notes."""
    trash = vault.get("trash", [])
    if not 1 <= index <= len(trash):
        print(f"Error: trash index {index} out of range.")
        return False
    restored = trash.pop(index - 1)
    vault.setdefault("notes", []).append(restored)
    print(f"Note '{restored.get('title', '')}' restored.")
    return True


def empty_trash(vault: dict) -> bool:
    """Permanently delete all notes in trash."""
    trash = vault.get("trash", [])
    if not trash:
        print("Trash is already empty.")
        return False
    count = len(trash)
    vault["trash"] = []
    print(f"Emptied {count} notes from trash.")
    return True


def export_vault(vault: dict, path: str) -> None:
    """Export the decrypted vault to a JSON file."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(vault, f, indent=2, ensure_ascii=False)
    print(f"Vault exported to {path}.")


def import_vault(vault: dict, path: str) -> bool:
    """Import notes from a JSON file and append them to the vault."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Failed to read {path}: {e}")
        return False

    imported_notes = data.get("notes", [])
    if not imported_notes:
        print("No notes found in the import file.")
        return False

    vault.setdefault("notes", []).extend(imported_notes)
    print(f"Imported {len(imported_notes)} notes from {path}.")
    return True


# ---------------------------------------------------------------------------


def search_notes(vault: dict, query: str) -> None:
    """Search notes by matching *query* in title or body."""
    notes = vault.get("notes", [])
    query = query.lower()
    found = False
    for idx, note in enumerate(notes, start=1):
        title = note.get("title", "")
        body = note.get("body", "")
        if query in title.lower() or query in body.lower():
            found = True
            print(f"  [{idx}] {title}")
    if not found:
        print("No matching notes found.")


# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="tsunami",
        description="Private, secure, encrypted notes for Ubuntu.",
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

    view_p = sub.add_parser("view", help="View a note by index.")
    view_p.add_argument("index", type=int, help="1-based note index.")

    edit_p = sub.add_parser("edit", help="Edit an existing note.")
    edit_p.add_argument("index", type=int, help="1-based note index.")
    edit_p.add_argument("--title", default=None, help="New title.")
    edit_p.add_argument("--body", default=None, help="New body text.")
    edit_p.add_argument("--tags", help="Comma separated tags.")

    del_p = sub.add_parser("delete", help="Delete a note by index.")
    del_p.add_argument("index", type=int, help="1-based note index.")

    search_p = sub.add_parser("search", help="Search notes by keyword.")
    search_p.add_argument("query", help="Keyword to search for.")

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

    return parser


def _prompt_password(confirm: bool = False, prompt: str = "Master password: ") -> str:
    password = getpass.getpass(prompt)
    if confirm:
        confirm_pw = getpass.getpass("Confirm password: ")
        if password != confirm_pw:
            print("Error: passwords do not match.")
            sys.exit(1)
    if not password:
        print("Error: password must not be empty.")
        sys.exit(1)
    return password


# pylint: disable=too-many-branches
def _run_command(args, vault, password) -> tuple[bool, str]:
    """Execute the command specified in args. Returns (modified, password)."""
    modified = False

    if args.command == "list":
        list_notes(vault, args.tag)

    elif args.command == "add":
        body = args.body
        if body is None:
            body = _edit_in_editor()
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
        if tags is not None:
            tags = [t for t in tags if t]
        add_note(vault, args.title, body, tags)
        modified = True

    elif args.command == "view":
        view_note(vault, args.index)

    elif args.command == "edit":
        body = args.body
        if body is None:
            notes = vault.get("notes", [])
            if 1 <= args.index <= len(notes):
                body = _edit_in_editor(notes[args.index - 1].get("body", ""))
        tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
        if tags is not None:
            tags = [t for t in tags if t]
        modified = edit_note(vault, args.index, args.title, body, tags)

    elif args.command == "delete":
        modified = delete_note(vault, args.index)

    elif args.command == "search":
        search_notes(vault, args.query)

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
        modified = True

    return modified, password


# pylint: disable=too-many-branches
def main(argv: list[str] | None = None) -> int:
    """Run the CLI and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    vault_path = args.vault
    is_new_vault = not os.path.exists(vault_path)

    password = _prompt_password(confirm=is_new_vault)

    try:
        vault = load_vault(vault_path, password)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1

    if args.command == "interactive":
        print("Entering interactive mode. Type 'exit' or 'quit' to quit.")
        while True:
            try:
                line = input("> ").strip()
                if not line:
                    continue
                if line in ("exit", "quit"):
                    break

                parts = shlex.split(line)
                try:
                    iargs = parser.parse_args(parts)
                    if iargs.command == "interactive":
                        print("Already in interactive mode.")
                        continue
                    modified, password = _run_command(iargs, vault, password)
                    if modified:
                        save_vault(vault_path, password, vault)
                except SystemExit:
                    pass
            except EOFError:
                print()
                break
    else:
        modified, password = _run_command(args, vault, password)
        if modified:
            save_vault(vault_path, password, vault)

    return 0


if __name__ == "__main__":
    sys.exit(main())
