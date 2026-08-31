"""Audio playback utility for Tsunami Notes."""

import os
import glob

try:
    import pygame  # pylint: disable=import-error

    pygame.mixer.init()
    AUDIO_AVAILABLE = True
except Exception:  # pylint: disable=broad-exception-caught
    AUDIO_AVAILABLE = False

SOUND_FILES = {
    "zelda_secret": "zelda_secret.wav",
    "keyboard_click": "keyboard_click.wav",
    "mgs_alert": "mgs_alert.wav",
    "navi_listen": "navi_listen.wav",
}

_sounds = {}
CURRENT_AMBIENT = None


def play_sound(name):
    """Play a sound file by name."""
    if not AUDIO_AVAILABLE:
        return
    if name not in SOUND_FILES:
        return
    if name not in _sounds:
        sound_path = os.path.join(os.path.dirname(__file__), SOUND_FILES[name])
        if os.path.exists(sound_path):
            try:
                _sounds[name] = pygame.mixer.Sound(sound_path)
            except Exception:  # pylint: disable=broad-exception-caught
                return
        else:
            return
    try:
        _sounds[name].play()
    except Exception:  # pylint: disable=broad-exception-caught
        pass


def start_focus_mode(theme_name="default"):
    """Start ambient background loop for focus mode."""
    global CURRENT_AMBIENT  # pylint: disable=global-statement
    if not AUDIO_AVAILABLE:
        return

    if CURRENT_AMBIENT == theme_name and pygame.mixer.music.get_busy():
        return

    theme_dir = os.path.join(os.path.dirname(__file__), "themes", theme_name)
    if not os.path.exists(theme_dir):
        # Fallback to a default if theme doesn't exist
        theme_dir = os.path.join(os.path.dirname(__file__), "themes")

    # Find any wav file in the theme dir
    wav_files = glob.glob(os.path.join(theme_dir, "*.wav"))
    if not wav_files:
        return

    try:
        pygame.mixer.music.load(wav_files[0])
        pygame.mixer.music.play(-1)
        CURRENT_AMBIENT = theme_name
    except Exception:  # pylint: disable=broad-exception-caught
        pass


def stop_focus_mode():
    """Stop ambient background loop."""
    global CURRENT_AMBIENT  # pylint: disable=global-statement
    if not AUDIO_AVAILABLE:
        return
    try:
        pygame.mixer.music.stop()
        CURRENT_AMBIENT = None
    except Exception:  # pylint: disable=broad-exception-caught
        pass
