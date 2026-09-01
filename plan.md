## Implementation Plan

1.  **Auto-Lock Timeout**:
    *   In `gui.py`: Add an inactivity timer (using `after()`) that resets on key/mouse events. When it times out, destroy the main window and re-prompt for the password using a lock screen window or standard prompt.
    *   In `tui.py`: Add a similar inactivity timer using Textual's timer capabilities.
2.  **Duress / Self-Destruct Password**:
    *   In `notes.py` (`load_vault` or in the `crypto.py` loading logic/CLI): Add a feature where checking if the password matches a separate "duress password" hash stored alongside the normal salt. Actually, since the vault is just encrypted, we might need a separate mechanism to store a duress hash, or just have a flag. The simplest way is to check the password against a duress hash file, and if it matches, overwrite the vault with random data and exit.
    *   Or, during vault creation, allow setting a duress password.
3.  **Markdown Support**:
    *   In `gui.py`: The `body_text` widget is a standard `tk.Text`. We can't render Markdown easily natively. However, we could use a library like `tkhtmlview` or simple tags (bold, italic) parsed from markdown. Wait, `notes.py` already uses `rich.markdown.Markdown` for the CLI. For `tk.Text`, we could add simple regex-based highlighting for basic markdown (e.g., `**bold**`, `*italic*`) and apply tags.
4.  **Global Search & Filter**:
    *   In `gui.py`: Add a Search Entry at the top (in the toolbar). Bind to its string var to filter the `listbox`.
5.  **Theme Packs**:
    *   In `audio.py`: The `play_sound` function currently looks for specific `.wav` files. We can add a `THEME` setting to choose a subdirectory of sounds (e.g., `sounds/zelda/`, `sounds/mgs/`).
6.  **Typing Soundscapes**:
    *   In `gui.py`: The `_on_key_press` already has `keyboard_sound_enabled`. We can expand this to play an ambient sound in a loop, or just change the sounds.
7.  **Trash Bin**:
    *   In `notes.py`: Instead of `notes.pop(index)`, move the note to a `trash` list inside the vault JSON. Add commands to list trash, restore from trash, and empty trash.
8.  **Note Revisions**:
    *   In `notes.py`: Inside the note object in the vault JSON, add a `revisions` array containing past bodies/titles and timestamps whenever a note is edited.

Since this is a lot, I will take it step by step.
