.DEFAULT_GOAL := help

PYTHON ?= python3
VERILATOR ?= verilator
VERILATOR_FLAGS ?=
BUILD_DIR ?= build
RANDOM_SEED ?= 1
VENV ?= .venv

SMOKE_RTL := rtl/common/register_en.sv
SMOKE_MDIR := $(BUILD_DIR)/verilator_smoke
RTL_PACKAGE_SOURCES := $(shell find rtl -type f -name '*_pkg.sv' -print | sort)
RTL_NONPACKAGE_SOURCES := $(shell find rtl -type f -name '*.sv' ! -name '*_pkg.sv' -print | sort)
RTL_SOURCES := $(RTL_PACKAGE_SOURCES) $(RTL_NONPACKAGE_SOURCES)
MEMORY_BUS_PROTOCOL_LINT_TOP := tests/unit/memory_bus_protocol/memory_bus_protocol_top.sv
BEHAVIORAL_RAM_LINT_TOP := tests/unit/behavioral_system_ram/behavioral_system_ram_bus_top.sv
MEMORY_TRACE_LINT_TOP := tests/unit/memory_transaction_trace/memory_transaction_trace_top.sv
ARCH_TRACE_LINT_TOP := tests/unit/architectural_trace_sink/architectural_trace_sink_top.sv
WAVEFORM_LINT_TOP := tests/unit/sim_waveform_control/sim_waveform_control_top.sv
R5900_TYPES_LINT_TOP := tests/unit/r5900_types/r5900_types_top.sv
R5900_TYPES_LINT_DRIVER := tests/unit/r5900_types/r5900_debug_driver.sv
R5900_TYPES_LINT_PROBE := tests/unit/r5900_types/r5900_debug_probe.sv
R5900_GPR_STORAGE := rtl/ee/r5900/r5900_gpr_storage.sv
R5900_GPR_FILE := rtl/ee/r5900/r5900_gpr_file.sv
R5900_PC := rtl/ee/r5900/r5900_pc.sv
R5900_CONTROL := rtl/ee/r5900/r5900_control.sv
R5900_CONTROL_CHECKER := rtl/ee/r5900/r5900_control_state_checker.sv
R5900_FETCH_REQUEST := rtl/ee/r5900/r5900_fetch_request.sv
R5900_FETCH_REQUEST_LINT_TOP := tests/unit/r5900_fetch_request/r5900_fetch_request_top.sv
R5900_FETCH_RESPONSE := rtl/ee/r5900/r5900_fetch_response.sv
R5900_FETCH_RESPONSE_LINT_TOP := tests/unit/r5900_fetch_response/r5900_fetch_response_top.sv
R5900_INSTRUCTION_FIELDS := rtl/ee/r5900/r5900_instruction_fields.sv
R5900_DECODE := rtl/ee/r5900/r5900_decode.sv
R5900_DECODE_DISPATCH := rtl/ee/r5900/r5900_decode_dispatch.sv
R5900_DECODE_DISPATCH_LINT_TOP := tests/unit/r5900_decode_dispatch/r5900_decode_dispatch_top.sv
R5900_WRITEBACK := rtl/ee/r5900/r5900_writeback.sv
R5900_WRITEBACK_LINT_TOP := tests/unit/r5900_writeback/r5900_writeback_top.sv
SIM_SOURCES := $(shell find sim -type f -name '*.sv' -print | sort)
SIM_LINT_TOPS := sim_clock sim_reset sim_cycle_timeout sim_termination
VENV_PYTHON := $(VENV)/bin/python
VENV_STAMP := $(VENV)/.requirements-dev.stamp
TEST_RUNNER := $(VENV_PYTHON) scripts/run_tests.py
WAVE_FILE := $(BUILD_DIR)/waves/sim_waveform_control/dump.vcd

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
	$(VERILATOR) --lint-only -Wall --timing --top-module memory_transaction_trace_top \
		$(VERILATOR_FLAGS) rtl/memory/memory_bus_if.sv \
		sim/debug/memory_transaction_trace.sv $(MEMORY_TRACE_LINT_TOP)
	$(VERILATOR) --lint-only -Wall --timing --top-module architectural_trace_sink_top \
		$(VERILATOR_FLAGS) sim/debug/architectural_trace_sink.sv $(ARCH_TRACE_LINT_TOP)
	$(VERILATOR) --lint-only -Wall --timing --top-module sim_waveform_control_top \
		$(VERILATOR_FLAGS) sim/debug/sim_waveform_control.sv $(WAVEFORM_LINT_TOP)
	$(VERILATOR) --lint-only -Wall --top-module r5900_types_top \
		$(VERILATOR_FLAGS) rtl/ee/r5900/r5900_types_pkg.sv \
		rtl/ee/r5900/r5900_debug_if.sv $(R5900_TYPES_LINT_DRIVER) \
		$(R5900_TYPES_LINT_PROBE) $(R5900_TYPES_LINT_TOP)
	$(VERILATOR) --lint-only -Wall --top-module r5900_gpr_storage \
		$(VERILATOR_FLAGS) rtl/ee/r5900/r5900_types_pkg.sv $(R5900_GPR_STORAGE)
	$(VERILATOR) --lint-only -Wall --assert --top-module r5900_gpr_file \
		$(VERILATOR_FLAGS) rtl/ee/r5900/r5900_types_pkg.sv \
		$(R5900_GPR_STORAGE) $(R5900_GPR_FILE)
	$(VERILATOR) --lint-only -Wall --top-module r5900_pc \
		$(VERILATOR_FLAGS) rtl/ee/r5900/r5900_types_pkg.sv $(R5900_PC)
	$(VERILATOR) --lint-only -Wall --assert --top-module r5900_control \
		$(VERILATOR_FLAGS) rtl/ee/r5900/r5900_types_pkg.sv \
		$(R5900_CONTROL_CHECKER) $(R5900_CONTROL)
	$(VERILATOR) --lint-only -Wall --assert --top-module r5900_fetch_request_top \
		$(VERILATOR_FLAGS) rtl/ee/r5900/r5900_types_pkg.sv \
		rtl/memory/memory_bus_if.sv $(R5900_FETCH_REQUEST) $(R5900_FETCH_REQUEST_LINT_TOP)
	$(VERILATOR) --lint-only -Wall --assert --top-module r5900_fetch_response_top \
		$(VERILATOR_FLAGS) rtl/ee/r5900/r5900_types_pkg.sv \
		rtl/memory/memory_bus_if.sv $(R5900_FETCH_RESPONSE) $(R5900_FETCH_RESPONSE_LINT_TOP)
	$(VERILATOR) --lint-only -Wall --top-module r5900_instruction_fields \
		$(VERILATOR_FLAGS) rtl/ee/r5900/r5900_types_pkg.sv $(R5900_INSTRUCTION_FIELDS)
	$(VERILATOR) --lint-only -Wall --top-module r5900_decode \
		$(VERILATOR_FLAGS) rtl/ee/r5900/r5900_types_pkg.sv $(R5900_DECODE)
	$(VERILATOR) --lint-only -Wall --top-module r5900_decode_dispatch_top \
		$(VERILATOR_FLAGS) rtl/ee/r5900/r5900_types_pkg.sv \
		$(R5900_DECODE) $(R5900_DECODE_DISPATCH) $(R5900_DECODE_DISPATCH_LINT_TOP)
	$(VERILATOR) --lint-only -Wall --assert --top-module r5900_writeback_top \
		$(VERILATOR_FLAGS) rtl/ee/r5900/r5900_types_pkg.sv \
		$(R5900_GPR_STORAGE) $(R5900_GPR_FILE) $(R5900_WRITEBACK) $(R5900_WRITEBACK_LINT_TOP)
	$(VERILATOR) --lint-only -Wall --assert --timing --top-module ps2_sim_top \
		$(VERILATOR_FLAGS) rtl/memory/memory_bus_if.sv \
		rtl/memory/memory_bus_protocol_checker.sv $(SIM_SOURCES)
	@for top in $(SIM_LINT_TOPS); do \
		$(VERILATOR) --lint-only -Wall --timing --top-module $$top \
			$(VERILATOR_FLAGS) $(SIM_SOURCES); \
	done
	$(VENV_PYTHON) -m ruff check reference scripts sim tests
	$(VENV_PYTHON) -m ruff format --check reference scripts sim tests
	$(VENV_PYTHON) -m yamllint -c .yamllint.yaml \
		milestones.yaml references.yaml coverage/r5900_isa.yaml .github/workflows/ci.yml
	$(VENV_PYTHON) scripts/check_tracked_files.py
	$(VENV_PYTHON) scripts/check_ci_workflow.py
	$(VENV_PYTHON) scripts/check_milestones.py
	$(VENV_PYTHON) scripts/check_references.py
	$(VENV_PYTHON) scripts/check_conventions.py
	$(VENV_PYTHON) scripts/check_roadmap.py
	$(VENV_PYTHON) scripts/check_r5900_coverage.py

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

waves: venv ## Run the waveform-control test and retain its Verilator VCD trace.
	@rm -f -- $(WAVE_FILE)
	PS2_WAVES=1 RANDOM_SEED="$(RANDOM_SEED)" \
		PS2_BUILD_ROOT="$(abspath $(BUILD_DIR))" \
		$(VENV_PYTHON) -m pytest -q tests/unit/test_sim_waveform_control_runner.py
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
