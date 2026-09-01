with open("tsunami_notes/tui.py", "r") as f:
    lines = f.readlines()

# Remove all hashlib and os imports
lines = [l for l in lines if not l.startswith("import hashlib")]
lines = [l for l in lines if not l.startswith("import os")]

# Insert hashlib right after the docstring
lines.insert(2, "import hashlib\n")

with open("tsunami_notes/tui.py", "w") as f:
    f.writelines(lines)
