import re

with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/notes.py",
    "r",
) as f:
    content = f.read()

content = content.replace("def def _play_animation_removed", "def _old_play_animation")
content = re.sub(r"def _old_play_animation.*?\n\n\n", "", content, flags=re.DOTALL)
content = content.replace(
    "from rich.text import Text\n\nconsole = Console()",
    "from rich.text import Text\nfrom tsunami_notes.animations import play_fullscreen_anim\n\nconsole = Console()",
)

content = content.replace(
    "_play_animation(f\"Note '{title}' added.\")",
    'play_fullscreen_anim("add", f"Note \'{title}\' added.")',
)
content = content.replace(
    '_play_animation(f"Note {index} updated.")',
    'play_fullscreen_anim("edit", f"Note {index} updated.")',
)
content = content.replace(
    "_play_animation(f\"Note '{removed.get('title', '')}' moved to trash.\")",
    "play_fullscreen_anim(\"trash\", f\"Note '{removed.get('title', '')}' moved to trash.\")",
)
content = content.replace(
    "_play_animation(f\"Note '{restored.get('title', '')}' restored.\")",
    "play_fullscreen_anim(\"restore\", f\"Note '{restored.get('title', '')}' restored.\")",
)
content = content.replace(
    '_play_animation(f"Emptied {count} notes from trash.")',
    'play_fullscreen_anim("empty-trash", f"Emptied {count} notes from trash.")',
)
content = content.replace(
    '_play_animation(f"Vault exported to {path}.")',
    'play_fullscreen_anim("export", f"Vault exported to {path}.")',
)
content = content.replace(
    '_play_animation(f"Imported {len(imported_notes)} notes from {path}.")',
    'play_fullscreen_anim("import", f"Imported {len(imported_notes)} notes from {path}.")',
)
content = content.replace(
    '_play_animation("Master password changed.")',
    'play_fullscreen_anim("passwd", "Master password changed.")',
)
content = content.replace(
    '_play_animation(f"Duress vault created at {fake_vault_path}.")',
    'play_fullscreen_anim("duress", f"Duress vault created at {fake_vault_path}.")',
)

with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/notes.py",
    "w",
) as f:
    f.write(content)
