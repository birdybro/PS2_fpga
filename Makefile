.DEFAULT_GOAL := help

PYTHON ?= python3
VERILATOR ?= verilator
BUILD_DIR ?= build
RANDOM_SEED ?= 1

.PHONY: help structure build lint test unit differential randomized integration regression software waves clean

help: ## Show available development commands.
	@awk 'BEGIN {FS = ":.*## "; printf "PS2_fpga development commands:\n\n"} /^[a-zA-Z0-9_-]+:.*## / {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

structure: ## Verify required repository subsystem boundaries.
	@$(PYTHON) scripts/check_structure.py

build: ## Compile synthesizable RTL (introduced by M003).
	@echo "build is not available until milestone M003" >&2
	@exit 2

lint: structure ## Run the currently available static repository checks.
	@git diff HEAD --check -- .

test: structure ## Run the routine test gate currently available.
	@echo "bootstrap tests: PASS"

unit: ## Run directed unit tests (introduced by M004).
	@echo "unit tests are not available until milestone M004" >&2
	@exit 2

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
