import sys
import os

with open("tsunami_notes/notes.py", "r") as f:
    content = f.read()

# Replace docstring
content = content.replace("Tsunami Notes — a private, secure, encrypted notes app for Ubuntu.", "Tsunami Notes — a private, secure, encrypted notes app for macOS and Linux.")

# Replace argparse description
content = content.replace("Private, secure, encrypted notes for Ubuntu.", "Private, secure, encrypted notes for macOS and Linux.")

# Replace tkinter error message
old_tk_msg = """                console.print(
                    "[yellow]On Ubuntu, you can install it with: "
                    "sudo apt install python3-tk[/yellow]"
                )"""

new_tk_msg = """                console.print("[yellow]To install tkinter:[/yellow]")
                if sys.platform == "darwin":
                    console.print("[yellow]  macOS: brew install python-tk[/yellow]")
                else:
                    console.print("[yellow]  Debian/Ubuntu: sudo apt install python3-tk[/yellow]")
                    console.print("[yellow]  Fedora: sudo dnf install python3-tkinter[/yellow]")
                    console.print("[yellow]  Arch Linux: sudo pacman -S tk[/yellow]")"""

content = content.replace(old_tk_msg, new_tk_msg)

with open("tsunami_notes/notes.py", "w") as f:
    f.write(content)
