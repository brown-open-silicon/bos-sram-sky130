.PHONY: all sim sim-local spice snm openram pdk-check shell clean

all: sim

sim:          ## RTL tests in the EDA container (Icarus + cocotb)
	scripts/eda.sh "python3 tb/run.py"

sim-local:    ## same, using iverilog + cocotb installed on your machine
	python3 tb/run.py

spice:        ## 6T cell butterfly curves at -40 / 27 / 100 C (ngspice, SKY130 models)
	mkdir -p build/spice
	scripts/eda.sh "ngspice -b spice/6t_cell/butterfly.spice"

snm: spice    ## read static noise margin from the sweeps
	python3 spice/6t_cell/snm.py

openram:      ## generate the baseline 256x32 1RW1R macro (slow)
	scripts/eda.sh 'python3 $$OPENRAM_HOME/../sram_compiler.py openram/config_256x32_1rw1r.py'

pdk-check:    ## confirm sky130A, the cell library and the SRAM macros are installed
	scripts/eda.sh 'ls $$PDK_ROOT; ls $$PDK_ROOT/sky130A/libs.ref | grep -Ei "sc_hd|sram"'

shell:
	scripts/eda.sh

clean:
	rm -rf build sim_build results.xml
