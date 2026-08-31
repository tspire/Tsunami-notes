import re

with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/animations.py",
    "r",
) as f:
    content = f.read()

content = content.replace("w, h, message", "_w, _h, message")
content = content.replace("for y in range(h):", "for _y in range(h):")
content = content.replace("for x in range(w):", "for _x in range(w):")
# some need x and y
content = content.replace(
    'for _y in range(h):\n                line = ""\n                for _x in range(w):\n                    dx = _x - w/2\n                    dy = _y - h/2',
    'for y in range(h):\n                line = ""\n                for x in range(w):\n                    dx = x - w/2\n                    dy = y - h/2',
)
content = content.replace(
    'for _y in range(h):\n                line = ""\n                for _x in range(w):\n                    if x < i - (h-_y)*2:',
    'for y in range(h):\n                line = ""\n                for x in range(w):\n                    if x < i - (h-y)*2:',
)

content = content.replace("from rich.panel import Panel\n", "")
content = content.replace("from rich.table import Table\n", "")
content = content.replace('" _/   \\_ "', 'r" _/   \_ "')

# Prepend docstrings
content = '"""Fullscreen terminal animations for various commands."""\n' + content

content = content.replace(
    "def play_fullscreen_anim(command: str, message: str) -> None:\n",
    'def play_fullscreen_anim(command: str, message: str) -> None:\n    """Play a fullscreen animation mapped to the given command."""\n',
)

with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/animations.py",
    "w",
) as f:
    f.write(content)
