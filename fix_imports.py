import re

for filename in [
    "tsunami_notes/notes.py",
    "tsunami_notes/gui.py",
    "tsunami_notes/tui.py",
]:
    with open(filename, "r") as f:
        content = f.read()

    if filename == "tsunami_notes/gui.py" or filename == "tsunami_notes/tui.py":
        if "import hashlib" not in content[:500]:
            content = content.replace("import os\n", "import os\nimport hashlib\n", 1)

    content = content.replace("                    import hashlib\n", "")
    content = content.replace("                    import os\n", "")
    content = content.replace("                import hashlib\n", "")
    content = content.replace("                import os\n", "")
    content = content.replace("    import hashlib\n", "")
    content = content.replace("    import os\n", "")
    content = content.replace("        import hashlib, os\n", "")

    with open(filename, "w") as f:
        f.write(content)
