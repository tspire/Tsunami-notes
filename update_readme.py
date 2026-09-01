import re

with open("README.md", "r") as f:
    content = f.read()

new_table = """| Command | Description |
|---------|-------------|
| `list` | List all note titles |
| `add <title> [body]` | Add a new note |
| `view <index>` | Display a note |
| `edit <index> [--title T] [--body B]` | Edit a note |
| `delete <index>` | Delete a note |
| `search <query>` | Search note titles and bodies |
| `export <path>` | Export vault to a JSON file |
| `import <path>` | Import notes from a JSON file |
| `trash` | Manage deleted notes (list/restore/empty) |
| `revisions` | Manage note revisions (list/view/rollback) |
| `passwd` | Change the master password |
| `gui` | Launch the Graphical UI |
| `tui` | Launch the Textual UI |
| `interactive` | Enter an interactive shell mode |"""

content = re.sub(
    r"\| Command \| Description \|.*?\| `tui` \| Launch the Textual UI \|",
    new_table,
    content,
    flags=re.DOTALL,
)

with open("README.md", "w") as f:
    f.write(content)
