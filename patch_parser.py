import re

with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/notes.py",
    "r",
) as f:
    content = f.read()

# Add to build_parser
parser_code = """
    sub.add_parser("duress-setup", help="Set up a duress PIN/password and fake vault.")

    agent_p = sub.add_parser("agent", help="Manage background password agent.")
    agent_p.add_argument("agent_cmd", choices=["start", "stop"], help="Start or stop the agent.")

    sub.add_parser("unlock", help="Cache the master password in the agent for this session.")

    return parser
"""
content = content.replace(
    '    sub.add_parser("duress-setup", help="Set up a duress PIN/password and fake vault.")\n\n    return parser',
    parser_code,
)

with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/notes.py",
    "w",
) as f:
    f.write(content)
