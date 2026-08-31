"""Audio playback utility for Tsunami Notes."""

import os

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
