import re

with open("tsunami_notes/notes.py", "r") as f:
    content = f.read()

# 1. imports
imports = """import argparse
import getpass
import json
import os
import secrets
import shlex
import subprocess
import tempfile
import sys
import time
import re
"""
content = re.sub(r"import argparse\n.*import sys\n", imports, content, flags=re.DOTALL)

# 2. TTL/read limits purging function
purge_func = """
def purge_expired_notes(vault: dict) -> bool:
    \"\"\"Remove notes that have expired (TTL or read limit) from the vault.\"\"\"
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
"""
content = content.replace("# Note helpers\n", purge_func)

# 3. Modify add_note and edit_note signatures and implementations
add_note_new = """def add_note(vault: dict, title: str, body: str, tags: list[str] | None = None, ttl: int | None = None, read_limit: int | None = None) -> None:
    \"\"\"Append a new note with *title* and *body* to *vault*.\"\"\"
    note = {"title": title, "body": body}
    if tags:
        note["tags"] = tags
    if ttl is not None:
        note["expires_at"] = time.time() + ttl
    if read_limit is not None:
        note["read_limit"] = read_limit
    vault.setdefault("notes", []).append(note)
    print(f"Note '{title}' added.")"""
content = re.sub(
    r"def add_note.*?print\(f\"Note '{title}' added\.\"\)",
    add_note_new,
    content,
    flags=re.DOTALL,
)

view_note_new = """def view_note(vault: dict, index: int) -> bool:
    \"\"\"Print the note at 1-based *index*. Decrements read limit if present.\"\"\"
    notes = vault.get("notes", [])
    if not 1 <= index <= len(notes):
        print(f"Error: note index {index} out of range (1–{len(notes)}).")
        return False
    note = notes[index - 1]
    title = note.get("title", "")
    body = note.get("body", "")
    print(f"Title : {title}")
    print("Body  :")
    console = Console()
    console.print(Markdown(body))
    
    modified = False
    if "read_limit" in note:
        note["read_limit"] -= 1
        modified = True
    return modified"""
content = re.sub(
    r"def view_note.*?console\.print\(Markdown\(body\)\)",
    view_note_new,
    content,
    flags=re.DOTALL,
)

edit_note_new = """def edit_note(
    vault: dict,
    index: int,
    title: str | None,
    body: str | None,
    tags: list[str] | None = None,
    ttl: int | None = None,
    read_limit: int | None = None,
) -> bool:
    \"\"\"Update the title/body/tags/ttl/read_limit of the note at *index*; returns success.\"\"\"
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
    if ttl is not None:
        notes[index - 1]["expires_at"] = time.time() + ttl
    if read_limit is not None:
        notes[index - 1]["read_limit"] = read_limit
    print(f"Note {index} updated.")
    return True"""
content = re.sub(
    r"def edit_note.*?return True", edit_note_new, content, flags=re.DOTALL
)

# 4. search_notes
search_notes_new = """def search_notes(vault: dict, query: str, use_regex: bool = False, fuzzy: bool = False) -> None:
    \"\"\"Search notes by matching *query* in title or body.\"\"\"
    notes = vault.get("notes", [])
    found = False
    
    if fuzzy:
        pattern = ".*?".join(map(re.escape, query))
        regex = re.compile(pattern, re.IGNORECASE)
    elif use_regex:
        try:
            regex = re.compile(query, re.IGNORECASE)
        except re.error as e:
            print(f"Invalid regex: {e}")
            return
    else:
        query_lower = query.lower()
        
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
            print(f"  [{idx}] {title}")
    if not found:
        print("No matching notes found.")"""
content = re.sub(
    r"def search_notes.*?print\(\"No matching notes found\.\"\)",
    search_notes_new,
    content,
    flags=re.DOTALL,
)

# 5. build_parser additions
parser_add_ttl = """
    add_p.add_argument("--tags", help="Comma separated tags.")
    add_p.add_argument("--ttl", type=int, help="Time to live in seconds.")
    add_p.add_argument("--read-limit", type=int, help="Number of times this note can be read.")
"""
content = content.replace(
    '    add_p.add_argument("--tags", help="Comma separated tags.")', parser_add_ttl
)

parser_edit_ttl = """
    edit_p.add_argument("--tags", help="Comma separated tags.")
    edit_p.add_argument("--ttl", type=int, help="Time to live in seconds.")
    edit_p.add_argument("--read-limit", type=int, help="Number of times this note can be read.")
"""
content = content.replace(
    '    edit_p.add_argument("--tags", help="Comma separated tags.")', parser_edit_ttl
)

