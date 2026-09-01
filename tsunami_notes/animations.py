"""Short, command-specific terminal animations for the CLI."""

import math
import os
import random
import shutil
import sys
import time
from collections.abc import Callable

from rich.align import Align
from rich.console import Console, RenderableType
from rich.live import Live
from rich.text import Text

console = Console()

FrameBuilder = Callable[[int, int, int, int], RenderableType]

_DISABLED_VALUES = {"0", "false", "no", "off"}
_FRAME_COUNT = 14
_FRAME_DELAY = 0.035
_RESULT_DELAY = 0.2


def play_fullscreen_anim(command: str, message: str) -> None:
    """Play the animation mapped to *command* and print its result message."""
    if not _animations_enabled():
        _print_result(message)
        return

    width, height = shutil.get_terminal_size((80, 24))
    width = max(20, min(width, 100))
    height = max(8, min(height - 1, 28))
    builder, style = _animation_for(command)

    try:
        with Live(
            console=console,
            screen=True,
            auto_refresh=False,
            transient=True,
        ) as live:
            for frame in range(_FRAME_COUNT):
                renderable = builder(width, height, frame, _FRAME_COUNT)
                live.update(Align.center(renderable, vertical="middle"), refresh=True)
                time.sleep(_FRAME_DELAY)

            if message:
                result = Text(f"✓  {message}", style=f"bold {style}")
                live.update(Align.center(result, vertical="middle"), refresh=True)
                time.sleep(_RESULT_DELAY)
    except (KeyboardInterrupt, OSError):
        pass

    _print_result(message)


def _animations_enabled() -> bool:
    setting = os.environ.get("TSUNAMI_ANIMATIONS", "1").strip().lower()
    return (
        setting not in _DISABLED_VALUES
        and os.environ.get("TERM", "") != "dumb"
        and sys.stdout.isatty()
    )


def _print_result(message: str) -> None:
    if message:
        console.print(f"[bold green]✓[/bold green] {message}")


def _animation_for(command: str) -> tuple[FrameBuilder, str]:
    animations = {
        "add": (_wave_frame, "cyan"),
        "edit": (_matrix_frame, "green"),
        "update": (_matrix_frame, "green"),
        "trash": (_vortex_frame, "red"),
        "delete": (_vortex_frame, "red"),
        "empty-trash": (_vortex_frame, "red"),
        "restore": (_restore_frame, "cyan"),
        "export": (_transfer_frame, "magenta"),
        "import": (_transfer_frame, "magenta"),
        "passwd": (_lock_frame, "green"),
        "duress": (_smoke_frame, "white"),
        "list": (_sonar_frame, "green"),
        "search": (_sonar_frame, "green"),
        "show": (_sonar_frame, "green"),
        "list-trash": (_sonar_frame, "green"),
        "view": (_sonar_frame, "green"),
    }
    return animations.get(command, (_pulse_frame, "cyan"))


def _canvas(width: int, height: int) -> list[list[str]]:
    return [[" " for _ in range(width)] for _ in range(height)]


def _text_canvas(canvas: list[list[str]], style: str) -> Text:
    return Text("\n".join("".join(row) for row in canvas), style=style)


def _wave_frame(width: int, height: int, frame: int, total: int) -> Text:
    canvas = _canvas(width, height)
    progress = (frame + 1) / total
    crest = int(progress * (width + 12)) - 6
    baseline = height * 2 // 3

    for x_pos in range(width):
        ripple = int(math.sin((x_pos - frame * 2) / 3) * 1.5)
        y_pos = baseline + ripple
        if 0 <= y_pos < height:
            canvas[y_pos][x_pos] = "≈"
        if x_pos < crest:
            for fill_y in range(max(0, y_pos + 1), height):
                canvas[fill_y][x_pos] = "~"

    for offset in range(6):
        x_pos = crest - offset
        y_pos = baseline - int(math.sqrt(max(0, 12 * offset)))
        if 0 <= x_pos < width and 0 <= y_pos < height:
            canvas[y_pos][x_pos] = "◢" if offset < 2 else "≈"
    return _text_canvas(canvas, "bold cyan")


