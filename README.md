# Tsunami Notes

Private, secure, and encrypted notes app for macOS and Linux, written in Python with a Rust-based cryptography engine.

## Features

- **AES-256-GCM** encryption — authenticated encryption protects every byte.
- **Scrypt** key derivation — master password is never stored; the derived key is used only in memory.
- **Fresh salt & nonce** on every save — re-encrypts the vault from scratch each time.
- **Atomic writes** — the vault file is replaced atomically to prevent corruption.
- **Restrictive permissions** — vault file is saved as `0600` (owner read/write only).
- **Multiple Interfaces** — Simple **CLI** for the terminal, a modern **GUI** (tkinter), and a **TUI** (Textual).
- **GUI Features**:
  - Native OS theming with themed widgets (ttk)
  - Scrollbars for notes list and editor
  - Native application menu
  - Status bar for non-intrusive feedback
- **Search & Tagging** — organize and quickly find notes.
- **Trash (Soft Delete)** — recover deleted notes before they are permanently removed.
- **Duress Passwords & Fake Vaults** — protect against forced access by setting up a decoy vault.
- **Password Agent** — securely cache your password in the background for a smoother experience.
- **Audio Feedback** — optional sound effects using `pygame-ce`.

## Requirements

- Python 3.10+
- Rust toolchain (`cargo` / `rustc`) to build the cryptography extension

Depending on your OS, you may need additional packages for the virtual environment and GUI:
- **macOS (Homebrew):** `brew install python rust python-tk`
- **Debian / Ubuntu:** `sudo apt install python3-venv python3-tk rustc cargo`
- **Fedora:** `sudo dnf install python3-tkinter rust cargo`
- **Arch Linux:** `sudo pacman -S tk rust cargo`

## Development setup (virtualenv)

Create a `.venv` and install the app in editable mode:

```bash
make venv
```

Run the app from the virtualenv:

```bash
make run ARGS="list"
# or
.venv/bin/tsunami list
# or launch the GUI / TUI
.venv/bin/tsunami gui
.venv/bin/tsunami tui
```

## Development tools

Install the dev tools (`black`, `pylint`) into the `.venv`:

```bash
make dev
```

Format the code:

```bash
make black
```

Run the linter (black, then pylint):

```bash
make lint
```

Dev-only dependencies live in `requirements.dev.txt`; production dependencies
are declared in `pyproject.toml`.

## Install

The app is installed into `/opt/tsunami` (its own virtualenv) with a small
wrapper at `/usr/local/bin/tsunami`:

```bash
sudo make install
```

Remove it again with:

```bash
sudo make uninstall
```

You can also build a wheel without installing:

```bash
make build   # → dist/tsunami_notes-0.1.0-py3-none-any.whl
```

> **Note:** `make install` needs Python's venv module and the Rust toolchain to compile
> the cryptography extension. Please ensure you have the required packages for your OS
> installed (see the Requirements section).

## Usage

### GUI & TUI

```bash
tsunami gui
# or
tsunami tui
```

Launch the graphical interface (Tkinter) or terminal user interface (Textual) for a richer experience.

### CLI

```bash
tsunami <command> [options]
```

On first run a new vault is created after prompting you to set a master password.
On subsequent runs you are prompted for the existing master password.

#### Commands

| Command | Description |
|---------|-------------|
| `list` | List all note titles |
| `add <title> [body]` | Add a new note |
| `view <index>` | Display a note |
| `edit <index> [--title T] [--body B]` | Edit a note |
| `delete <index>` | Delete a note |
| `search <keyword>` | Search notes by keyword |
| `export <file>` | Export the decrypted vault to JSON |
| `import <file>` | Import notes from a JSON file |
| `trash` | Manage trash (`list`, `restore <index>`, `empty`) |
| `interactive` | Start an interactive session |
| `passwd` | Change the master password |
| `tui` | Launch the Textual TUI |
| `gui` | Launch the Tkinter GUI |
| `duress-setup` | Set up a duress PIN/password and fake vault |
| `agent` | Manage background password agent (`start`, `stop`, `status`) |
| `unlock` | Cache the master password in the agent for this session |

#### Examples

```bash
# Add a note
tsunami add "Shopping list" "Milk, eggs, bread"

# List all notes
tsunami list

# Search for notes containing a keyword
tsunami search "password"

# Launch Textual TUI
tsunami tui

# Use a custom vault path
tsunami --vault /path/to/my.vault list
```

## Running Tests

`make test` runs the linter (black + pylint) before the tests.

```bash
make test
# or
.venv/bin/python -m unittest test_notes -v
```

## Vault File Format

```
[ 32 bytes — Scrypt salt ]
[ 12 bytes — AES-GCM nonce | N bytes — AES-256-GCM ciphertext+tag ]
```

The plaintext inside the vault is a UTF-8 encoded JSON object.
