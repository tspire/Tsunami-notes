def add_top(file):
    with open(file, "r") as f:
        content = f.read()
    if "import hashlib" not in content:
        content = content.replace("import os\n", "import os\nimport hashlib\n", 1)
    with open(file, "w") as f:
        f.write(content)


add_top("tsunami_notes/notes.py")
add_top("tsunami_notes/gui.py")
add_top("tsunami_notes/tui.py")
