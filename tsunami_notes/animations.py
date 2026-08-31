"""Fullscreen terminal animations for various commands."""

import sys
import time
import random
import math
import shutil
from rich.live import Live
from rich.text import Text
from rich.align import Align
from rich.console import Console

# pylint: disable=unused-argument, unused-variable, anomalous-backslash-in-string, invalid-name

console = Console()


def play_fullscreen_anim(command: str, message: str) -> None:
    """Play a fullscreen animation mapped to the given command."""
    if not sys.stdout.isatty():
        console.print(f"[green]{message}[/green]")
        return

    width, height = shutil.get_terminal_size((80, 24))

    if command == "add":
        _anim_tsunami(width, height, message)
    elif command in ("edit", "update"):
        _anim_matrix(width, height, message)
    elif command in ("trash", "delete"):
        _anim_whirlpool(width, height, message)
    elif command == "empty-trash":
        _anim_incinerator(width, height, message)
    elif command == "restore":
        _anim_geyser(width, height, message)
    elif command == "export":
        _anim_submarine(width, height, message)
    elif command == "import":
        _anim_ufo(width, height, message)
    elif command == "passwd":
        _anim_lock(width, height, message)
    elif command == "duress":
        _anim_smoke(width, height, message)
    elif command in ("list", "search", "show", "list-trash", "view"):
        _anim_sonar(width, height, message)
    else:
        _anim_default(width, height, message)


def _anim_default(w, h, message):
    with Live(screen=True, refresh_per_second=10) as live:
        for _ in range(10):
            live.update(Align.center(Text(message, style="green"), vertical="middle"))
            time.sleep(0.1)


def _anim_tsunami(w, h, message):
    with Live(screen=True, refresh_per_second=20) as live:
        for i in range(w + 10):
            lines = []
            for y in range(h):
                line = ""
                for x in range(w):
                    if x < i - (h - y) * 2:
                        line += "~"
                    elif x < i - (h - y):
                        line += "≈"
                    else:
                        line += " "
                lines.append(line)
            live.update(Text("\n".join(lines), style="cyan"))
            time.sleep(0.02)
        live.update(Align.center(Text(message, style="bold green"), vertical="middle"))
        time.sleep(0.5)


def _anim_matrix(w, h, message):
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@#$%^&*"
    with Live(screen=True, refresh_per_second=20) as live:
        for frame in range(25):
            lines = []
            for y in range(h):
                line = ""
                for x in range(w):
                    if random.random() < 0.1 or frame > 15:
                        line += " "
                    else:
                        line += random.choice(chars)
                lines.append(line)
            live.update(Text("\n".join(lines), style="green"))
            time.sleep(0.05)
        live.update(Align.center(Text(message, style="bold green"), vertical="middle"))
        time.sleep(0.5)


def _anim_whirlpool(w, h, message):
    with Live(screen=True, refresh_per_second=20) as live:
        for i in range(25):
            lines = []
            for y in range(h):
                line = ""
                for x in range(w):
                    dx = x - w / 2
                    dy = y - h / 2
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist > i:
                        line += random.choice(["~", "@", "O", "o"])
                    else:
                        line += " "
                lines.append(line)
            live.update(Text("\n".join(lines), style="blue"))
            time.sleep(0.05)
        live.update(Align.center(Text(message, style="bold green"), vertical="middle"))
        time.sleep(0.5)


def _anim_incinerator(w, h, message):
    chars = ["@", "#", "*", "W", " ", " "]
    with Live(screen=True, refresh_per_second=20) as live:
        for frame in range(25):
            lines = []
            for y in range(h):
                line = ""
                for x in range(w):
                    if frame > 15:
                        line += random.choice([".", " ", " "])
                    else:
                        line += random.choice(chars)
                # Shaking effect
                if frame <= 15:
                    offset = random.randint(-1, 1)
                    if offset > 0:
                        line = " " * offset + line[:-offset]
                    elif offset < 0:
                        line = line[-offset:] + " " * (-offset)
                lines.append(line)
            live.update(
                Text("\n".join(lines), style="bold red" if frame <= 15 else "dim white")
            )
            time.sleep(0.05)
        live.update(Align.center(Text(message, style="bold green"), vertical="middle"))
        time.sleep(0.5)


