# pylint: disable=unspecified-encoding,import-outside-toplevel
"""Background agent for caching the master password."""

import os
import sys
import socket
import atexit

SOCKET_PATH = os.path.join(os.path.expanduser("~"), ".tsunami_agent.sock")


def daemonize():
    """Double fork to daemonize."""
    try:
        if os.fork() > 0:
            sys.exit(0)
    except OSError as e:
        print(f"fork #1 failed: {e}")
        sys.exit(1)

    os.setsid()

    try:
        if os.fork() > 0:
            sys.exit(0)
    except OSError as e:
        print(f"fork #2 failed: {e}")
        sys.exit(1)

    sys.stdout.flush()
    sys.stderr.flush()
    with open(os.devnull, "r") as f:
        os.dup2(f.fileno(), sys.stdin.fileno())
    with open(os.devnull, "a+") as f:
        os.dup2(f.fileno(), sys.stdout.fileno())
        os.dup2(f.fileno(), sys.stderr.fileno())


def run_agent():
    """Run the background agent loop."""
    daemonize()

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o600)
    server.listen(1)

    # Clean up socket on exit
    def cleanup():
        if os.path.exists(SOCKET_PATH):
            os.remove(SOCKET_PATH)

    atexit.register(cleanup)

    cached_password = ""

    while True:
        try:
            conn, _ = server.accept()
            data = conn.recv(4096).decode("utf-8")
            if data == "GET":
                conn.sendall(cached_password.encode("utf-8"))
            elif data.startswith("SET "):
                cached_password = data[4:]
                conn.sendall(b"OK")
            elif data == "STOP":
                conn.sendall(b"OK")
                conn.close()
                break
            conn.close()
        except Exception:  # pylint: disable=broad-exception-caught
            pass

    cleanup()


def send_to_agent(msg: str) -> str | None:
    """Send message to agent and return response. Returns None if agent not reachable."""
    if not os.path.exists(SOCKET_PATH):
        return None
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(SOCKET_PATH)
        client.sendall(msg.encode("utf-8"))
        resp = client.recv(4096).decode("utf-8")
        client.close()
        return resp
    except Exception:  # pylint: disable=broad-exception-caught
        return None


def start_agent():
    """Start the background agent if not running."""
    if os.path.exists(SOCKET_PATH):
        if send_to_agent("GET") is not None:
            print("Agent is already running.")
            return
        # Stale socket
        os.remove(SOCKET_PATH)
    print("Starting tsunami agent...")
    pid = os.fork()
    if pid == 0:
        run_agent()
        sys.exit(0)
    else:
        import time

        time.sleep(0.2)


def stop_agent():
    """Stop the background agent."""
    resp = send_to_agent("STOP")
    if resp == "OK":
        print("Agent stopped.")
    else:
        print("Agent not running.")


def set_password(password: str):
    """Cache the password in the agent."""
    if not os.path.exists(SOCKET_PATH):
        start_agent()
    resp = send_to_agent(f"SET {password}")
    if resp == "OK":
        print("Password cached in agent.")


def get_password() -> str | None:
    """Retrieve the cached password from the agent."""
    resp = send_to_agent("GET")
    return resp if resp else None
