# AGENTS.md — Tsunami Notes (Ubuntu)

Guidance for AI agents (and humans) continuing work on this repository.
The primary author/requester communicates in Norwegian; the codebase, docs,
and this file are in English.

## What this project is

A private, encrypted command-line notes app for Ubuntu, written in Python.

- Encryption: AES-256-GCM (authenticated), key derived with Scrypt.
- Fresh salt + nonce on every save; the vault is re-encrypted from scratch each time.
- Atomic writes via `os.replace`; vault file permissions `0600`.
- Default vault path: `~/.tsunami_notes`.
- Installed command: `tsunami` (e.g. `tsunami add "foo" "var"`).

## Repository layout

```
.
├── Makefile               # all dev / build / install targets
├── pyproject.toml         # packaging, prod deps, console script, tool config
├── requirements.dev.txt   # dev-only deps (black, pylint)
├── README.md              # user-facing docs
├── test_notes.py          # unittest suite (18 tests)
├── .gitignore
└── tsunami_notes/
    ├── __init__.py        # __version__ = "0.1.0"
    └── notes.py           # crypto + note helpers + CLI (single module)
```

The CLI logic lives entirely in `tsunami_notes/notes.py`. Naming:

- import package: `tsunami_notes` (underscore)
- pip distribution: `tsunami-notes` (hyphen)
- console-script command: `tsunami`

Ignored build artifacts (not part of the source): `.venv/`, `__pycache__/`,
`build/`, `dist/`, `*.egg-info/`.

## Requirements the user gave (paraphrased, in order)

1. Add a `Makefile` that creates a `.venv` to run the app.
2. Make it build an installable pip package so the app becomes a command in a
   `bin` dir (`.local` or `/usr/local`).
3. The app must install into `/opt/tsunami` (its own virtualenv) with a wrapper
   at `/usr/local/bin/tsunami`, so `tsunami add foo "var"` works.
4. Add a `black` target and a `lint` target; `lint` must depend on `black` and
   then run `pylint`.
5. Dev dependencies go in `requirements.dev.txt` (NOT the standard/removed
   `requirements.txt`); keep dev and prod requirements generally separated.
6. `test` must depend on `lint` (so it runs black + pylint before the tests).

## Key decisions / conventions

- Console script: `tsunami = "tsunami_notes.notes:main"` (in `pyproject.toml`).
- `prog="tsunami"` in `argparse` (matches the installed command).
- `[tool.black] target-version = ["py310"]` to match `requires-python = ">=3.10"`.
  Required because black 26.x defaults to the newest Python target, and its
  safety check then fails on older interpreters (e.g. Python 3.14).
- Prod deps in `pyproject.toml` → `[project].dependencies`; dev deps in
  `requirements.dev.txt`.
- `make dev` installs dev deps into `.venv` and records a stamp at
  `$(VENV)/.dev-installed`, so it only reinstalls when `requirements.dev.txt`
  or the venv changes.
- Install wrapper (written to `$(BIN_DIR)/tsunami`):

  ```sh
  #!/bin/sh
  exec "/opt/tsunami/venv/bin/tsunami" "$@"
  ```

## Makefile targets

| Target | Effect |
|--------|--------|
| `make venv` | create `.venv` and install the app in editable mode |
| `make dev` | install dev tools (`requirements.dev.txt`) into `.venv` |
| `make run ARGS="..."` | run the app inside `.venv` |
| `make black` | format code with black |
| `make lint` | black, then pylint |
| `make test` | lint (black + pylint), then unit tests |
| `make build` | build a wheel into `dist/` |
| `make install` | install to `/opt/tsunami` + wrapper in `/usr/local/bin/tsunami` (root) |
| `make uninstall` | remove wrapper + `/opt/tsunami` (root) |
| `make clean` | remove `.venv`, `build/`, `dist/`, `*.egg-info` |

Dependency chain: `test → lint → black → dev → .venv`.

## Lessons learned / gotchas

- The original repo had a typo'd `.gitigonore`; it was replaced with `.gitignore`.
- `notes.py` was originally a single top-level script; it was MOVED into
  `tsunami_notes/notes.py`, and `test_notes.py` now imports
  `from tsunami_notes.notes import ...`.
- `requirements.txt` was deleted — the prod dependency (`cryptography`) now lives
  in `pyproject.toml`.
- Removed the shebang from `tsunami_notes/notes.py` (it is now an importable
  module, not an executable script).
- Removed an unused `import base64` and added docstrings to the public functions
  so `pylint` scores 10/10.
- `make install` must create `$(BIN_DIR)` as well as `$(OPT_DIR)` (an earlier
  version assumed `/usr/local/bin` already existed).
- In sandboxed/restricted CI environments, black's multiprocessing
  (`forkserver`) can be blocked (`PermissionError`); workaround is `black -W 1 .`.
  Not an issue on normal machines.
- Python 3.14 + PEP 668: a plain system `pip install` may require
  `--break-system-packages`; the app sidesteps this by installing into its own
  venv under `/opt/tsunami`.

## How to validate

```bash
make test                 # black + pylint + 18 unit tests (all pass)
make lint                 # black + pylint (pylint = 10.00/10)
make build                # produces dist/tsunami_notes-0.1.0-py3-none-any.whl
```

Test the install flow without root:

```bash
make install OPT_DIR=/tmp/tsunami-opt-test BIN_DIR=/tmp/tsunami-bin-test
/tmp/tsunami-bin-test/tsunami --help
```

## Known non-blocking issues

- A type checker (pyright/pylance) still flags `dict` annotations without type
  arguments and some `argparse` return values. These are pre-existing, do not
  affect runtime or tests, and could be addressed later by adding type hints
  (e.g. a `TypedDict` for a note/vault).
- Dev dependency versions are `>=` floors, not pinned. Pin to `==` if strict
  reproducibility is desired.

## Likely next steps

- Add type hints / a `TypedDict` for the vault/note structure to silence the
  type-checker warnings, if desired.
- Pin dev dependency versions.
- Add `[tool.pylint]` config if custom lint rules are wanted.
- Add CI (e.g. run `make lint` and `make test`).
