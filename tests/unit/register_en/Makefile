SIM ?= verilator
TOPLEVEL_LANG := verilog

REPO_ROOT := $(abspath ../../..)
VERILOG_SOURCES := $(REPO_ROOT)/rtl/common/register_en.sv
TOPLEVEL := register_en
COCOTB_TEST_MODULES := cocotb_register_en
COMPILE_ARGS += -Wall

include $(shell cocotb-config --makefiles)/Makefile.sim
