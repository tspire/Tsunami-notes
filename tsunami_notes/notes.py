"""Tsunami Notes — a private, secure, encrypted notes app for Ubuntu."""

import argparse
import getpass
import json
import os
import secrets
import sys

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
# Note helpers
# ---------------------------------------------------------------------------


def list_notes(vault: dict) -> None:
    """Print the title of every note in *vault*."""
    notes = vault.get("notes", [])
    if not notes:
        print("No notes found.")
        return
    for idx, note in enumerate(notes, start=1):
        title = note.get("title", "(untitled)")
        print(f"  [{idx}] {title}")


def add_note(vault: dict, title: str, body: str) -> None:
    """Append a new note with *title* and *body* to *vault*."""
    vault.setdefault("notes", []).append({"title": title, "body": body})
    print(f"Note '{title}' added.")


def view_note(vault: dict, index: int) -> None:
    """Print the note at 1-based *index*."""
    notes = vault.get("notes", [])
    if not 1 <= index <= len(notes):
        print(f"Error: note index {index} out of range (1–{len(notes)}).")
        return
    note = notes[index - 1]
    print(f"Title : {note.get('title', '')}")
    print(f"Body  :\n{note.get('body', '')}")


def edit_note(vault: dict, index: int, title: str | None, body: str | None) -> bool:
    """Update the title/body of the note at *index*; returns success."""
    notes = vault.get("notes", [])
    if not 1 <= index <= len(notes):
        print(f"Error: note index {index} out of range.")
        return False
    if title is not None:
        notes[index - 1]["title"] = title
    if body is not None:
        notes[index - 1]["body"] = body
    print(f"Note {index} updated.")
    return True


def delete_note(vault: dict, index: int) -> bool:
    """Remove the note at *index*; returns success."""
    notes = vault.get("notes", [])
    if not 1 <= index <= len(notes):
        print(f"Error: note index {index} out of range.")
        return False
    removed = notes.pop(index - 1)
    print(f"Note '{removed.get('title', '')}' deleted.")
    return True


# ---------------------------------------------------------------------------
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

    sub.add_parser("list", help="List all note titles.")

    add_p = sub.add_parser("add", help="Add a new note.")
    add_p.add_argument("title", help="Note title.")
    add_p.add_argument("body", nargs="?", default="", help="Note body text.")

    view_p = sub.add_parser("view", help="View a note by index.")
    view_p.add_argument("index", type=int, help="1-based note index.")

    edit_p = sub.add_parser("edit", help="Edit an existing note.")
    edit_p.add_argument("index", type=int, help="1-based note index.")
    edit_p.add_argument("--title", default=None, help="New title.")
    edit_p.add_argument("--body", default=None, help="New body text.")

    del_p = sub.add_parser("delete", help="Delete a note by index.")
    del_p.add_argument("index", type=int, help="1-based note index.")

    return parser


def _prompt_password(confirm: bool = False) -> str:
    password = getpass.getpass("Master password: ")
    if confirm:
        confirm_pw = getpass.getpass("Confirm password: ")
        if password != confirm_pw:
            print("Error: passwords do not match.")
            sys.exit(1)
    if not password:
        print("Error: password must not be empty.")
        sys.exit(1)
    return password


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

    modified = False

    if args.command == "list":
        list_notes(vault)

    elif args.command == "add":
        add_note(vault, args.title, args.body)
        modified = True

    elif args.command == "view":
        view_note(vault, args.index)

    elif args.command == "edit":
        modified = edit_note(vault, args.index, args.title, args.body)

    elif args.command == "delete":
        modified = delete_note(vault, args.index)

    if modified:
        save_vault(vault_path, password, vault)

    return 0


if __name__ == "__main__":
    sys.exit(main())
