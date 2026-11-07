"""OpenRAM config for the baseline SKY130 SRAM in spec/sram_spec.md.

256 words x 32 bits, byte-writable, 1 read/write port + 1 read port.
This is the same shape as OpenRAM's silicon-proven sky130_sram_1kbyte_1rw1r_32x256_8.

Run (inside the EDA container, see Makefile `make openram`):
    python3 $OPENRAM_HOME/../sram_compiler.py openram/config_256x32_1rw1r.py

Check option names against the OpenRAM version in your image; they've
changed between releases. If you only need the macro (not to regenerate it),
the prebuilt one may already be in $PDK_ROOT/sky130A/libs.ref/sky130_sram_macros/.
"""
tech_name = "sky130"

word_size = 32
num_words = 256
write_size = 8          # byte mask -> wmask[3:0]

num_rw_ports = 1
num_r_ports = 1
num_w_ports = 0
num_spare_rows = 1      # sky130 bitcell array needs spare rows/cols in OpenRAM's sky130 flow
num_spare_cols = 1

# One corner while learning. Add more (SS/FF, -40/100 C) for real characterization.
nominal_corner_only = True
process_corners = ["TT"]
supply_voltages = [1.8]
temperatures = [25]

route_supplies = "ring"
check_lvsdrc = True     # slow; set False for quick experiments

output_path = "build/openram"
output_name = f"bos_sram_{word_size}x{num_words}_1rw1r"
