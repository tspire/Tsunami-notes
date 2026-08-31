with open("tsunami_notes/__init__.py", "r") as f:
    content = f.read()

content = content.replace("Tsunami Notes — a private, secure, encrypted notes app for Ubuntu.", "Tsunami Notes — a private, secure, encrypted notes app for macOS and Linux.")

with open("tsunami_notes/__init__.py", "w") as f:
    f.write(content)
