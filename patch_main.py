with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/notes.py",
    "r",
) as f:
    content = f.read()

main_code = """
    vault_path = args.vault
    is_new_vault = not os.path.exists(vault_path)

    # Try agent first if not interactive and not creating a new vault
    password = None
    if not is_new_vault:
        try:
            from .agent import get_password
            agent_pw = get_password()
            if agent_pw:
                password = agent_pw
        except ImportError:
            pass

    if not password:
        password = _prompt_password(confirm=is_new_vault)

    try:
"""
content = content.replace(
    """    vault_path = args.vault
    is_new_vault = not os.path.exists(vault_path)

    password = _prompt_password(confirm=is_new_vault)

    try:""",
    main_code,
)

with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/notes.py",
    "w",
) as f:
    f.write(content)
