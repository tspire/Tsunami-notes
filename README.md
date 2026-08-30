# Tsunami Notes — Ubuntu

Private, secure, and encrypted notes app for Ubuntu, written in Python.

## Features

- **AES-256-GCM** encryption — authenticated encryption protects every byte.
- **Scrypt** key derivation — master password is never stored; the derived key is used only in memory.
- **Fresh salt & nonce** on every save — re-encrypts the vault from scratch each time.
- **Atomic writes** — the vault file is replaced atomically to prevent corruption.
- **Restrictive permissions** — vault file is saved as `0600` (owner read/write only).
- Simple **CLI** interface — add, list, view, edit, and delete notes from the terminal.

## Requirements

```
Python 3.10+
cryptography >= 41.0.0
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

```bash
python notes.py <command> [options]
```

On first run a new vault is created after prompting you to set a master password.
On subsequent runs you are prompted for the existing master password.

### Commands

| Command | Description |
|---------|-------------|
| `list` | List all note titles |
| `add <title> [body]` | Add a new note |
| `view <index>` | Display a note |
| `edit <index> [--title T] [--body B]` | Edit a note |
| `delete <index>` | Delete a note |

### Examples

```bash
# Add a note
python notes.py add "Shopping list" "Milk, eggs, bread"

# List all notes
python notes.py list

# View note #1
python notes.py view 1

# Edit the title of note #1
python notes.py edit 1 --title "Grocery list"

# Delete note #1
python notes.py delete 1

# Use a custom vault path
python notes.py --vault /path/to/my.vault list
```

## Running Tests

```bash
python -m unittest test_notes -v
```

## Vault File Format

```
[ 32 bytes — Scrypt salt ]
[ 12 bytes — AES-GCM nonce | N bytes — AES-256-GCM ciphertext+tag ]
```

The plaintext inside the vault is a UTF-8 encoded JSON object.
