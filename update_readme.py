import re

with open("README.md", "r") as f:
    content = f.read()

# Replace title and description
content = content.replace("# Tsunami Notes — Ubuntu", "# Tsunami Notes")
content = content.replace("Private, secure, and encrypted notes app for Ubuntu, written in Python with a Rust-based cryptography engine.", "Private, secure, and encrypted notes app for macOS and Linux, written in Python with a Rust-based cryptography engine.")

# Replace Requirements section
old_reqs = """## Requirements

- Python 3.10+
- Rust toolchain (`cargo` / `rustc`) to build the cryptography extension
- `python3-venv` (Ubuntu package, for `make venv` / `make install`)"""

new_reqs = """## Requirements

- Python 3.10+
- Rust toolchain (`cargo` / `rustc`) to build the cryptography extension

Depending on your OS, you may need additional packages for the virtual environment and GUI:
- **macOS (Homebrew):** `brew install python rust python-tk`
- **Debian / Ubuntu:** `sudo apt install python3-venv python3-tk rustc cargo`
- **Fedora:** `sudo dnf install python3-tkinter rust cargo`
- **Arch Linux:** `sudo pacman -S tk rust cargo`"""

content = content.replace(old_reqs, new_reqs)

# Replace Ubuntu specific note in Install section
old_note = """> **Note:** `make install` needs `python3-venv` and the Rust toolchain to compile
> the cryptography extension. On Ubuntu, install the venv module with
> `sudo apt install python3-venv`."""

new_note = """> **Note:** `make install` needs Python's venv module and the Rust toolchain to compile
> the cryptography extension. Please ensure you have the required packages for your OS
> installed (see the Requirements section)."""

content = content.replace(old_note, new_note)

with open("README.md", "w") as f:
    f.write(content)
