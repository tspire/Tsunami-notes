import re

with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/notes.py",
    "r",
) as f:
    content = f.read()

run_cmd_code = """
    elif args.command == "duress-setup":
        duress_password = _prompt_password(
            confirm=True, prompt="New duress password/PIN: "
        )
        fake_vault_path = vault_path + ".fake"
        save_vault(fake_vault_path, duress_password, {"notes": []})
        print(f"Duress vault created at {fake_vault_path}.")

    elif args.command == "agent":
        from .agent import start_agent, stop_agent
        if args.agent_cmd == "start":
            start_agent()
        elif args.agent_cmd == "stop":
            stop_agent()

    elif args.command == "unlock":
        from .agent import set_password
        set_password(password)

    return modified, password
"""
content = content.replace(
    """    elif args.command == "duress-setup":
        duress_password = _prompt_password(
            confirm=True, prompt="New duress password/PIN: "
        )
        fake_vault_path = vault_path + ".fake"
        save_vault(fake_vault_path, duress_password, {"notes": []})
        print(f"Duress vault created at {fake_vault_path}.")

    return modified, password""",
    run_cmd_code,
)

with open(
    "/home/runner/work/Tsunami-notes-ubuntu/Tsunami-notes-ubuntu/tsunami_notes/notes.py",
    "w",
) as f:
    f.write(content)
