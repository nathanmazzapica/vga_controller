# Simulation Makefile (Icarus Verilog)
# Usage: make test   - build and run the vga_timing testbench
#        make clean  - remove build artifacts
 
IVERILOG ?= iverilog
VVP      ?= vvp
 
BUILD := build
 
RTL := rtl/vga_timing.v
TB  := tb/vga_timing_tb.v
TOP := vga_timing_tb
 
SIM := $(BUILD)/$(TOP).vvp
LOG := $(BUILD)/$(TOP).log
 
.PHONY: all test clean
 
all: test
 
$(BUILD):
	mkdir -p $@
 
# Recompiles only when the RTL or testbench changes
$(SIM): $(RTL) $(TB) | $(BUILD)
	$(IVERILOG) -g2012 -Wall -s $(TOP) -o $@ $(TB) $(RTL)
 
# Runs the sim, saves a log, and fails if any "TEST FAILED" line was printed
timetest: $(SIM)
	$(VVP) $(SIM) | tee $(LOG)
	@if grep -q "TEST FAILED" $(LOG); then \
		echo "*** $(TOP): FAILED ***"; exit 1; \
	else \
		echo "*** $(TOP): PASSED ***"; \
	fi
 
clean:
	rm -rf $(BUILD)

# --- vga_controller testbench ---------------------------------------------
# Full color pipeline: timing + text/font + vram + tilemap + color mux.
# Note: $readmemh in the RTL loads tiles.mem, palette.mem, vram.mem and
# font_ascii_8x8.mem relative to the cwd, so this must run from the repo root.
CTRL_RTL := rtl/vga_controller.v \
            rtl/vga_timing.v \
            rtl/vga_color.v \
            rtl/text_renderer.v \
            rtl/font_renderer.v \
            rtl/font_rom.v \
            rtl/tilemap.v \
            rtl/vram.v

CTRL_TB  := tb/vga_controller_tb.v
CTRL_TOP := vga_controller_tb
CTRL_SIM := $(BUILD)/$(CTRL_TOP).vvp
CTRL_LOG := $(BUILD)/$(CTRL_TOP).log

.PHONY: ctrltest

$(CTRL_SIM): $(CTRL_RTL) $(CTRL_TB) | $(BUILD)
	$(IVERILOG) -g2012 -Wall -s $(CTRL_TOP) -o $@ $(CTRL_TB) $(CTRL_RTL)

# Runs the sim, saves a log, and fails if any "FAIL" line was printed
ctrltest: $(CTRL_SIM)
	$(VVP) $(CTRL_SIM) | tee $(CTRL_LOG)
	@if grep -q "FAIL" $(CTRL_LOG); then \
		echo "*** $(CTRL_TOP): FAILED ***"; exit 1; \
	else \
		echo "*** $(CTRL_TOP): PASSED ***"; \
	fi
