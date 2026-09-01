with open("tsunami_notes/notes.py", "r") as f:
    content = f.read()

content = content.replace(
    "if hashlib.sha256((salt + pwd).encode()).hexdigest() == h:",
    "if hashlib.pbkdf2_hmac('sha256', pwd.encode(), salt.encode(), 100000).hex() == h:",
)

with open("tsunami_notes/notes.py", "w") as f:
    f.write(content)
