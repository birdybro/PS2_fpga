.DEFAULT_GOAL := help

PYTHON ?= python3
VERILATOR ?= verilator
VERILATOR_FLAGS ?=
BUILD_DIR ?= build
RANDOM_SEED ?= 1
VENV ?= .venv

SMOKE_RTL := rtl/common/register_en.sv
SMOKE_MDIR := $(BUILD_DIR)/verilator_smoke
VENV_PYTHON := $(VENV)/bin/python
VENV_STAMP := $(VENV)/.requirements-dev.stamp

.PHONY: help venv structure build lint test unit differential randomized integration regression software waves clean

help: ## Show available development commands.
	@awk 'BEGIN {FS = ":.*## "; printf "PS2_fpga development commands:\n\n"} /^[a-zA-Z0-9_-]+:.*## / {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

venv: $(VENV_STAMP) ## Create the pinned local Python verification environment.

$(VENV_STAMP): requirements-dev.txt
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --requirement requirements-dev.txt
	@touch $(VENV_STAMP)

structure: ## Verify required repository subsystem boundaries.
	@$(PYTHON) scripts/check_structure.py

build: $(SMOKE_MDIR)/Vregister_en__ALL.a ## Compile the current synthesizable RTL smoke model.

$(SMOKE_MDIR)/Vregister_en__ALL.a: $(SMOKE_RTL)
	@mkdir -p $(SMOKE_MDIR)
	$(VERILATOR) --cc --build --Mdir $(SMOKE_MDIR) \
		--top-module register_en --prefix Vregister_en \
		-Wall $(VERILATOR_FLAGS) $(SMOKE_RTL)

lint: structure ## Run the currently available static repository checks.
	@git diff HEAD --check -- .

test: structure build venv ## Run the routine pytest gate.
	@mkdir -p $(BUILD_DIR)/results
	RANDOM_SEED="$(RANDOM_SEED)" PS2_BUILD_ROOT="$(abspath $(BUILD_DIR))" \
		$(VENV_PYTHON) -m pytest \
		--junitxml="$(abspath $(BUILD_DIR))/results/pytest.xml"
	@echo "routine tests: PASS"

unit: venv ## Run directed unit tests.
	@mkdir -p $(BUILD_DIR)/results
	RANDOM_SEED="$(RANDOM_SEED)" PS2_BUILD_ROOT="$(abspath $(BUILD_DIR))" \
		$(VENV_PYTHON) -m pytest tests/unit/test_register_en_runner.py \
		--junitxml="$(abspath $(BUILD_DIR))/results/pytest-unit.xml"

differential: ## Run differential tests (introduced with reference models).
	@echo "differential tests are not implemented yet" >&2
	@exit 2

randomized: ## Run deterministic randomized tests (introduced by M008).
	@echo "randomized tests are not available until milestone M008" >&2
	@exit 2

integration: ## Run integration tests (introduced as subsystems connect).
	@echo "integration tests are not implemented yet" >&2
	@exit 2

regression: test ## Run the authoritative pre-commit regression gate.
	@echo "bootstrap regression: PASS"

software: ## Build legal project test software when a cross-toolchain is configured.
	@echo "software builds are not implemented yet" >&2
	@exit 2

waves: ## Run a trace-enabled test (introduced by M009).
	@echo "waveform generation is not available until milestone M009" >&2
	@exit 2

clean: ## Remove ignored local build outputs.
	@rm -rf -- build obj_dir sim_build
