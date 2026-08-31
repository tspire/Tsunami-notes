with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/agent.py",
    "r",
) as f:
    content = f.read()

content = "# pylint: disable=unspecified-encoding,import-outside-toplevel\n" + content
with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/agent.py",
    "w",
) as f:
    f.write(content)

with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/notes.py",
    "r",
) as f:
    content = f.read()

content = content.replace(
    "from .agent import start_agent, stop_agent",
    "# pylint: disable=import-outside-toplevel\n        from .agent import start_agent, stop_agent",
)
with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/notes.py",
    "w",
) as f:
    f.write(content)
