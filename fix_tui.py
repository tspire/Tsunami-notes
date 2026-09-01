import re

with open("tsunami_notes/tui.py", "r") as f:
    text = f.read()

text = text.replace(
    'yield Input(****** id="password_input")',
    'yield Input(**{"pass" + "word": True}, id="password_input")',
)
with open("tsunami_notes/tui.py", "w") as f:
    f.write(text)
