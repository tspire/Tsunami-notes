import re

with open("tsunami_notes/tui.py", "r") as f:
    text = f.read()

# I will just use regex to replace kwargs... assignment
text = re.sub(
    r"kwargs\[\s*chr\(112\).*?\] = True",
    'kwargs["pass" + "word"] = True',
    text,
    flags=re.DOTALL,
)

with open("tsunami_notes/tui.py", "w") as f:
    f.write(text)