def _anim_geyser(w, h, message):
    with Live(screen=True, refresh_per_second=20) as live:
        for i in range(h):
            lines = []
            for y in range(h):
                line = ""
                for x in range(w):
                    if w / 2 - i < x < w / 2 + i and y > h - i:
                        line += random.choice(["|", "~", "O", "o", " "])
                    else:
                        line += " "
                lines.append(line[:w])
            live.update(Text("\n".join(lines), style="cyan"))
            time.sleep(0.05)
        live.update(Align.center(Text(message, style="bold green"), vertical="middle"))
        time.sleep(0.5)


def _anim_submarine(w, h, message):
    sub = [
        "      _     ",
        "    _| |_   ",
        r"  /       \ ",
        " |_________|",
        r"  \_______/ ",
    ]
    with Live(screen=True, refresh_per_second=20) as live:
        for i in range(-15, w + 15):
            lines = [" " * w for _ in range(h)]
            for sy, sline in enumerate(sub):
                target_y = h // 2 + sy - 2
                target_x = i
                if 0 <= target_y < h:
                    pre = max(0, target_x)
                    post = max(0, w - target_x - len(sline))
                    visible = sline[max(0, -target_x) : max(0, w - target_x)]
                    lines[target_y] = (" " * pre) + visible + (" " * post)
                    if len(lines[target_y]) < w:
                        lines[target_y] += " " * (w - len(lines[target_y]))
                    lines[target_y] = lines[target_y][:w]
            live.update(Text("\n".join(lines), style="yellow"))
            time.sleep(0.05)
        live.update(Align.center(Text(message, style="bold green"), vertical="middle"))
        time.sleep(0.5)


def _anim_ufo(w, h, message):
    ufo = ["   ___   ", r" _/   \_ ", r"/_______\\"]
    with Live(screen=True, refresh_per_second=20) as live:
        for i in range(20):
            lines = [" " * w for _ in range(h)]
            for sy, sline in enumerate(ufo):
                target_y = 2 + sy
                target_x = w // 2 - len(sline) // 2
                if 0 <= target_y < h:
                    lines[target_y] = (
                        lines[target_y][:target_x]
                        + sline
                        + lines[target_y][target_x + len(sline) :]
                    )

            for beam_y in range(5, h):
                lines[beam_y] = (
                    lines[beam_y][: w // 2]
                    + (random.choice(["|", " "]))
                    + lines[beam_y][w // 2 + 1 :]
                )

            live.update(Text("\n".join(lines), style="cyan"))
            time.sleep(0.05)
        live.update(Align.center(Text(message, style="bold green"), vertical="middle"))
        time.sleep(0.5)


def _anim_lock(w, h, message):
    with Live(screen=True, refresh_per_second=20) as live:
        for i in range(25):
            lines = []
            for y in range(h):
                line = ""
                for x in range(w):
                    if w / 2 - 15 < x < w / 2 + 15 and h / 2 - 7 < y < h / 2 + 7:
                        line += str(random.randint(0, 9))
                    else:
                        line += " "
                lines.append(line)
            live.update(Text("\n".join(lines), style="red" if i < 15 else "green"))
            time.sleep(0.05)
        live.update(Align.center(Text(message, style="bold green"), vertical="middle"))
        time.sleep(0.5)


def _anim_smoke(w, h, message):
    chars = ["░", "▒", "▓", "█"]
    with Live(screen=True, refresh_per_second=20) as live:
        for frame in range(25):
            lines = []
            for y in range(h):
                line = ""
                for x in range(w):
                    if frame < 10:
                        line += random.choice(chars)
                    elif frame < 20:
                        line += random.choice(["░", " ", " "])
                    else:
                        line += " "
                lines.append(line)
            live.update(Text("\n".join(lines), style="white"))
            time.sleep(0.05)
        live.update(Align.center(Text(message, style="bold green"), vertical="middle"))
        time.sleep(0.5)


def _anim_sonar(w, h, message):
    dots = [(random.randint(0, w - 1), random.randint(0, h - 1)) for _ in range(30)]
    with Live(screen=True, refresh_per_second=20) as live:
        for angle in range(0, 360, 15):
            lines = []
            for y in range(h):
                line = ""
                for x in range(w):
                    dx = x - w / 2
                    dy = (y - h / 2) * 2
                    p_angle = math.degrees(math.atan2(dy, dx))
                    if p_angle < 0:
                        p_angle += 360
                    if abs(p_angle - angle) < 20 or (x, y) in dots:
                        line += "."
                    else:
                        line += " "
                lines.append(line)
            live.update(Text("\n".join(lines), style="green"))
            time.sleep(0.05)
        if message:
            live.update(
                Align.center(Text(message, style="bold green"), vertical="middle")
            )
            time.sleep(0.5)