parser_search = """
    search_p.add_argument("query", help="Keyword to search for.")
    search_p.add_argument("--regex", action="store_true", help="Use regular expression.")
    search_p.add_argument("--fuzzy", action="store_true", help="Use fuzzy matching.")
"""
content = content.replace(
    '    search_p.add_argument("query", help="Keyword to search for.")', parser_search
)

parser_extra = """
    sub.add_parser("gui", help="Launch the GUI.")
    sub.add_parser("tui", help="Launch the Textual TUI.")
    sub.add_parser("duress-setup", help="Set up a duress PIN/password and fake vault.")
"""
content = content.replace(
    '    sub.add_parser("gui", help="Launch the GUI.")', parser_extra
)

# 6. _run_command additions
run_cmd_start = """def _run_command(args, vault, vault_path, password) -> tuple[bool, str]:
    \"\"\"Execute the command specified in args. Returns (modified, password).\"\"\"
    modified = purge_expired_notes(vault)
"""
content = content.replace(
    'def _run_command(args, vault, vault_path, password) -> tuple[bool, str]:\n    """Execute the command specified in args. Returns (modified, password)."""\n    modified = False',
    run_cmd_start,
)

run_cmd_add = """        add_note(vault, args.title, body, tags, args.ttl, args.read_limit)
        modified = True"""
content = content.replace(
    "        add_note(vault, args.title, body, tags)\n        modified = True",
    run_cmd_add,
)

run_cmd_view = """    elif args.command == "view":
        if view_note(vault, args.index):
            modified = True"""
content = content.replace(
    '    elif args.command == "view":\n        view_note(vault, args.index)',
    run_cmd_view,
)

run_cmd_edit = """        mod = edit_note(vault, args.index, args.title, body, tags, args.ttl, args.read_limit)
        if mod: modified = True"""
content = content.replace(
    "        modified = edit_note(vault, args.index, args.title, body, tags)",
    run_cmd_edit,
)

run_cmd_search = """    elif args.command == "search":
        search_notes(vault, args.query, args.regex, args.fuzzy)"""
content = content.replace(
    '    elif args.command == "search":\n        search_notes(vault, args.query)',
    run_cmd_search,
)

run_cmd_extra = """    elif args.command == "gui":
        # pylint: disable=import-outside-toplevel
        try:
            from .gui import run_gui
        except ImportError as e:
            if "tkinter" in str(e):
                print("Error: The GUI requires 'tkinter', which is not installed.")
                print("On Ubuntu, you can install it with: sudo apt install python3-tk")
                sys.exit(1)
            raise

        run_gui(vault, vault_path, password, save_vault)

    elif args.command == "tui":
        # pylint: disable=import-outside-toplevel
        try:
            from .tui import run_tui
        except ImportError as e:
            print("Error: The TUI requires 'textual'. Install it with: pip install textual")
            sys.exit(1)
        run_tui(vault, vault_path, password, save_vault)

    elif args.command == "duress-setup":
        duress_password = _prompt_password(confirm=True, prompt="New duress password/PIN: ")
        fake_vault_path = vault_path + ".fake"
        save_vault(fake_vault_path, duress_password, {"notes": []})
        print(f"Duress vault created at {fake_vault_path}.")
"""
content = content.replace(
    """    elif args.command == "gui":
        # pylint: disable=import-outside-toplevel
        try:
            from .gui import run_gui
        except ImportError as e:
            if "tkinter" in str(e):
                print("Error: The GUI requires 'tkinter', which is not installed.")
                print("On Ubuntu, you can install it with: sudo apt install python3-tk")
                sys.exit(1)
            raise

        run_gui(vault, vault_path, password, save_vault)""",
    run_cmd_extra,
)

# 7. main loading logic for duress
main_load = """    try:
        vault = load_vault(vault_path, password)
    except ValueError as exc:
        fake_vault_path = vault_path + ".fake"
        try:
            vault = load_vault(fake_vault_path, password)
            vault_path = fake_vault_path
        except ValueError:
            print(f"Error: {exc}")
            return 1
            
    # Purge expired notes early
    if purge_expired_notes(vault):
        save_vault(vault_path, password, vault)
"""
content = content.replace(
    """    try:
        vault = load_vault(vault_path, password)
    except ValueError as exc:
        print(f"Error: {exc}")
        return 1""",
    main_load,
)


with open("tsunami_notes/notes.py", "w") as f:
    f.write(content)
