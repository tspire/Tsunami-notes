# Tsunami Notes — Ubuntu

Private, secure, and encrypted notes app for Ubuntu, written in Python.

## Features

- **AES-256-GCM** encryption — authenticated encryption protects every byte.
- **Scrypt** key derivation — master password is never stored; the derived key is used only in memory.
- **Fresh salt & nonce** on every save — re-encrypts the vault from scratch each time.
- **Atomic writes** — the vault file is replaced atomically to prevent corruption.
- **Restrictive permissions** — vault file is saved as `0600` (owner read/write only).
- **Dual Interface** — Simple **CLI** interface for the terminal, or a modern **GUI** with native OS styling.
- **GUI Features**:
  - Native OS theming with themed widgets (ttk)
  - Scrollbars for notes list and editor
  - Native application menu
  - Status bar for non-intrusive feedback

## Requirements

- Python 3.10+
- `cryptography >= 41.0.0` (declared in `pyproject.toml`)
- `python3-venv` (Ubuntu package, for `make venv` / `make install`)

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
# or launch the GUI
.venv/bin/tsunami gui
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

> **Note:** `make install` needs `python3-venv` and network access to download
> `cryptography`. On Ubuntu, install the venv module once with
> `sudo apt install python3-venv`.

## Usage

### GUI

```bash
tsunami gui
```

Launch the graphical interface with a notes list, editor, native menu, and status bar.

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

#### Examples

```bash
# Add a note
tsunami add "Shopping list" "Milk, eggs, bread"

# List all notes
tsunami list

# View note #1
tsunami view 1

# Edit the title of note #1
tsunami edit 1 --title "Grocery list"

# Delete note #1
tsunami delete 1

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