def _matrix_frame(width: int, height: int, frame: int, total: int) -> Text:
    del total
    canvas = _canvas(width, height)
    chars = "TSUNAMI0123456789"
    spacing = max(3, width // 18)

    for column in range(0, width, spacing):
        head = (frame * 2 + column * 3) % (height + 6)
        for trail in range(5):
            y_pos = head - trail
            if 0 <= y_pos < height:
                canvas[y_pos][column] = chars[(column + frame - trail) % len(chars)]
    return _text_canvas(canvas, "green")


def _vortex_frame(width: int, height: int, frame: int, total: int) -> Text:
    canvas = _canvas(width, height)
    center_x, center_y = width / 2, height / 2
    max_radius = min(width / 2, height)
    progress = frame / max(1, total - 1)

    for point in range(90):
        radius = max_radius * ((point / 90 + progress) % 1)
        angle = point * 0.6 + frame * 0.7
        x_pos = int(center_x + math.cos(angle) * radius * 2)
        y_pos = int(center_y + math.sin(angle) * radius)
        if 0 <= x_pos < width and 0 <= y_pos < height:
            canvas[y_pos][x_pos] = "·" if radius > max_radius / 2 else "◦"
    return _text_canvas(canvas, "bold red")


def _restore_frame(width: int, height: int, frame: int, total: int) -> Text:
    canvas = _canvas(width, height)
    progress = frame / max(1, total - 1)
    peak = height - 1 - int(progress * (height - 2))
    spread = max(1, int(progress * min(12, width // 4)))
    center = width // 2

    for y_pos in range(peak, height):
        distance = y_pos - peak
        half_width = min(spread, distance + 1)
        for x_pos in range(center - half_width, center + half_width + 1):
            if 0 <= x_pos < width and (x_pos + y_pos + frame) % 3:
                canvas[y_pos][x_pos] = random.choice(("│", "·", "•"))
    canvas[peak][center] = "▲"
    return _text_canvas(canvas, "bold cyan")


def _transfer_frame(  # pylint: disable=too-many-locals
    width: int, height: int, frame: int, total: int
) -> Text:
    canvas = _canvas(width, height)
    left, right = width // 4, width * 3 // 4
    y_pos = height // 2

    for x_pos in range(left, right + 1):
        canvas[y_pos][x_pos] = "─"
    canvas[y_pos][left] = "◆"
    canvas[y_pos][right] = "◆"

    progress = frame / max(1, total - 1)
    packet = left + int(progress * (right - left))
    canvas[y_pos][packet] = "●"
    if y_pos > 1:
        label = f" {int(progress * 100):3d}% "
        start = max(0, width // 2 - len(label) // 2)
        canvas[y_pos - 2][start : start + len(label)] = label
    return _text_canvas(canvas, "bold magenta")


def _lock_frame(  # pylint: disable=too-many-locals
    width: int, height: int, frame: int, total: int
) -> Text:
    canvas = _canvas(width, height)
    center_x, center_y = width // 2, height // 2
    unlocked = frame < total // 2
    lock = [
        "      ╭───╮" if unlocked else "  ╭─────╮  ",
        "      │    " if unlocked else "  │     │  ",
        "╭─┴─────┴─╮",
        "│    ◆    │",
        "╰─────────╯",
    ]
    start_y = center_y - len(lock) // 2
    start_x = center_x - len(lock[0]) // 2
    for row_index, line in enumerate(lock):
        y_pos = start_y + row_index
        if 0 <= y_pos < height:
            for column, char in enumerate(line):
                x_pos = start_x + column
                if 0 <= x_pos < width:
                    canvas[y_pos][x_pos] = char
    return _text_canvas(canvas, "yellow" if unlocked else "bold green")


def _smoke_frame(width: int, height: int, frame: int, total: int) -> Text:
    canvas = _canvas(width, height)
    fade = 1 - frame / total
    count = int(width * height * 0.08 * fade)
    chars = ("░", "▒", "▓")

    for point in range(count):
        x_pos = (point * 37 + frame * 11) % width
        y_pos = (point * 19 - frame * 2) % height
        canvas[y_pos][x_pos] = chars[(point + frame) % len(chars)]
    return _text_canvas(canvas, "dim white")


def _sonar_frame(width: int, height: int, frame: int, total: int) -> Text:
    canvas = _canvas(width, height)
    center_x, center_y = width // 2, height // 2
    radius = min(width // 3, height - 2)
    angle = frame / total * math.tau

    for ring in range(3, radius + 1, 4):
        for degree in range(0, 360, 8):
            radians = math.radians(degree)
            x_pos = int(center_x + math.cos(radians) * ring * 2)
            y_pos = int(center_y + math.sin(radians) * ring)
            if 0 <= x_pos < width and 0 <= y_pos < height:
                canvas[y_pos][x_pos] = "·"

    for distance in range(radius + 1):
        x_pos = int(center_x + math.cos(angle) * distance * 2)
        y_pos = int(center_y + math.sin(angle) * distance)
        if 0 <= x_pos < width and 0 <= y_pos < height:
            canvas[y_pos][x_pos] = "•"
    canvas[center_y][center_x] = "◉"
    return _text_canvas(canvas, "green")


def _pulse_frame(width: int, height: int, frame: int, total: int) -> Text:
    canvas = _canvas(width, height)
    center_x, center_y = width // 2, height // 2
    radius = 1 + int((frame / total) * min(width // 4, height // 2))

    for degree in range(0, 360, 5):
        radians = math.radians(degree)
        x_pos = int(center_x + math.cos(radians) * radius * 2)
        y_pos = int(center_y + math.sin(radians) * radius)
        if 0 <= x_pos < width and 0 <= y_pos < height:
            canvas[y_pos][x_pos] = "•"
    return _text_canvas(canvas, "bold cyan")
