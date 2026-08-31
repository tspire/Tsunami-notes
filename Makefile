PYTHON ?= python3
VENV ?= .venv
VENV_BIN := $(VENV)/bin
DEV_STAMP := $(VENV)/.dev-installed

OPT_DIR ?= /opt/tsunami
BIN_DIR ?= /usr/local/bin

.PHONY: help venv dev run test black lint build install uninstall clean

.DEFAULT_GOAL := help

help:
	@echo "Tsunami Notes — development & installation targets"
	@echo ""
	@echo "  make venv          Create .venv and install the app in editable mode"
	@echo "  make dev           Install dev tools (requirements.dev.txt) into .venv"
	@echo "  make run ARGS=...  Run the app inside .venv (e.g. ARGS=\"list\")"
	@echo "  make test          Run lint (black + pylint), then unit tests"
	@echo "  make black         Format code with black"
	@echo "  make lint          Run black, then pylint"
	@echo "  make build         Build a wheel into dist/"
	@echo "  make install       Install to $(OPT_DIR) + wrapper in $(BIN_DIR)/tsunami (run as root)"
	@echo "  make uninstall     Remove the wrapper and $(OPT_DIR) (run as root)"
	@echo "  make clean         Remove .venv and build artifacts"
	@echo ""

venv: $(VENV_BIN)/activate

$(VENV_BIN)/activate:
	$(PYTHON) -m venv $(VENV)
	$(VENV_BIN)/python -m pip install --upgrade pip
	$(VENV_BIN)/pip install -e .

dev: $(DEV_STAMP)

$(DEV_STAMP): $(VENV_BIN)/activate requirements.dev.txt
	$(VENV_BIN)/pip install -r requirements.dev.txt
	touch $(DEV_STAMP)

run: venv
	$(VENV_BIN)/tsunami $(ARGS)

test: lint
	$(VENV_BIN)/python -m unittest test_notes -v

black: dev
	$(VENV_BIN)/black .

lint: black
	$(VENV_BIN)/pylint tsunami_notes

build: venv
	PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 $(VENV_BIN)/pip wheel --no-deps --wheel-dir dist .

install:
	install -d -m 755 "$(OPT_DIR)"
	install -d -m 755 "$(BIN_DIR)"
	$(PYTHON) -m venv "$(OPT_DIR)/venv"
	"$(OPT_DIR)/venv/bin/python" -m pip install --upgrade pip
	PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 "$(OPT_DIR)/venv/bin/pip" install .
	printf '%s\n' '#!/bin/sh' 'exec "$(OPT_DIR)/venv/bin/tsunami" "$$@"' > "$(BIN_DIR)/tsunami"
	chmod 755 "$(BIN_DIR)/tsunami"

uninstall:
	rm -f "$(BIN_DIR)/tsunami"
	rm -rf "$(OPT_DIR)"

clean:
	rm -rf $(VENV) build dist *.egg-info
