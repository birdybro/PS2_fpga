.DEFAULT_GOAL := help

PYTHON ?= python3
VERILATOR ?= verilator
VERILATOR_FLAGS ?=
BUILD_DIR ?= build
RANDOM_SEED ?= 1
VENV ?= .venv

SMOKE_RTL := rtl/common/register_en.sv
SMOKE_MDIR := $(BUILD_DIR)/verilator_smoke
RTL_SOURCES := $(shell find rtl -type f -name '*.sv' -print | sort)
MEMORY_BUS_PROTOCOL_LINT_TOP := tests/unit/memory_bus_protocol/memory_bus_protocol_top.sv
BEHAVIORAL_RAM_LINT_TOP := tests/unit/behavioral_system_ram/behavioral_system_ram_bus_top.sv
SIM_SOURCES := $(shell find sim -type f -name '*.sv' -print | sort)
SIM_LINT_TOPS := sim_clock sim_reset sim_cycle_timeout sim_termination
VENV_PYTHON := $(VENV)/bin/python
VENV_STAMP := $(VENV)/.requirements-dev.stamp
TEST_RUNNER := $(VENV_PYTHON) scripts/run_tests.py
WAVE_FILE := $(BUILD_DIR)/waves/register_en/dump.vcd

.PHONY: help venv structure build lint test unit differential randomized integration regression software waves ci clean

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

lint: structure venv ## Run HDL, Python, YAML, whitespace, and hygiene checks.
	@git diff HEAD --check -- .
	$(VERILATOR) --lint-only -Wall --assert --top-module register_en \
		$(VERILATOR_FLAGS) $(RTL_SOURCES)
	$(VERILATOR) --lint-only -Wall --assert --top-module memory_bus_protocol_top \
		$(VERILATOR_FLAGS) $(RTL_SOURCES) $(MEMORY_BUS_PROTOCOL_LINT_TOP)
	$(VERILATOR) --lint-only -Wall --assert --timing --top-module behavioral_system_ram_bus_top \
		$(VERILATOR_FLAGS) rtl/memory/memory_bus_if.sv $(SIM_SOURCES) $(BEHAVIORAL_RAM_LINT_TOP)
	@for top in $(SIM_LINT_TOPS); do \
		$(VERILATOR) --lint-only -Wall --timing --top-module $$top \
			$(VERILATOR_FLAGS) $(SIM_SOURCES); \
	done
	$(VENV_PYTHON) -m ruff check reference scripts sim tests
	$(VENV_PYTHON) -m ruff format --check reference scripts sim tests
	$(VENV_PYTHON) -m yamllint -c .yamllint.yaml milestones.yaml references.yaml .github/workflows/ci.yml
	$(VENV_PYTHON) scripts/check_tracked_files.py
	$(VENV_PYTHON) scripts/check_ci_workflow.py
	$(VENV_PYTHON) scripts/check_milestones.py
	$(VENV_PYTHON) scripts/check_references.py
	$(VENV_PYTHON) scripts/check_conventions.py
	$(VENV_PYTHON) scripts/check_roadmap.py

test: structure build venv ## Run the routine pytest gate.
	$(TEST_RUNNER) test --seed "$(RANDOM_SEED)" --build-root "$(abspath $(BUILD_DIR))"

unit: venv ## Run directed unit tests.
	$(TEST_RUNNER) unit --seed "$(RANDOM_SEED)" --build-root "$(abspath $(BUILD_DIR))"

differential: venv ## Run differential tests.
	$(TEST_RUNNER) differential --seed "$(RANDOM_SEED)" --build-root "$(abspath $(BUILD_DIR))"

randomized: venv ## Run deterministic randomized tests.
	$(TEST_RUNNER) randomized --seed "$(RANDOM_SEED)" --build-root "$(abspath $(BUILD_DIR))"

integration: venv ## Run integration tests.
	$(TEST_RUNNER) integration --seed "$(RANDOM_SEED)" --build-root "$(abspath $(BUILD_DIR))"

regression: structure build venv ## Run the authoritative pre-commit regression gate.
	$(TEST_RUNNER) regression --seed "$(RANDOM_SEED)" --build-root "$(abspath $(BUILD_DIR))"

software: ## Build legal project test software when a cross-toolchain is configured.
	@echo "software builds are not implemented yet" >&2
	@exit 2

waves: venv ## Run a directed test and generate a Verilator VCD trace.
	@rm -f -- $(WAVE_FILE)
	PS2_WAVES=1 $(TEST_RUNNER) unit \
		--seed "$(RANDOM_SEED)" --build-root "$(abspath $(BUILD_DIR))"
	@test -s $(WAVE_FILE)
	@grep -q '$$enddefinitions $$end' $(WAVE_FILE)
	@echo "waveform: $(WAVE_FILE)"

ci: venv ## Run the complete local equivalent of required CI verification.
	$(MAKE) lint
	$(MAKE) build
	$(MAKE) unit
	$(MAKE) differential
	$(MAKE) randomized
	$(MAKE) integration
	$(MAKE) regression

clean: ## Remove ignored local build outputs.
	@rm -rf -- build obj_dir sim_build
