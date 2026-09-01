import re
import os


def fix_hashing(filename):
    with open(filename, "r") as f:
        content = f.read()

    # Find the old hashlib code
    content = content.replace(
        "h = hashlib.sha256((salt + password).encode()).hexdigest()",
        "h = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000).hex()",
    )
    content = content.replace(
        "h = hashlib.sha256((salt + pwd).encode()).hexdigest()",
        "h = hashlib.pbkdf2_hmac('sha256', pwd.encode(), salt.encode(), 100000).hex()",
    )

    with open(filename, "w") as f:
        f.write(content)


fix_hashing("tsunami_notes/notes.py")
fix_hashing("tsunami_notes/gui.py")
fix_hashing("tsunami_notes/tui.py")
