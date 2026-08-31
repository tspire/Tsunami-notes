with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/agent.py",
    "r",
) as f:
    content = f.read()

# Fix unspecified-encoding
content = content.replace(
    "with open(os.devnull, 'r') as f:",
    "with open(os.devnull, 'r', encoding='utf-8') as f:",
)
content = content.replace(
    "with open(os.devnull, 'a+') as f:",
    "with open(os.devnull, 'a+', encoding='utf-8') as f:",
)

# Fix broad-exception-caught by disabling pylint for those lines
content = content.replace(
    "except Exception:", "except Exception:  # pylint: disable=broad-exception-caught"
)

# Fix no-else-return
content = content.replace(
    """        if send_to_agent("GET") is not None:
            print("Agent is already running.")
            return
        else:
            # Stale socket
            os.remove(SOCKET_PATH)""",
    """        if send_to_agent("GET") is not None:
            print("Agent is already running.")
            return
        # Stale socket
        os.remove(SOCKET_PATH)""",
)

# Fix import outside toplevel
content = content.replace(
    "        import time\n        time.sleep(0.2)",
    "        import time  # pylint: disable=import-outside-toplevel\n        time.sleep(0.2)",
)

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
    "from .agent import start_agent, stop_agent  # pylint: disable=import-outside-toplevel",
)
content = content.replace(
    "from .agent import set_password",
    "from .agent import set_password  # pylint: disable=import-outside-toplevel",
)
content = content.replace(
    "from .agent import get_password",
    "from .agent import get_password  # pylint: disable=import-outside-toplevel",
)

content = content.replace(
    "def _run_command(args, vault, vault_path, password) -> tuple[bool, str]:",
    "# pylint: disable=too-many-locals\ndef _run_command(args, vault, vault_path, password) -> tuple[bool, str]:",
)

with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/notes.py",
    "w",
) as f:
    f.write(content)
